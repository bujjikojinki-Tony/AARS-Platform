import AppKit
import Foundation
import Darwin

@objc protocol ProbePing {
    func ping(reply: @escaping (Int32) -> Void)
}

final class ProbeService: NSObject, ProbePing {
    func ping(reply: @escaping (Int32) -> Void) { reply(getpid()) }
}

final class ProbeDelegate: NSObject, NSXPCListenerDelegate, @unchecked Sendable {
    private let lock = NSLock()
    private var count = 0

    var accepted: Int {
        lock.lock()
        defer { lock.unlock() }
        return count
    }

    func listener(_ listener: NSXPCListener, shouldAcceptNewConnection connection: NSXPCConnection) -> Bool {
        guard connection.effectiveUserIdentifier == geteuid() else { return false }
        lock.lock()
        count += 1
        lock.unlock()
        connection.exportedInterface = NSXPCInterface(with: ProbePing.self)
        connection.exportedObject = ProbeService()
        connection.activate()
        return true
    }
}

final class ProbeReply<Value>: @unchecked Sendable {
    let signal = DispatchSemaphore(value: 0)
    private let lock = NSLock()
    private var response: Value?

    func record(_ value: Value) {
        lock.lock()
        defer { lock.unlock() }
        if response == nil {
            response = value
            signal.signal()
        }
    }

    func wait() -> Value? {
        guard signal.wait(timeout: .now() + 5) == .success else { return nil }
        lock.lock()
        defer { lock.unlock() }
        return response
    }
}

struct Observation: Encodable {
    let outcome: String
    var pid: Int32?
    var errorDomain: String?
    var errorCode: Int?
    var category: String?

    static func rejected(_ error: NSError) -> Observation {
        let message = error.localizedDescription.lowercased()
        let category: String
        if message.contains("failed at lookup") || message.contains("no such process") {
            category = "SERVICE_LOOKUP"
        } else if message.contains("operation not permitted") || message.contains("permission denied") ||
                    message.contains("sandbox") {
            category = "PERMISSION"
        } else if error.domain == NSCocoaErrorDomain && error.code == 4102 {
            category = "CODE_SIGNING_REQUIREMENT"
        } else if message.contains("entitlement") || message.contains("code signing") {
            category = "IDENTITY"
        } else {
            category = "CONNECTION"
        }
        return Observation(outcome: "REFUSED", errorDomain: error.domain, errorCode: error.code, category: category)
    }
}

enum BootstrapFailure: Error {
    case missingProxy
    case noReply
    case peer(NSError)

    var observation: Observation {
        switch self {
        case .missingProxy: return Observation(outcome: "NO_PROXY")
        case .noReply: return Observation(outcome: "TIMEOUT")
        case let .peer(error): return .rejected(error)
        }
    }
}

@objc protocol ProbeBootstrap {
    func hello(reply: @escaping (Int32) -> Void)
    func endpoint(restricted: Bool, reply: @escaping (NSXPCListenerEndpoint) -> Void)
    func restrictedAccepts(reply: @escaping (Int32) -> Void)
}

@available(macOS 13.0, *)
final class BootstrapDelegate: NSObject, NSXPCListenerDelegate, ProbeBootstrap, @unchecked Sendable {
    private let normalDelegate = ProbeDelegate()
    private let restrictedDelegate = ProbeDelegate()
    private let normal: NSXPCListener
    private let restricted: NSXPCListener

    init(broker: ApprovalPeerIdentity) {
        normal = NSXPCListener.anonymous()
        restricted = broker.makeBrokerListener(delegate: restrictedDelegate)
        super.init()
        normal.delegate = normalDelegate
        normal.activate()
        restricted.activate()
    }

    func listener(_ listener: NSXPCListener, shouldAcceptNewConnection connection: NSXPCConnection) -> Bool {
        guard connection.effectiveUserIdentifier == geteuid() else { return false }
        connection.exportedInterface = NSXPCInterface(with: ProbeBootstrap.self)
        connection.exportedObject = self
        connection.activate()
        return true
    }

    func hello(reply: @escaping (Int32) -> Void) { reply(getpid()) }

    func endpoint(restricted: Bool, reply: @escaping (NSXPCListenerEndpoint) -> Void) {
        reply(restricted ? self.restricted.endpoint : normal.endpoint)
    }

