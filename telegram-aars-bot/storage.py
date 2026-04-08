from typing import Optional

from models import ProjectSession


class InMemoryStorage:
    def __init__(self):
        self.active_session: Optional[ProjectSession] = None

    def get_active_session(self) -> Optional[ProjectSession]:
        return self.active_session

    def save_active_session(self, session: ProjectSession) -> None:
        self.active_session = session

    def clear_active_session(self) -> None:
        self.active_session = None


storage = InMemoryStorage()
