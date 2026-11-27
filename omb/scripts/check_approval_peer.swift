import Foundation
import Darwin

@available(macOS 13.0, *)
@main
struct ApprovalPeerPreflight {
    struct Result: Encodable {
        let status: String
        let detail: String
        let expectedIdentifier: String?
        let signingStatus: Int32?
        let gate = "BLOCKED_APPROVAL_PLATFORM"
    }

    static func main() {
        let fields = Array(CommandLine.arguments.dropFirst())
        guard fields.count == 4, fields[0] == "--verify",
              let role = ApprovalPeerRole(rawValue: fields[1]) else {
            finish(Result(status: "INVALID_ARGUMENT", detail: "Expected --verify broker|service TEAM_ID /absolute/bundle",
                          expectedIdentifier: nil, signingStatus: nil), code: 64)
        }
        do {
            let identity = try ApprovalPeerIdentity(role: role, trustedTeamID: fields[2])
            try identity.verifyBundle(at: fields[3])
            finish(Result(status: "IDENTITY_MATCHED", detail: "Static bundle signature only",
                          expectedIdentifier: role.identifier, signingStatus: 0), code: 0)
        } catch PeerIdentityError.invalidTeamID {
            finish(Result(status: "INVALID_ARGUMENT", detail: "Expected a 10-character ASCII Team ID",
                          expectedIdentifier: role.identifier, signingStatus: nil), code: 64)
        } catch PeerIdentityError.invalidBundlePath {
            finish(Result(status: "BLOCKED", detail: "Invalid or ambiguous bundle path",
                          expectedIdentifier: role.identifier, signingStatus: nil), code: 2)
        } catch PeerIdentityError.osStatus(let status) {
            finish(Result(status: "BLOCKED", detail: "Bundle identity was not verified",
                          expectedIdentifier: role.identifier, signingStatus: status), code: 2)
        } catch {
            finish(Result(status: "BLOCKED", detail: "Verification could not complete",
                          expectedIdentifier: role.identifier, signingStatus: nil), code: 2)
        }
    }

    static func finish(_ result: Result, code: Int32) -> Never {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        do {
            let data = try encoder.encode(result)
            FileHandle.standardOutput.write(data + Data([0x0a]))
        } catch {
            exit(1)
        }
        exit(code)
    }
}
