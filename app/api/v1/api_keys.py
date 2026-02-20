from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.api_key import APIKey
from app.models.organization import Organization
from app.core.security import generate_api_key, hash_api_key

router = APIRouter()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/organizations/{org_id}/api-keys")
async def create_api_key(
    org_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        return {"error": "Organization not found"}

    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)

    api_key = APIKey(
        key_hash=key_hash,
        organization_id=org.id,
    )

    db.add(api_key)
    await db.commit()

    return {
        "api_key": raw_key  
    }