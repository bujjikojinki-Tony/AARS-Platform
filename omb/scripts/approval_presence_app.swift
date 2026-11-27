import AppKit
import Darwin
import Foundation

struct WindowEvidence {
    let root: URL
    let sessionID: UUID

    var reportURL: URL {
        root.appendingPathComponent("AARS_F02_INTERACTIVE_\(sessionID.uuidString).json")
    }

    var progressURL: URL {
        root.appendingPathComponent("AARS_F02_GUI_PROGRESS_\(sessionID.uuidString).json")
    }

    struct Progress: Codable {
        let sessionID: UUID
        let timestampUTC: String
        let status: String
        let detail: String
    }

    struct Result: Codable {
        let sessionID: UUID
        let timestampUTC: String
        let interface: String
        let probeExitCode: Int32
        let nativeProbe: Report
    }

    func progress(_ status: String, _ detail: String) throws {
        let state = Progress(sessionID: sessionID, timestampUTC: Date().ISO8601Format(),
                             status: status, detail: detail)
        try diagnosticJSON(state).write(to: progressURL, options: .atomic)
    }

    func save(_ result: ProbeResult) throws {
        let evidence = Result(sessionID: sessionID, timestampUTC: Date().ISO8601Format(),
                              interface: "AppKit", probeExitCode: result.exitCode, nativeProbe: result.report)
        try diagnosticJSON(evidence).write(to: reportURL, options: .atomic)
    }
}

@MainActor
final class PresenceWindow: NSObject, NSApplicationDelegate {
    private var window: NSWindow?
    private var currentReport: URL?
    private let status = NSTextField(wrappingLabelWithString: "等待开始。")
    private lazy var start = NSButton(title: "开始诊断", target: self, action: #selector(begin))
    private lazy var reveal = NSButton(title: "在访达中显示报告", target: self, action: #selector(revealReport))

    func applicationDidFinishLaunching(_ notification: Notification) {
        let panel = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 540, height: 260),
                             styleMask: [.titled, .closable, .miniaturizable],
                             backing: .buffered, defer: false)
        panel.title = "AARS F-02 本机诊断"
        panel.center()

        let title = NSTextField(labelWithString: "人工在场签名诊断")
        title.font = .systemFont(ofSize: 22, weight: .semibold)
        let description = NSTextField(wrappingLabelWithString:
            "检查本机硬件签名及取消行为。系统弹窗需要你本人操作。")
        description.textColor = .secondaryLabelColor
        status.font = .systemFont(ofSize: 15)
        status.setAccessibilityLabel("诊断进度")
        reveal.isEnabled = false
        start.keyEquivalent = "\r"
        let buttons = NSStackView(views: [start, reveal])
        buttons.spacing = 12
        let stack = NSStackView(views: [title, description, status, buttons])
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 20
        stack.edgeInsets = NSEdgeInsets(top: 26, left: 26, bottom: 26, right: 26)
        [description, status].forEach { $0.preferredMaxLayoutWidth = 488 }
        panel.contentView = stack
        window = panel
        panel.makeKeyAndOrderFront(nil)
        if #available(macOS 14.0, *) {
            NSApp.activate()
        } else {
            NSApp.activate(ignoringOtherApps: true)
        }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        true
    }

    @objc private func begin() {
        start.isEnabled = false
        reveal.isEnabled = false
        currentReport = nil
        let evidence = WindowEvidence(root: Bundle.main.bundleURL.deletingLastPathComponent(),
                                      sessionID: UUID())
        do {
            try evidence.progress("RUNNING", "诊断已启动。")
        } catch {
            status.stringValue = "无法写入交付目录。请将诊断应用放在可写目录后重试。"
            start.isEnabled = true
            return
        }
        status.stringValue = "诊断已启动。"
        DispatchQueue.global(qos: .userInitiated).async {
            let result = runApprovalPresence(interactive: true, confirm: { step in
                DispatchQueue.main.sync { self.confirm(step) }
            }, progress: { detail in
                try? evidence.progress("RUNNING", detail)
                DispatchQueue.main.async { self.status.stringValue = detail }
            })
            DispatchQueue.main.async { self.finish(result, evidence: evidence) }
        }
    }

    private func confirm(_ message: String) -> Bool {
        let alert = NSAlert()
        alert.messageText = message
        alert.informativeText = "点「继续」会打开系统认证。你也可以结束诊断。"
        alert.addButton(withTitle: "继续")
        alert.addButton(withTitle: "结束诊断")
        return alert.runModal() == .alertFirstButtonReturn
    }

    private func finish(_ result: ProbeResult, evidence: WindowEvidence) {
        defer { start.isEnabled = true }
        do {
            try evidence.save(result)
            try? evidence.progress(result.report.status, "已保存最终诊断报告。")
            currentReport = evidence.reportURL
            reveal.isEnabled = true
            switch result.report.status {
            case "PRIMITIVES_PASS":
                status.stringValue = "硬件签名诊断通过。可信审批组件仍待验收。\n报告已保存。"
            case "FAIL":
                status.stringValue = "诊断发现签名行为不符合要求。\n报告已保存。"
            default:
                status.stringValue = "诊断未通过或提前结束。\n报告已保存。"
            }
        } catch {
            status.stringValue = "诊断结束，但报告无法写入。"
        }
    }

    @objc private func revealReport() {
        if let currentReport {
            NSWorkspace.shared.activateFileViewerSelecting([currentReport])
        }
    }
}

@main
struct PresenceApplication {
    @MainActor
    static func main() {
        if Array(CommandLine.arguments.dropFirst()) == ["--self-check"] {
            selfCheck()
        }
        let app = NSApplication.shared
        let delegate = PresenceWindow()
        app.setActivationPolicy(.regular)
        app.delegate = delegate
        withExtendedLifetime(delegate) {
            app.run()
        }
    }

    private static func selfCheck() -> Never {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("aars-f02-\(UUID().uuidString)")
        do {
            try FileManager.default.createDirectory(at: root, withIntermediateDirectories: false)
            defer { try? FileManager.default.removeItem(at: root) }
            let evidence = WindowEvidence(root: root, sessionID: UUID())
            try evidence.progress("RUNNING", "诊断已启动。")
            let result = runApprovalPresence(interactive: false, confirm: { _ in false }, progress: { _ in })
            try evidence.save(result)
            try evidence.progress(result.report.status, "已保存最终诊断报告。")
            let progress = try JSONSerialization.jsonObject(with: Data(contentsOf: evidence.progressURL))
                as? [String: Any]
            let report = try JSONSerialization.jsonObject(with: Data(contentsOf: evidence.reportURL))
                as? [String: Any]
            guard progress?["status"] as? String == result.report.status,
                  report?["interface"] as? String == "AppKit",
                  let native = report?["native_probe"] as? [String: Any],
                  native["gate"] as? String == "BLOCKED_APPROVAL_PLATFORM" else {
                throw CocoaError(.fileReadCorruptFile)
            }
            FileHandle.standardOutput.write(try diagnosticJSON([
                "self_check": "PASS", "native_probe_status": result.report.status, "evidence_saved": "PASS",
            ]))
        } catch {
            FileHandle.standardError.write(Data("本机窗口的报告写入自检失败。\n".utf8))
            exit(1)
        }
        exit(0)
    }
}
