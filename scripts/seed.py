import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from passlib.context import CryptContext

# Add the project root to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from models.base import Base
from models.user import User

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_data():
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found in .env file.")
        return

    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        # Create tables if they don't exist (optional, Alembic handles this)
        # await conn.run_sync(Base.metadata.create_all)
        pass

    async with async_session() as session:
        # Seed Users
        existing_user = await session.execute(text("SELECT 1 FROM users WHERE email = :email"), {"email": "admin@example.com"})
        if not existing_user.scalar_one_or_none():
            hashed_password = pwd_context.hash("adminpassword") # TODO: Use a strong password and manage securely
            admin_user = User(
                email="admin@example.com",
                hashed_password=hashed_password,
                full_name="System Administrator"
            )
            session.add(admin_user)
            print("Added admin user.")
        else:
            print("Admin user already exists.")

        # TODO: Add more seeding logic for other models (e.g., initial Odoo configurations, RAG data)
        # Example for RAG data (conceptual, requires RAGStore client)
        # from modules.rag_store import RAGStore
        # rag_store = RAGStore()
        # await rag_store.add_documents(
        #     documents=["This is a sample knowledge base document."],
        #     metadatas=[{"source": "seed_script"}],
        #     ids=["doc_1"]
        # )

        await session.commit()
        print("Data seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_data())


