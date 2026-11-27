"""Stable, non-sensitive application errors (not MCP transport errors)."""

class TaskError(ValueError):
    def __init__(self, code: str, *, retryable: bool = False):
        self.code = code
        self.retryable = retryable
        super().__init__(code)

    def to_dict(self):
        return {"code": self.code, "message": self.code.replace("_", " ").lower(), "retryable": self.retryable}
