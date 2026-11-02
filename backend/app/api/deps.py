from typing import AsyncGenerator
from fastapi import Header, HTTPException, Security, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.session import AsyncSessionLocal
from backend.app.core.config import settings


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def verify_admin_key(x_admin_key: str = Header(default="")):
    if not x_admin_key or x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-Key header"
        )
    return True
