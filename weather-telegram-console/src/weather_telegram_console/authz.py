from __future__ import annotations


class Authz:
    def __init__(self, admin_user_ids: set[int], admin_usernames: set[str] | None = None) -> None:
        self.admin_user_ids = admin_user_ids
        self.admin_usernames = admin_usernames or set()

    def is_admin(self, user_id: int | None, username: str | None = None) -> bool:
        if user_id is not None and user_id in self.admin_user_ids:
            return True
        if username is not None and username.lstrip("@").lower() in self.admin_usernames:
            return True
        return False
