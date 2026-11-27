import CryptoKit
import Darwin
import Foundation
import LocalAuthentication
import Security

// This probe signs only fixed diagnostic messages. It cannot generate an AARS receipt.
struct Check: Codable {
    let name: String
    let status: String
    let errorDomain: String?
    let errorCode: Int?

    init(_ name: String, _ status: String, error: NSError? = nil) {
        self.name = name
        self.status = status
        self.errorDomain = error?.domain
        self.errorCode = error?.code
    }
}

struct Report: Codable {
    let scope = "AARS-OMB-F02 diagnostic"
    let mode: String
    let status: String
    let gate: String
    let checks: [Check]

    enum CodingKeys: String, CodingKey { case scope, mode, status, gate, checks }
}

func emit(_ mode: String, _ status: String, _ checks: [Check], _ code: Int32) -> Never {
    let report = Report(mode: mode, status: status, gate: "BLOCKED_APPROVAL_PLATFORM", checks: checks)
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
    encoder.keyEncodingStrategy = .convertToSnakeCase
    if let output = try? encoder.encode(report) {
        FileHandle.standardOutput.write(output + Data([0x0a]))
    }
    exit(code)
}

func context(interactive: Bool, reason: String = "") -> LAContext {
    let result = LAContext()
    result.interactionNotAllowed = !interactive
    result.touchIDAuthenticationAllowableReuseDuration = 0
    if interactive {
        result.localizedReason = reason
    }
    return result
}

func capability(_ name: String, _ policy: LAPolicy, interactive: Bool) -> Check {
    let probe = context(interactive: interactive)
    defer { probe.invalidate() }
    var error: NSError?
    let available = probe.canEvaluatePolicy(policy, error: &error)
    return Check(name, available ? "PASS" : "BLOCKED", error: error)
}

func authenticationError(_ error: NSError, expectedLA: LAError.Code, expectedSec: OSStatus) -> NSError? {
    var next: NSError? = error
    for _ in 0..<8 {
        guard let current = next else { break }
        if (current.domain == LAError.errorDomain && current.code == expectedLA.rawValue)
            || (current.domain == NSOSStatusErrorDomain && current.code == Int(expectedSec)) {
            return current
        }
        next = current.userInfo[NSUnderlyingErrorKey] as? NSError
    }
    return nil
}

func sign(_ label: String, envelope: Data, publicKey: P256.Signing.PublicKey, interactive: Bool) throws -> Bool {
    let auth = context(interactive: interactive, reason: "AARS 本机签名诊断：\(label)")
    defer { auth.invalidate() }
    let key = try SecureEnclave.P256.Signing.PrivateKey(dataRepresentation: envelope, authenticationContext: auth)
    let message = Data("AARS-OMB-F02-PRESENCE-DIAGNOSTIC-V1\n\(label)".utf8)
    let signature = try key.signature(for: message)
    return publicKey.isValidSignature(signature, for: message)
}

func signWithoutInteraction(_ label: String, envelope: Data, publicKey: P256.Signing.PublicKey) -> Check {
    do {
        _ = try sign(label, envelope: envelope, publicKey: publicKey, interactive: false)
        return Check(label, "FAIL")
    } catch {
        let error = error as NSError
        if let denied = authenticationError(error, expectedLA: .notInteractive, expectedSec: errSecInteractionNotAllowed) {
            return Check(label, "PASS", error: denied)
        }
        return Check(label, "BLOCKED", error: error)
    }
}

func prompt(_ description: String) -> Bool {
    FileHandle.standardError.write(Data((description + " 准备好请按回车，输入其他文字可退出。\n").utf8))
    return readLine() == ""
}

let args = Array(CommandLine.arguments.dropFirst())
guard args.isEmpty || args == ["--interactive"] else {
    emit("invalid", "INVALID_ARGUMENT", [], 64)
}
let interactive = args == ["--interactive"]
let mode = interactive ? "interactive" : "noninteractive"
guard !interactive || isatty(STDIN_FILENO) != 0 else {
    emit(mode, "BLOCKED", [Check("operator_terminal", "BLOCKED")], 2)
}

