import AppKit
import CryptoKit
import Foundation
import LocalAuthentication
import Security

private let scope = "F02_ISOLATED_HARDWARE_PIN"
private let domain = Data("AARS-OMB-PIN-ENROLLMENT-V1\n".utf8)

private struct Session: Decodable {
    let scope: String
    let run_id: String
}

private struct Challenge: Decodable {
    let scope: String
    let run_id: String
    let payload_b64: String
}

private struct Claims: Decodable {
    let workspace_id: String
    let db_instance_id: String
    let operator_id: String
    let boot_id: String
    let policy_version: Int
    let key_id: String
    let pin_sha256: String
    let nonce: String
    let issued_at: String
    let expires_at: String
}

private enum DiagnosticError: Error { case invalidInput, timedOut, wrongFixture }

private func readJSON<T: Decodable>(_ type: T.Type, _ url: URL) throws -> T {
    let values = try url.resourceValues(forKeys: [.isSymbolicLinkKey, .isRegularFileKey, .fileSizeKey])
    guard values.isRegularFile == true, values.isSymbolicLink == false,
          let size = values.fileSize, size > 0, size <= 4096 else { throw DiagnosticError.invalidInput }
    return try JSONDecoder().decode(type, from: Data(contentsOf: url))
}

private func writeJSON(_ payload: [String: String], name: String, in root: URL) throws {
    let data = try diagnosticJSON(payload)
    try data.write(to: root.appendingPathComponent(name), options: .atomic)
}

private func waitForJSON<T: Decodable>(_ type: T.Type, _ url: URL, seconds: TimeInterval) throws -> T {
    let start = ContinuousClock.now
    while start.duration(to: .now) < .seconds(seconds) {
        if FileManager.default.fileExists(atPath: url.path) {
            return try readJSON(type, url)
        }
        Thread.sleep(forTimeInterval: 0.2)
    }
    throw DiagnosticError.timedOut
}

