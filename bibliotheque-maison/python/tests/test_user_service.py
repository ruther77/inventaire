"""Tests pour auth.user_service."""

from __future__ import annotations

from datetime import datetime, timezone

from auth.user_service import (
    ALLOWED_ROLES,
    PasswordPolicy,
    authenticate_user,
    create_user,
    generate_secure_password,
    hash_password,
    reset_user_password,
    update_user_role,
    verify_password,
)


class MemoryUserRepo:
    def __init__(self):
        self.users = {}
        self.next_id = 1

    def get_user_by_login(self, identifier: str):
        lowered = identifier.lower()
        for user in self.users.values():
            if user["username"].lower() == lowered or user["email"].lower() == lowered:
                return dict(user)
        return None

    def get_user_by_id(self, user_id: int):
        user = self.users.get(int(user_id))
        return dict(user) if user else None

    def create_user(self, payload):
        user_id = self.next_id
        self.next_id += 1
        record = {
            "id": user_id,
            "username": payload["username"],
            "email": payload["email"],
            "password_hash": payload["password_hash"],
            "role": payload["role"],
            "created_at": datetime.now(timezone.utc),
        }
        self.users[user_id] = record
        return dict(record)

    def update_user_role(self, user_id: int, role: str):
        self.users[int(user_id)]["role"] = role

    def update_user_password(self, user_id: int, password_hash: str):
        self.users[int(user_id)]["password_hash"] = password_hash

    def count_admins(self) -> int:
        return sum(1 for user in self.users.values() if user["role"] == "admin")


def test_generate_secure_password_policy():
    policy = PasswordPolicy(length=12)
    password = generate_secure_password(policy)
    assert len(password) == 12
    assert any(c.islower() for c in password)
    assert any(c.isupper() for c in password)
    assert any(c.isdigit() for c in password)
    assert any(c in policy.symbols for c in password)


def test_hash_and_verify_password():
    hashed = hash_password("Test1234!")
    assert verify_password("Test1234!", hashed) is True
    assert verify_password("Wrong", hashed) is False


def test_create_and_authenticate_user():
    repo = MemoryUserRepo()
    created = create_user(repo, "alice", "alice@example.com", "Strong123!", role="admin")
    assert created["role"] == "admin"
    auth = authenticate_user(repo, "alice", "Strong123!")
    assert auth is not None
    assert auth["email"] == "alice@example.com"


def test_update_user_role_protects_last_admin():
    repo = MemoryUserRepo()
    user = create_user(repo, "admin", "admin@example.com", "Strong123!", role="admin")

    try:
        update_user_role(repo, user["id"], "standard")
    except ValueError as exc:
        assert "last" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError when removing last admin")


def test_reset_user_password_updates_hash():
    repo = MemoryUserRepo()
    user = create_user(repo, "bob", "bob@example.com", "Strong123!", role="manager")
    new_password = reset_user_password(repo, user["id"], new_password="NewPass123!")
    assert new_password == "NewPass123!"
    stored = repo.get_user_by_id(user["id"])
    assert verify_password("NewPass123!", stored["password_hash"]) is True
