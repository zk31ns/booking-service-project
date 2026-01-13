"""Модуль пользователей и аутентификации."""

from app.api.v1.users.router import auth_router, router

__all__ = ['auth_router', 'router']
