import Darwin
import Foundation

@main
struct PresenceCLI {
    static func main() {
        let args = Array(CommandLine.arguments.dropFirst())
        guard args.isEmpty || args == ["--interactive"] else {
            emit(ProbeResult("invalid", "INVALID_ARGUMENT", [], 64))
        }
        let interactive = args == ["--interactive"]
        guard !interactive || isatty(STDIN_FILENO) != 0 else {
            emit(ProbeResult("interactive", "BLOCKED", [Check("operator_terminal", "BLOCKED")], 2))
        }
        emit(runApprovalPresence(interactive: interactive, confirm: prompt, progress: { _ in }))
    }

    static func prompt(_ message: String) -> Bool {
        FileHandle.standardError.write(Data((message + " 准备好请按回车，输入其他文字可退出。\n").utf8))
        return readLine() == ""
    }

    static func emit(_ result: ProbeResult) -> Never {
        do {
            FileHandle.standardOutput.write(try diagnosticJSON(result.report))
        } catch {
            FileHandle.standardError.write(Data("无法生成 F-02 诊断报告。\n".utf8))
            exit(1)
        }
        exit(result.exitCode)
    }
}