    func restrictedAccepts(reply: @escaping (Int32) -> Void) {
        reply(Int32(restrictedDelegate.accepted))
    }
}

@available(macOS 13.0, *)
@MainActor
final class ProbeWindow: NSObject, NSApplicationDelegate {
    private let policy: ApprovalPeerIdentity
    private var window: NSWindow?

    init(policy: ApprovalPeerIdentity) {
        self.policy = policy
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        let panel = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 510, height: 185),
                             styleMask: [.titled, .closable], backing: .buffered, defer: false)
        panel.title = "F-02 跨进程诊断"
        panel.center()
        let status = NSTextField(wrappingLabelWithString: "正在检查两个独立进程之间的连接。")
        status.preferredMaxLayoutWidth = 450
        let content = NSStackView(views: [status])
        content.edgeInsets = NSEdgeInsets(top: 26, left: 26, bottom: 26, right: 26)
        panel.contentView = content
        window = panel
        panel.makeKeyAndOrderFront(nil)
        if #available(macOS 14.0, *) { NSApp.activate() } else { NSApp.activate(ignoringOtherApps: true) }

        let policy = policy
        DispatchQueue.global(qos: .userInitiated).async {
            let results = ApprovalXPCProbe.separated(service: policy)
            let destination = Bundle.main.bundleURL.deletingLastPathComponent()
                .appendingPathComponent("xpc_separate_gui.json")
            do {
                try ApprovalXPCProbe.report(results).write(to: destination, options: .atomic)
                let wording = ApprovalXPCProbe.passedSeparated(results) ? "跨进程测试通过。" : "跨进程测试未通过。"
                DispatchQueue.main.async { status.stringValue = wording + " 报告已保存。" }
            } catch {
                DispatchQueue.main.async { status.stringValue = "无法保存跨进程测试报告。" }
            }
        }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

@available(macOS 13.0, *)
@main
struct ApprovalXPCProbe {
    struct Case: Encodable {
        let name: String
        let accepted: Int?
        let observation: Observation
    }

    static func check(_ name: String, broker: ApprovalPeerIdentity? = nil,
                      service: ApprovalPeerIdentity? = nil) -> Case {
        let delegate = ProbeDelegate()
        let listener = broker?.makeBrokerListener(delegate: delegate) ?? NSXPCListener.anonymous()
        listener.delegate = delegate
        listener.activate()
        defer { listener.invalidate() }
        let received = sendPing(to: listener.endpoint, service: service)
        return withExtendedLifetime(delegate) {
            Case(name: name, accepted: delegate.accepted, observation: received)
        }
    }

    static func sendPing(to endpoint: NSXPCListenerEndpoint, service: ApprovalPeerIdentity? = nil) -> Observation {
        let connection = service?.makeServiceConnection(to: endpoint)
            ?? NSXPCConnection(listenerEndpoint: endpoint)
        defer { connection.invalidate() }
        connection.remoteObjectInterface = NSXPCInterface(with: ProbePing.self)
        let reply = ProbeReply<Observation>()
        let proxy = connection.remoteObjectProxyWithErrorHandler { error in
            reply.record(.rejected(error as NSError))
        } as? ProbePing
        connection.activate()
        proxy?.ping { pid in reply.record(Observation(outcome: "REPLY", pid: pid)) }
        return reply.wait() ?? Observation(outcome: "TIMEOUT")
    }

    private static func callBootstrap<Value>(
        _ connection: NSXPCConnection, _ request: (ProbeBootstrap, @escaping (Value) -> Void) -> Void
    ) throws -> Value {
        let result = ProbeReply<Result<Value, BootstrapFailure>>()
        guard let proxy = connection.remoteObjectProxyWithErrorHandler({ error in
            result.record(.failure(.peer(error as NSError)))
        }) as? ProbeBootstrap else {
            throw BootstrapFailure.missingProxy
        }
        request(proxy) { result.record(.success($0)) }
        guard let reply = result.wait() else { throw BootstrapFailure.noReply }
        return try reply.get()
    }

