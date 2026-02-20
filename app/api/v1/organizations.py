from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.organization import Organization

router = APIRouter()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/organizations")
async def create_organization(
    name: str,
    db: AsyncSession = Depends(get_db),
):
    org = Organization(name=name)
    db.add(org)
    await db.commit()
    await db.refresh(org)

    return {"id": str(org.id), "name": org.name}