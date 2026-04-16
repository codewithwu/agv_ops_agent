"""健康检查端点."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health_check() -> dict[str, str]:
    """检查服务是否运行正常."""
    return {"status": "healthy"}
