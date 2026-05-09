import asyncio
import motor.motor_asyncio
import sys
import os

# Add backend to sys path so app can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.config import settings

async def f():
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL, tlsAllowInvalidCertificates=True)
    await client[settings.DATABASE_NAME].users.update_one(
        {"email": "sahasounak.jobs@gmail.com"}, 
        {"$set": {"name": "Sounak"}}
    )
    print("Database updated.")

asyncio.run(f())
