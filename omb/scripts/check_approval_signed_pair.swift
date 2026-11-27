import AppKit
import Darwin
import Foundation

@objc protocol SignedPairPing {
    func ping(reply: @escaping (Int32) -> Void)
}

@available(macOS 13.0, *)
final class SignedPairService: NSObject, NSXPCListenerDelegate, SignedPairPing, @unchecked Sendable {
    private let broker: ApprovalPeerIdentity

    init(broker: ApprovalPeerIdentity) {
        self.broker = broker
    }

    func listener(_ listener: NSXPCListener, shouldAcceptNewConnection connection: NSXPCConnection) -> Bool {
        guard connection.effectiveUserIdentifier == geteuid() else { return false }
        broker.configurePeerCheck(on: connection)
        connection.exportedInterface = NSXPCInterface(with: SignedPairPing.self)
        connection.exportedObject = self
        connection.activate()
        return true
    }

    func ping(reply: @escaping (Int32) -> Void) { reply(getpid()) }
}

struct SignedPairReport: Encodable {
    let status: String
    let stage: String
    var hostPID: Int32?
    var servicePID: Int32?
    var errorDomain: String?
    var errorCode: Int?
    let approvalGate = "BLOCKED_APPROVAL_PLATFORM"

    func json() throws -> Data {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        encoder.keyEncodingStrategy = .convertToSnakeCase
        return try encoder.encode(self) + Data([0x0a])
    }
}

final class PairReply: @unchecked Sendable {
    private let signal = DispatchSemaphore(value: 0)
    private let lock = NSLock()
    private var report: SignedPairReport?

    func record(_ value: SignedPairReport) {
        lock.lock()
        defer { lock.unlock() }
        if report == nil {
            report = value
            signal.signal()
        }
    }

    func wait() -> SignedPairReport {
        guard signal.wait(timeout: .now() + 8) == .success else {
            return SignedPairReport(status: "BLOCKED", stage: "peer_reply_timeout")
        }
        lock.lock()
        defer { lock.unlock() }
        return report ?? SignedPairReport(status: "BLOCKED", stage: "peer_reply_missing")
    }
}

enum PairConfigurationError: Error {
    case invalidRole
    case teamMismatch
    case missingTeam
}

@available(macOS 13.0, *)
struct SignedPairProbe {
    static func configuredTeam(expected: String?) throws -> String {
        guard let team = Bundle.main.object(forInfoDictionaryKey: "AARSExpectedAppleTeamID") as? String else {
            throw PairConfigurationError.missingTeam
        }
        if let expected, expected != team { throw PairConfigurationError.teamMismatch }
        return team
    }

    static func verifyHost(team: String) throws -> ApprovalPeerIdentity {
        let broker = try ApprovalPeerIdentity(role: .broker, trustedTeamID: team)
        let service = try ApprovalPeerIdentity(role: .service, trustedTeamID: team)
        let host = Bundle.main.bundleURL
        guard host.pathExtension == "app", Bundle.main.bundleIdentifier == broker.role.identifier else {
            throw PairConfigurationError.invalidRole
        }
        try broker.verifyBundle(at: host.path)
        let serviceBundle = host.appendingPathComponent("Contents/XPCServices/\(service.role.identifier).xpc")
        try service.verifyBundle(at: serviceBundle.path)
        return service
    }

    static func probe(team: String) throws -> SignedPairReport {
        let service = try verifyHost(team: team)
        let connection = NSXPCConnection(serviceName: service.role.identifier)
        defer { connection.invalidate() }
        service.configurePeerCheck(on: connection)
        connection.remoteObjectInterface = NSXPCInterface(with: SignedPairPing.self)
        let response = PairReply()
        let host = getpid()
        let proxy = connection.remoteObjectProxyWithErrorHandler { error in
            let error = error as NSError
            response.record(SignedPairReport(status: "BLOCKED", stage: "peer_connection",
                                             hostPID: host, errorDomain: error.domain, errorCode: error.code))
        } as? SignedPairPing
        guard let proxy else {
            return SignedPairReport(status: "BLOCKED", stage: "peer_proxy_unavailable", hostPID: host)
        }
        connection.activate()
        proxy.ping { pid in
            let validPeer = pid > 0 && pid != host
            response.record(SignedPairReport(status: validPeer ? "SIGNED_XPC_PASS" : "BLOCKED",
                                             stage: validPeer ? "peer_round_trip" : "unexpected_service_pid",
                                             hostPID: host, servicePID: pid))
        }
        return response.wait()
    }