let enclave = SecureEnclave.isAvailable
var checks = [
    Check("secure_enclave", enclave ? "PASS" : "BLOCKED"),
    capability("device_owner_policy", .deviceOwnerAuthentication, interactive: interactive),
    capability("biometric_policy", .deviceOwnerAuthenticationWithBiometrics, interactive: interactive),
]
var aclError: Unmanaged<CFError>?
guard let acl = SecAccessControlCreateWithFlags(nil, kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
                                               [.privateKeyUsage, .userPresence], &aclError) else {
    let detail = aclError.map { ($0.takeRetainedValue() as Error) as NSError }
    checks.append(Check("presence_acl", "BLOCKED", error: detail))
    emit(mode, "BLOCKED", checks, 2)
}
checks.append(Check("presence_acl", "PASS"))
guard enclave else {
    checks.append(Check("hardware_key_creation", "PENDING"))
    checks.append(Check("noninteractive_signature_rejected", "PENDING"))
    checks.append(Check("interactive_signatures_and_cancel", "PENDING"))
    emit(mode, "BLOCKED", checks, 2)
}

// CryptoKit's sealed representation stays confined to this process. The probe
// never adds a Keychain item or emits the representation, signature or key.
let creator = context(interactive: false)
let envelope: Data
let publicKey: P256.Signing.PublicKey
do {
    defer { creator.invalidate() }
    let key = try SecureEnclave.P256.Signing.PrivateKey(compactRepresentable: false, accessControl: acl,
                                                      authenticationContext: creator)
    envelope = key.dataRepresentation
    publicKey = key.publicKey
    checks.append(Check("hardware_key_creation", "PASS"))
} catch {
    checks.append(Check("hardware_key_creation", "BLOCKED", error: error as NSError))
    emit(mode, "BLOCKED", checks, 2)
}
let denied = signWithoutInteraction("noninteractive_signature_rejected", envelope: envelope, publicKey: publicKey)
checks.append(denied)
guard denied.status == "PASS" else {
    emit(mode, denied.status, checks, denied.status == "FAIL" ? 1 : 2)
}
guard interactive else {
    checks.append(Check("interactive_signatures_and_cancel", "PENDING"))
    emit(mode, "PRECHECK_PASS", checks, 0)
}

for label in ["interactive_signature_1", "interactive_signature_2"] {
    guard prompt("请在系统弹窗中确认本次诊断签名。") else {
        checks.append(Check(label, "PENDING"))
        emit(mode, "BLOCKED", checks, 2)
    }
    do {
        let verified = try sign(label, envelope: envelope, publicKey: publicKey, interactive: true)
        checks.append(Check(label, verified ? "PASS" : "FAIL"))
        guard verified else { emit(mode, "FAIL", checks, 1) }
    } catch {
        checks.append(Check(label, "BLOCKED", error: error as NSError))
        emit(mode, "BLOCKED", checks, 2)
    }
}

let after = signWithoutInteraction("noninteractive_signature_rejected_after_success", envelope: envelope,
                                   publicKey: publicKey)
checks.append(after)
guard after.status == "PASS" else { emit(mode, after.status, checks, after.status == "FAIL" ? 1 : 2) }
guard prompt("请在最后一次系统弹窗中点取消。") else {
    checks.append(Check("interactive_cancel", "PENDING"))
    emit(mode, "BLOCKED", checks, 2)
}
do {
    _ = try sign("interactive_cancel", envelope: envelope, publicKey: publicKey, interactive: true)
    checks.append(Check("interactive_cancel", "FAIL"))
    emit(mode, "FAIL", checks, 1)
} catch {
    let error = error as NSError
    guard let cancelled = authenticationError(error, expectedLA: .userCancel, expectedSec: errSecUserCanceled) else {
        checks.append(Check("interactive_cancel", "BLOCKED", error: error))
        emit(mode, "BLOCKED", checks, 2)
    }
    checks.append(Check("interactive_cancel", "PASS", error: cancelled))
    checks.append(Check("trusted_broker_and_enrollment", "PENDING"))
    emit(mode, "PRIMITIVES_PASS", checks, 0)
}
