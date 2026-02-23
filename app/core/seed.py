from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.plan import Plan


async def seed_plans():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Plan))
        existing = result.scalars().all()

        if existing:
            return

        free = Plan(name="free", requests_per_minute=100)
        pro = Plan(name="pro", requests_per_minute=1000)
        enterprise = Plan(name="enterprise", requests_per_minute=10000)

        db.add_all([free, pro, enterprise])
        await db.commit()