private func verifiedMessage(_ challenge: Challenge, session: Session, fingerprint: String) throws -> Data {
    guard challenge.scope == scope, challenge.run_id == session.run_id,
          let raw = Data(base64Encoded: challenge.payload_b64), raw.count <= 1400,
          raw.starts(with: domain) else { throw DiagnosticError.wrongFixture }
    let json = Data(raw.dropFirst(domain.count))
    let values = try JSONDecoder().decode(Claims.self, from: json)
    guard let fields = try JSONSerialization.jsonObject(with: json) as? [String: Any],
          Set(fields.keys) == ["workspace_id", "db_instance_id", "operator_id", "boot_id", "policy_version",
                               "key_id", "pin_sha256", "nonce", "issued_at", "expires_at"],
          try JSONSerialization.data(withJSONObject: fields, options: [.sortedKeys, .withoutEscapingSlashes]) == json,
          values.key_id == "f02-hardware-fixture", values.pin_sha256 == fingerprint, values.policy_version == 1,
          values.workspace_id.range(of: #"^workspace\.[a-f0-9]{32}$"#, options: .regularExpression) != nil,
          values.db_instance_id.range(of: #"^db\.[a-f0-9]{32}$"#, options: .regularExpression) != nil,
          values.boot_id.range(of: #"^boot\.[a-f0-9]{32}$"#, options: .regularExpression) != nil,
          values.operator_id.range(of: #"^principal\.[a-f0-9]{32}$"#, options: .regularExpression) != nil,
          values.nonce.range(of: #"^[a-f0-9]{64}$"#, options: .regularExpression) != nil else {
        throw DiagnosticError.wrongFixture
    }
    let dates = ISO8601DateFormatter()
    dates.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    guard let issued = dates.date(from: values.issued_at), let expires = dates.date(from: values.expires_at),
          expires.timeIntervalSince(issued) == 120, Date() >= issued, Date() < expires else {
        throw DiagnosticError.timedOut
    }
    return raw
}

private func sha256Hex(_ value: Data) -> String {
    SHA256.hash(data: value).map { String(format: "%02x", $0) }.joined()
}

@MainActor
final class EnrollmentWindow: NSObject, NSApplicationDelegate {
    private var window: NSWindow?
    private let status = NSTextField(wrappingLabelWithString: "等待开始。")
    private lazy var start = NSButton(title: "开始登记测试", target: self, action: #selector(begin))

    func applicationDidFinishLaunching(_ notification: Notification) {
        let panel = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 530, height: 245),
                             styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        panel.title = "F-02 实机公钥登记诊断"
        panel.center()
        let title = NSTextField(labelWithString: "Secure Enclave 公钥登记测试")
        title.font = .systemFont(ofSize: 20, weight: .semibold)
        let text = NSTextField(wrappingLabelWithString: "测试只会在独立数据目录写入未激活公钥。请本人完成系统认证。")
        let stack = NSStackView(views: [title, text, status, start])
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 18
        stack.edgeInsets = NSEdgeInsets(top: 26, left: 26, bottom: 26, right: 26)
        for label in [text, status] { label.preferredMaxLayoutWidth = 478 }
        panel.contentView = stack
        window = panel
        panel.makeKeyAndOrderFront(nil)
        if #available(macOS 14.0, *) { NSApp.activate() } else { NSApp.activate(ignoringOtherApps: true) }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }

    @objc private func begin() {
        start.isEnabled = false
        status.stringValue = "正在准备本机临时公钥。"
        let root = Bundle.main.bundleURL.deletingLastPathComponent()
        DispatchQueue.global(qos: .userInitiated).async {
            let message = Self.diagnose(root: root) {
                DispatchQueue.main.sync { self.confirm() }
            }
            DispatchQueue.main.async { self.status.stringValue = message }
        }
    }

    private func confirm() -> Bool {
        status.stringValue = "已核对登记挑战，等待现场确认。"
        let alert = NSAlert()
        alert.messageText = "对测试登记挑战签名"
        alert.informativeText = "点击继续后请本人完成 macOS 系统认证。"
        alert.addButton(withTitle: "继续")
        alert.addButton(withTitle: "取消")
        return alert.runModal() == .alertFirstButtonReturn
    }

    private nonisolated static func diagnose(root: URL, confirm: () -> Bool) -> String {
        do {
            let session = try readJSON(Session.self, root.appendingPathComponent("session.json"))
            guard session.scope == scope, session.run_id.range(of: #"^[a-f0-9]{32}$"#,
                  options: .regularExpression) != nil,
                  !FileManager.default.fileExists(atPath: root.appendingPathComponent("offer.json").path) else {
                throw DiagnosticError.wrongFixture
            }
            guard SecureEnclave.isAvailable,
                  let acl = SecAccessControlCreateWithFlags(nil, kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
                                                            [.privateKeyUsage, .userPresence], nil) else {
                return "当前会话无法创建受保护的临时密钥。"
            }
            let creator = context(interactive: false)
            let sealed: Data
            let point: Data
            do {
                defer { creator.invalidate() }
                let key = try SecureEnclave.P256.Signing.PrivateKey(compactRepresentable: false,
                                                                  accessControl: acl,
                                                                  authenticationContext: creator)
                sealed = key.dataRepresentation
                point = key.publicKey.x963Representation
            }
            try writeJSON(["run_id":session.run_id, "public_point_b64":point.base64EncodedString(),
                           "source":"SECURE_ENCLAVE_DIAGNOSTIC"], name: "offer.json", in: root)
            let challenge = try waitForJSON(Challenge.self, root.appendingPathComponent("challenge.json"), seconds: 25)
            let message = try verifiedMessage(challenge, session: session, fingerprint: "sha256:" + sha256Hex(point))
            guard confirm() else {
                try writeJSON(["run_id":session.run_id, "action":"CANCELLED"], name: "cancel.json", in: root)
                return "已取消，未提交登记证明。"
            }
            let auth = context(interactive: true, reason: "AARS F-02 独立测试库公钥登记诊断")
            defer { auth.invalidate() }
            let signature: P256.Signing.ECDSASignature
            do {
                let key = try SecureEnclave.P256.Signing.PrivateKey(dataRepresentation: sealed,
                                                                  authenticationContext: auth)
                signature = try key.signature(for: message)
            } catch {
                if authenticationError(error as NSError, expectedLA: .userCancel,
                                       expectedSec: errSecUserCanceled) != nil {
                    try writeJSON(["run_id":session.run_id, "action":"CANCELLED"], name:"cancel.json", in: root)
                    return "系统认证已取消，未提交登记证明。"
                }
                throw error
            }
            try writeJSON(["run_id":session.run_id, "payload_sha256":sha256Hex(message),
                           "signature_base64":signature.derRepresentation.base64EncodedString()],
                          name:"proof.json", in:root)
            struct Outcome: Decodable { let run_id: String; let status: String }
            if let outcome = try? waitForJSON(Outcome.self, root.appendingPathComponent("result.json"), seconds: 10),
               outcome.run_id == session.run_id {
                return outcome.status == "INACTIVE_PIN_STAGED"
                    ? "签名已验证。候选公钥已写入隔离库，状态为未激活。"
                    : "宿主未接受测试签名，请查看诊断报告。"
            }
            return "已生成签名证明，正在等待宿主校验。"
        } catch {
            return "诊断中断。请查看当前诊断目录。"
        }
    }
}

@main
struct EnrollmentDiagnosticApp {
    @MainActor
    static func main() throws {
        let args = Array(CommandLine.arguments.dropFirst())
        if args.count == 2 && args[0] == "--verify-message" {
            // Validate the canonical bytes without creating a key or opening an approval UI.
            let raw = try Data(contentsOf: URL(fileURLWithPath: args[1]))
            guard raw.starts(with: domain) else { throw DiagnosticError.invalidInput }
            let claims = try JSONDecoder().decode(Claims.self, from: Data(raw.dropFirst(domain.count)))
            let session = Session(scope: scope, run_id: String(repeating: "a", count: 32))
            let challenge = Challenge(scope: scope, run_id: session.run_id, payload_b64: raw.base64EncodedString())
            let verified = try verifiedMessage(challenge, session: session, fingerprint: claims.pin_sha256)
            print(sha256Hex(verified))
            return
        }
        let app = NSApplication.shared
        let delegate = EnrollmentWindow()
        app.setActivationPolicy(.regular)
        app.delegate = delegate
        withExtendedLifetime(delegate) { app.run() }
    }
}
