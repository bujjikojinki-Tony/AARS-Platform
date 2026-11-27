import Foundation
import Security

enum ApprovalPeerRole: String {
    case broker
    case service

    var identifier: String { "local.aars.omb.approval-\(rawValue)" }
}

enum PeerIdentityError: Error {
    case invalidTeamID
    case invalidBundlePath
    case osStatus(OSStatus)
}

@available(macOS 13.0, *)
struct ApprovalPeerIdentity {
    let role: ApprovalPeerRole
    private let expression: String
    private let requirement: SecRequirement

    /// The team comes from the host's trusted configuration, before listening.
    init(role: ApprovalPeerRole, trustedTeamID: String) throws {
        guard trustedTeamID.utf8.count == 10, trustedTeamID.utf8.allSatisfy({
            (65...90).contains($0) || (48...57).contains($0)
        }) else { throw PeerIdentityError.invalidTeamID }

        self.role = role
        expression = "anchor apple generic and identifier \"\(role.identifier)\""
            + " and certificate leaf[subject.OU] = \"\(trustedTeamID)\""
        var compiled: SecRequirement?
        let status = SecRequirementCreateWithString(expression as CFString, [], &compiled)
        guard status == errSecSuccess, let compiled else {
            throw PeerIdentityError.osStatus(status == errSecSuccess ? errSecInternalError : status)
        }
        requirement = compiled
    }

    /// Preflight only. Live peers require their own OS-enforced identity check.
    func verifyBundle(at absolutePath: String) throws {
        guard absolutePath.hasPrefix("/") else { throw PeerIdentityError.invalidBundlePath }
        let url = URL(fileURLWithPath: absolutePath).standardizedFileURL
        guard url.path == url.resolvingSymlinksInPath().path,
              ["app", "xpc"].contains(url.pathExtension),
              (try? url.resourceValues(forKeys: [.isDirectoryKey]).isDirectory) == true else {
            throw PeerIdentityError.invalidBundlePath
        }
        var code: SecStaticCode?
        let status = SecStaticCodeCreateWithPath(url as CFURL, [], &code)
        guard status == errSecSuccess, let code else {
            throw PeerIdentityError.osStatus(status == errSecSuccess ? errSecInternalError : status)
        }
        let flags = kSecCSCheckAllArchitectures | kSecCSStrictValidate | kSecCSCheckNestedCode | kSecCSRestrictSymlinks
        let result = SecStaticCodeCheckValidity(code, SecCSFlags(rawValue: flags), requirement)
        guard result == errSecSuccess else { throw PeerIdentityError.osStatus(result) }
    }

    /// Set the broker requirement before the host exposes an endpoint.
    func makeBrokerListener(delegate: NSXPCListenerDelegate) -> NSXPCListener {
        precondition(role == .broker)
        let listener = NSXPCListener.anonymous()
        listener.setConnectionCodeSigningRequirement(expression)
        listener.delegate = delegate
        return listener
    }

    /// Apply the peer requirement to an inactive connection, exactly once.
    func configurePeerCheck(on connection: NSXPCConnection) {
        connection.setCodeSigningRequirement(expression)
    }

    /// Set the service requirement before the broker sends its first message.
    func makeServiceConnection(to endpoint: NSXPCListenerEndpoint) -> NSXPCConnection {
        precondition(role == .service)
        let connection = NSXPCConnection(listenerEndpoint: endpoint)
        configurePeerCheck(on: connection)
        return connection
    }
}
