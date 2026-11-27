import CryptoKit
import LocalAuthentication
import Security

// Readiness only. Do not request authentication or create a Keychain item.
func reportPolicy(_ name: String, _ policy: LAPolicy) {
    let context = LAContext()
    context.interactionNotAllowed = true
    var error: NSError?
    let available = context.canEvaluatePolicy(policy, error: &error)
    print("\(name)_available=\(available)")
    print("\(name)_error_domain=\(error?.domain ?? "none")")
    print("\(name)_error_code=\(error?.code ?? 0)")
}

let flags: SecAccessControlCreateFlags = [.privateKeyUsage, .userPresence]
let acl = SecAccessControlCreateWithFlags(nil, kSecAttrAccessibleWhenUnlockedThisDeviceOnly, flags, nil)
print("secure_enclave_available=\(SecureEnclave.isAvailable)")
print("user_presence_acl_constructed=\(acl != nil)")
reportPolicy("owner_authentication", .deviceOwnerAuthentication)
reportPolicy("biometric_authentication", .deviceOwnerAuthenticationWithBiometrics)
