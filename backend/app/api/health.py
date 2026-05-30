from fastapi import APIRouter, HTTPException, Request, status

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/db")
async def database_health(request: Request) -> dict[str, str]:
    try:
        await request.app.state.database_check(request.app)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database health check failed",
        ) from exc

    return {"status": "ok"}
