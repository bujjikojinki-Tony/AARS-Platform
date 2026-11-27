// Development verifier for generated fixture receipts. It has no signing or approval entry point.
import CryptoKit
import Foundation

struct Fixture: Decodable {
    let publicKeyBase64: String
    let receipt: String
    let expectedStatementSha256: String
}

let domain = "AARS-OMB-TASK-APPROVAL-V1"
let fixture = try JSONDecoder().decode(Fixture.self, from: FileHandle.standardInput.readDataToEndOfFile())
guard var fields = try JSONSerialization.jsonObject(with: Data(fixture.receipt.utf8)) as? [String: Any],
      let encoded = fields.removeValue(forKey: "signature_base64") as? String,
      let der = Data(base64Encoded: encoded),
      let point = Data(base64Encoded: fixture.publicKeyBase64),
      let version = fields["domain"] as? String, version == domain else {
    print("INVALID_FIXTURE")
    exit(2)
}
let options: JSONSerialization.WritingOptions = [.fragmentsAllowed, .withoutEscapingSlashes]
func fragment(_ value: Any) throws -> String {
    try String(decoding: JSONSerialization.data(withJSONObject: value, options: options), as: UTF8.self)
}
let orderedFields = try fields.keys.sorted().map { name in
    try fragment(name) + ":" + fragment(fields[name] ?? NSNull())
}
let statement = Data((domain + "\n{" + orderedFields.joined(separator: ",") + "}").utf8)
let fingerprint = "sha256:" + SHA256.hash(data: statement).map { String(format: "%02x", $0) }.joined()
let key = try P256.Signing.PublicKey(x963Representation: point)
let signature = try P256.Signing.ECDSASignature(derRepresentation: der)
let verified = key.isValidSignature(signature, for: statement)
print("statement_bytes_match=\(fingerprint == fixture.expectedStatementSha256)")
print("signature_valid=\(verified)")
