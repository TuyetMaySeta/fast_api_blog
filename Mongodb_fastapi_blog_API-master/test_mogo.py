import motor.motor_asyncio

MONGO_URL = "mongodb+srv://maybom29032004_db_user:K5Jhjknr124ZOXah@project1.yfwfznc.mongodb.net/fastapi_demo?retryWrites=true&w=majority&appName=Project1"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.fastapi_demo  # database tên fastapi_demo

async def test_connection():
    collections = await db.list_collection_names()
    print("Collections:", collections)

import asyncio
asyncio.run(test_connection())
