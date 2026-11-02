from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db_session, verify_admin_key
from backend.app.models.models import User, utcnow

router = APIRouter(prefix="/users", tags=["Users"])


class UserUpdateSchema(BaseModel):
    is_banned: Optional[bool] = None
    role: Optional[str] = None
    balance_adjustment: Optional[float] = None
    reason: Optional[str] = None


@router.get("", dependencies=[Depends(verify_admin_key)])
async def list_users(
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session)
):
    q = select(User)
    if search:
        pat = f"%{search}%"
        q = q.where(or_(User.username.ilike(pat), User.first_name.ilike(pat)))

    q = q.order_by(User.id.desc()).offset(offset).limit(limit)
    res = await session.execute(q)
    users = res.scalars().all()

    return {"success": True, "count": len(users), "users": users}


@router.get("/{id}", dependencies=[Depends(verify_admin_key)])
async def get_user_detail(id: int, session: AsyncSession = Depends(get_db_session)):
    q = select(User).where(User.id == id)
    res = await session.execute(q)
    user = res.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"success": True, "user": user}


@router.patch("/{id}", dependencies=[Depends(verify_admin_key)])
async def update_user(
    id: int,
    payload: UserUpdateSchema,
    session: AsyncSession = Depends(get_db_session)
):
    q = select(User).where(User.id == id)
    res = await session.execute(q)
    user = res.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.is_banned is not None:
        user.is_banned = payload.is_banned
    if payload.role is not None:
        user.role = payload.role
    if payload.balance_adjustment is not None:
        user.balance += payload.balance_adjustment

    user.updated_at = utcnow()
    await session.commit()
    await session.refresh(user)

    return {"success": True, "user": user}
