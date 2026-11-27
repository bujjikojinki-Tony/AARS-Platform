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
}

@objc protocol ProbeBootstrap {
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
        let accepted: Int
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
            let error = error as NSError
            reply.record(Observation(outcome: "REFUSED", errorDomain: error.domain, errorCode: error.code))
        } as? ProbePing
        connection.activate()
        proxy?.ping { pid in reply.record(Observation(outcome: "REPLY", pid: pid)) }
        return reply.wait() ?? Observation(outcome: "TIMEOUT")
    }

    static func separated(service: ApprovalPeerIdentity) -> [Case] {
        let connection = NSXPCConnection(serviceName: "local.aars.f02.peer-test-service")
        defer { connection.invalidate() }
        connection.remoteObjectInterface = NSXPCInterface(with: ProbeBootstrap.self)
        let unrestricted = ProbeReply<Result<NSXPCListenerEndpoint, NSError>>()
        let restricted = ProbeReply<NSXPCListenerEndpoint>()
        let count = ProbeReply<Int32>()
        let proxy = connection.remoteObjectProxyWithErrorHandler { error in
            unrestricted.record(.failure(error as NSError))
        } as? ProbeBootstrap
        connection.activate()
        proxy?.endpoint(restricted: false) { endpoint in unrestricted.record(.success(endpoint)) }
        guard let handshake = unrestricted.wait() else {
            return [Case(name: "embedded_service_unavailable", accepted: 0, observation: Observation(outcome: "TIMEOUT"))]
        }
        let endpoint: NSXPCListenerEndpoint
        switch handshake {
        case .success(let value):
            endpoint = value
        case .failure(let error):
            return [Case(name: "embedded_service_unavailable", accepted: 0,
                         observation: Observation(outcome: "REFUSED", errorDomain: error.domain, errorCode: error.code))]
        }
        let baseline = sendPing(to: endpoint)
        let remoteCheck = sendPing(to: endpoint, service: service)
        proxy?.endpoint(restricted: true) { restricted.record($0) }
        guard let restrictedEndpoint = restricted.wait() else {
            return [Case(name: "embedded_service_endpoint_unavailable", accepted: 0,
                         observation: Observation(outcome: "TIMEOUT"))]
        }
        let listenerCheck = sendPing(to: restrictedEndpoint)
        proxy?.restrictedAccepts { count.record($0) }
        return [
            Case(name: "separate_process_ping_baseline", accepted: baseline.outcome == "REPLY" ? 1 : 0,
                 observation: baseline),
            Case(name: "separate_process_listener_rejects_ad_hoc_broker",
                 accepted: Int(count.wait() ?? -1), observation: listenerCheck),
            Case(name: "separate_process_client_rejects_ad_hoc_service", accepted: 1, observation: remoteCheck),
        ]
    }

    static func passedSeparated(_ cases: [Case]) -> Bool {
        // NSXPCConnectionCodeSigningRequirementFailure in FoundationErrors.h.
        let signingRequirementFailure = 4102
        guard cases.count == 3, let other = cases[0].observation.pid else { return false }
        return other != getpid() && cases[0].observation.outcome == "REPLY"
            && cases[1].accepted == 0 && cases[1].observation.outcome == "REFUSED"
            && cases[2].observation.errorDomain == NSCocoaErrorDomain
            && cases[2].observation.errorCode == signingRequirementFailure
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
