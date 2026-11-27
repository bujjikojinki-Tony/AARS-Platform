import CryptoKit
import LocalAuthentication
import Security
let context = LAContext()
context.interactionNotAllowed = true
var error: NSError?
let biometricReady = context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error)
let flags: SecAccessControlCreateFlags = [.privateKeyUsage, .userPresence]
let acl = SecAccessControlCreateWithFlags(nil, kSecAttrAccessibleWhenUnlockedThisDeviceOnly, flags, nil)
print("secure_enclave_available=\(SecureEnclave.isAvailable)")
print("biometric_policy_available_noninteractive=\(biometricReady)")
print("biometric_policy_error_code=\(error?.code ?? 0)")
print("user_presence_acl_constructed=\(acl != nil)")