    static func separated(service: ApprovalPeerIdentity) -> [Case] {
        let connection = NSXPCConnection(serviceName: service.role.identifier)
        defer { connection.invalidate() }
        connection.remoteObjectInterface = NSXPCInterface(with: ProbeBootstrap.self)
        connection.activate()
        var cases: [Case] = []
        var stage = "embedded_service_hello"
        do {
            let pid: Int32 = try callBootstrap(connection) { proxy, reply in proxy.hello(reply: reply) }
            guard pid > 0, pid != getpid() else {
                return [Case(name: stage, accepted: 0, observation: Observation(outcome: "WRONG_PROCESS", pid: pid))]
            }
            cases.append(Case(name: stage, accepted: 1, observation: Observation(outcome: "REPLY", pid: pid)))
            stage = "embedded_service_normal_endpoint"
            let endpoint: NSXPCListenerEndpoint = try callBootstrap(connection) { proxy, reply in
                proxy.endpoint(restricted: false, reply: reply)
            }
            let baseline = sendPing(to: endpoint)
            cases.append(Case(name: "separate_process_ping_baseline",
                              accepted: baseline.outcome == "REPLY" ? 1 : 0, observation: baseline))
            guard baseline.outcome == "REPLY" && baseline.pid == pid else { return cases }
            stage = "embedded_service_restricted_endpoint"
            let restrictedEndpoint: NSXPCListenerEndpoint = try callBootstrap(connection) { proxy, reply in
                proxy.endpoint(restricted: true, reply: reply)
            }
            let listenerCheck = sendPing(to: restrictedEndpoint)
            stage = "embedded_service_restricted_accept_count"
            let count: Int32 = try callBootstrap(connection) { proxy, reply in proxy.restrictedAccepts(reply: reply) }
            cases.append(Case(name: "separate_process_listener_rejects_ad_hoc_broker",
                              accepted: Int(count), observation: listenerCheck))
            cases.append(Case(name: "separate_process_client_rejects_ad_hoc_service",
                              accepted: nil, observation: sendPing(to: endpoint, service: service)))
        } catch let failure as BootstrapFailure {
            cases.append(Case(name: stage, accepted: 0, observation: failure.observation))
        } catch {
            cases.append(Case(name: stage, accepted: 0, observation: .rejected(error as NSError)))
        }
        return cases
    }

    static func passedSeparated(_ cases: [Case]) -> Bool {
        guard cases.count == 4, let pid = cases[0].observation.pid else { return false }
        return pid != getpid() && cases[1].observation.pid == pid
            && cases[1].observation.outcome == "REPLY"
            && cases[2].accepted == 0 && cases[2].observation.outcome == "REFUSED"
            && cases[3].observation.outcome == "REFUSED"
            && cases[3].observation.category == "CODE_SIGNING_REQUIREMENT"
    }

    static func report(_ cases: [Case]) throws -> Data {
        struct Run: Encodable {
            let hostPID: Int32
            let status: String
            let observations: [Case]
        }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        encoder.keyEncodingStrategy = .convertToSnakeCase
        return try encoder.encode(Run(hostPID: getpid(), status: passedSeparated(cases) ? "PASS" : "BLOCKED",
                                      observations: cases)) + Data([0x0a])
    }

    @MainActor
    static func main() throws {
        // Test-only trust anchor. It cannot be used to enroll any AARS operator.
        let fixtureTeam = "AARSDEMO01"
        let broker = try ApprovalPeerIdentity(role: .broker, trustedTeamID: fixtureTeam)
        let service = try ApprovalPeerIdentity(role: .service, trustedTeamID: fixtureTeam)
        if Bundle.main.bundleURL.pathExtension == "xpc" {
            let listener = NSXPCListener.service()
            let delegate = BootstrapDelegate(broker: broker)
            listener.delegate = delegate
            withExtendedLifetime(delegate) { listener.resume() }
            return
        }
        let args = Array(CommandLine.arguments.dropFirst())
        if Bundle.main.bundleURL.pathExtension == "app", args.isEmpty {
            let app = NSApplication.shared
            let delegate = ProbeWindow(policy: service)
            app.setActivationPolicy(.regular)
            app.delegate = delegate
            withExtendedLifetime(delegate) { app.run() }
            return
        }
        if args == ["--separate"] {
            FileHandle.standardOutput.write(try report(separated(service: service)))
            return
        }
        let results = [
            check("diagnostic_ping_baseline"),
            check("listener_rejects_ad_hoc_broker", broker: broker),
            check("client_rejects_ad_hoc_service", service: service),
        ]
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        encoder.keyEncodingStrategy = .convertToSnakeCase
        FileHandle.standardOutput.write(try encoder.encode(results) + Data([0x0a]))
    }
}