    static func blocked(_ error: Error) -> SignedPairReport {
        switch error {
        case PairConfigurationError.invalidRole:
            return SignedPairReport(status: "BLOCKED", stage: "unexpected_bundle_role")
        case PairConfigurationError.teamMismatch:
            return SignedPairReport(status: "BLOCKED", stage: "expected_team_mismatch")
        case PairConfigurationError.missingTeam:
            return SignedPairReport(status: "BLOCKED", stage: "missing_team_configuration")
        case PeerIdentityError.invalidTeamID:
            return SignedPairReport(status: "BLOCKED", stage: "invalid_team_configuration")
        case PeerIdentityError.osStatus(let code):
            return SignedPairReport(status: "BLOCKED", stage: "static_identity", errorCode: Int(code))
        default:
            return SignedPairReport(status: "BLOCKED", stage: "static_preflight")
        }
    }
}

@available(macOS 13.0, *)
@MainActor
final class SignedPairWindow: NSObject, NSApplicationDelegate {
    private var window: NSWindow?

    func applicationDidFinishLaunching(_ notification: Notification) {
        let panel = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 510, height: 185),
                             styleMask: [.titled, .closable], backing: .buffered, defer: false)
        panel.title = "F-02 正式签名组件连通性诊断"
        panel.center()
        let status = NSTextField(wrappingLabelWithString: "正在验证组件签名和双向连接。")
        status.preferredMaxLayoutWidth = 450
        let content = NSStackView(views: [status])
        content.edgeInsets = NSEdgeInsets(top: 26, left: 26, bottom: 26, right: 26)
        panel.contentView = content
        window = panel
        panel.makeKeyAndOrderFront(nil)
        if #available(macOS 14.0, *) { NSApp.activate() } else { NSApp.activate(ignoringOtherApps: true) }
        DispatchQueue.global(qos: .userInitiated).async {
            let result: SignedPairReport
            do {
                result = try SignedPairProbe.probe(team: SignedPairProbe.configuredTeam(expected: nil))
            } catch {
                result = SignedPairProbe.blocked(error)
            }
            let destination = Bundle.main.bundleURL.deletingLastPathComponent()
                .appendingPathComponent("F02_SIGNED_PAIR_\(UUID().uuidString).json")
            do {
                try result.json().write(to: destination, options: .atomic)
                let summary = result.status == "SIGNED_XPC_PASS" ? "双向签名连接通过。" : "双向签名连接未通过。"
                DispatchQueue.main.async { status.stringValue = summary + " 报告已保存。" }
            } catch {
                DispatchQueue.main.async { status.stringValue = "无法保存双向签名连接报告。" }
            }
        }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

@available(macOS 13.0, *)
@main
struct SignedPairMain {
    @MainActor
    static func main() {
        if Bundle.main.bundleURL.pathExtension == "xpc" {
            serve()
        }
        let args = Array(CommandLine.arguments.dropFirst())
        if args.count == 2 && args[0] == "--preflight" {
            do {
                let team = try SignedPairProbe.configuredTeam(expected: args[1])
                _ = try SignedPairProbe.verifyHost(team: team)
                emit(SignedPairReport(status: "STATIC_IDENTITY_VERIFIED", stage: "bundle_pair"), exitCode: 0)
            } catch {
                emit(SignedPairProbe.blocked(error), exitCode: 2)
            }
        }
        if args.isEmpty && Bundle.main.bundleURL.pathExtension == "app" {
            let app = NSApplication.shared
            let delegate = SignedPairWindow()
            app.setActivationPolicy(.regular)
            app.delegate = delegate
            withExtendedLifetime(delegate) { app.run() }
            return
        }
        emit(SignedPairReport(status: "BLOCKED", stage: "invalid_arguments"), exitCode: 64)
    }

    private static func serve() -> Never {
        do {
            let team = try SignedPairProbe.configuredTeam(expected: nil)
            let service = try ApprovalPeerIdentity(role: .service, trustedTeamID: team)
            guard Bundle.main.bundleIdentifier == service.role.identifier else {
                throw PairConfigurationError.invalidRole
            }
            try service.verifyBundle(at: Bundle.main.bundleURL.path)
            let delegate = SignedPairService(broker: try ApprovalPeerIdentity(role: .broker, trustedTeamID: team))
            let listener = NSXPCListener.service()
            listener.delegate = delegate
            withExtendedLifetime(delegate) { listener.resume() }
            exit(1)
        } catch {
            emit(SignedPairProbe.blocked(error), exitCode: 2)
        }
    }

    private static func emit(_ report: SignedPairReport, exitCode: Int32) -> Never {
        if let bytes = try? report.json() {
            FileHandle.standardOutput.write(bytes)
        }
        exit(exitCode)
    }
}
