#!/usr/bin/env python3
"""
Test simple de conexión a DB
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, text

from app.models.contact import Contact

async def test_simple_db():
    """Test simple de conexión y query"""

    # Crear engine
    engine = create_async_engine(
        "postgresql+asyncpg://sms_user:sms_password@localhost:15432/sms_marketing",
        echo=True  # Para ver las queries
    )

    # Crear session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Test 1: Query simple
            print("🔄 Test 1: Query simple...")
            result = await session.execute(text("SELECT COUNT(*) FROM contacts"))
            count = result.scalar()
            print(f"✅ Total contacts: {count:,}")

            # Test 2: Query con modelo
            print("\n🔄 Test 2: Query con modelo...")
            query = select(func.count(Contact.id))
            result = await session.execute(query)
            model_count = result.scalar()
            print(f"✅ Model count: {model_count:,}")

            # Test 3: Query de estados
            print("\n🔄 Test 3: Query de estados...")
            state_query = select(Contact.state_name, func.count(Contact.id).label("count")).where(
                Contact.state_name.is_not(None)
            ).group_by(Contact.state_name).order_by(func.count(Contact.id).desc()).limit(5)

            state_result = await session.execute(state_query)
            states = state_result.fetchall()

            print("✅ Top 5 estados:")
            for state in states:
                print(f"   {state.state_name}: {state.count:,} contactos")

            print("\n🎉 ¡Todos los tests pasaron!")

        except Exception as e:
            print(f"❌ Error: {e}")
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_simple_db())
