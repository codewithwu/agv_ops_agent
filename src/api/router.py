"""API 路由聚合模块."""

from fastapi import APIRouter

from src.api.v1 import agent, auth, file, health, user

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(file.router, prefix="/files", tags=["files"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
