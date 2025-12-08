"""
User Repository - Data access for app_users table.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Sequence

from sqlalchemy import text

from core.data_repository import get_engine, query_df, exec_sql, exec_sql_return_id


@dataclass
class User:
    """User entity."""

    id: int
    username: str
    email: str
    role: str
    tenant_id: int
    is_active: bool = True
    last_login: datetime | None = None
    created_at: datetime | None = None


class UserRepository(Protocol):
    """User repository interface."""

    def get_by_id(self, id: int, *, tenant_id: int) -> User | None:
        ...

    def get_by_username(self, username: str, *, tenant_id: int) -> User | None:
        ...

    def get_by_email(self, email: str, *, tenant_id: int) -> User | None:
        ...

    def list_all(self, *, tenant_id: int, limit: int = 100, offset: int = 0) -> Sequence[User]:
        ...

    def list_active(self, *, tenant_id: int) -> Sequence[User]:
        ...

    def add(self, user: User, password_hash: str) -> User:
        ...

    def update(self, user: User) -> User:
        ...

    def update_last_login(self, user_id: int, *, tenant_id: int) -> None:
        ...

    def deactivate(self, user_id: int, *, tenant_id: int) -> bool:
        ...


class SqlUserRepository:
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self):
        self._engine = get_engine()

    def get_by_id(self, id: int, *, tenant_id: int) -> User | None:
        sql = text(
            """
            SELECT id, username, email, role, tenant_id, is_active, last_login, created_at
            FROM app_users
            WHERE id = :id AND tenant_id = :tenant_id
            """
        )
        df = query_df(sql, {"id": id, "tenant_id": tenant_id})
        if df.empty:
            return None
        return self._row_to_user(df.iloc[0].to_dict())

    def get_by_username(self, username: str, *, tenant_id: int) -> User | None:
        sql = text(
            """
            SELECT id, username, email, role, tenant_id, is_active, last_login, created_at
            FROM app_users
            WHERE LOWER(username) = LOWER(:username) AND tenant_id = :tenant_id
            """
        )
        df = query_df(sql, {"username": username, "tenant_id": tenant_id})
        if df.empty:
            return None
        return self._row_to_user(df.iloc[0].to_dict())

    def get_by_email(self, email: str, *, tenant_id: int) -> User | None:
        sql = text(
            """
            SELECT id, username, email, role, tenant_id, is_active, last_login, created_at
            FROM app_users
            WHERE LOWER(email) = LOWER(:email) AND tenant_id = :tenant_id
            """
        )
        df = query_df(sql, {"email": email, "tenant_id": tenant_id})
        if df.empty:
            return None
        return self._row_to_user(df.iloc[0].to_dict())

    def list_all(
        self, *, tenant_id: int, limit: int = 100, offset: int = 0
    ) -> Sequence[User]:
        sql = text(
            """
            SELECT id, username, email, role, tenant_id, is_active, last_login, created_at
            FROM app_users
            WHERE tenant_id = :tenant_id
            ORDER BY username ASC
            LIMIT :limit OFFSET :offset
            """
        )
        df = query_df(sql, {"tenant_id": tenant_id, "limit": limit, "offset": offset})
        return [self._row_to_user(row) for row in df.to_dict("records")]

    def list_active(self, *, tenant_id: int) -> Sequence[User]:
        sql = text(
            """
            SELECT id, username, email, role, tenant_id, is_active, last_login, created_at
            FROM app_users
            WHERE tenant_id = :tenant_id AND is_active = TRUE
            ORDER BY username ASC
            """
        )
        df = query_df(sql, {"tenant_id": tenant_id})
        return [self._row_to_user(row) for row in df.to_dict("records")]

    def add(self, user: User, password_hash: str) -> User:
        sql = text(
            """
            INSERT INTO app_users (username, email, password_hash, role, tenant_id, is_active)
            VALUES (:username, :email, :password_hash, :role, :tenant_id, :is_active)
            RETURNING id, created_at
            """
        )
        params = {
            "username": user.username,
            "email": user.email,
            "password_hash": password_hash,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "is_active": user.is_active,
        }
        engine = get_engine()
        with engine.begin() as conn:
            result = conn.execute(sql, params)
            row = result.fetchone()
            if row:
                user.id = row[0]
                user.created_at = row[1]
        return user

    def update(self, user: User) -> User:
        sql = text(
            """
            UPDATE app_users
            SET username = :username, email = :email, role = :role, is_active = :is_active
            WHERE id = :id AND tenant_id = :tenant_id
            """
        )
        exec_sql(
            sql,
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "tenant_id": user.tenant_id,
            },
        )
        return user

    def update_last_login(self, user_id: int, *, tenant_id: int) -> None:
        sql = text(
            """
            UPDATE app_users
            SET last_login = NOW()
            WHERE id = :id AND tenant_id = :tenant_id
            """
        )
        exec_sql(sql, {"id": user_id, "tenant_id": tenant_id})

    def deactivate(self, user_id: int, *, tenant_id: int) -> bool:
        sql = text(
            """
            UPDATE app_users
            SET is_active = FALSE
            WHERE id = :id AND tenant_id = :tenant_id
            RETURNING id
            """
        )
        engine = get_engine()
        with engine.begin() as conn:
            result = conn.execute(sql, {"id": user_id, "tenant_id": tenant_id})
            return result.fetchone() is not None

    def _row_to_user(self, row: dict) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            role=row["role"],
            tenant_id=row["tenant_id"],
            is_active=row.get("is_active", True),
            last_login=row.get("last_login"),
            created_at=row.get("created_at"),
        )
