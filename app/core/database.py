# app/core/database.py

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

DATABASE_URL = "mongodb://localhost:27017"

client = AsyncIOMotorClient(DATABASE_URL)

# Define the MongoDB database
database = client.webchat

# Optional: If you want to use a specific collection
# Example: user_collection = database.get_collection("users")


# If you need to close the database connection when the application shuts down
async def close_db_connection():
    client.close()
