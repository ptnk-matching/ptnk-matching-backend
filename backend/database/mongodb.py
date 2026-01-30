"""MongoDB database connection and configuration."""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from typing import Optional

class MongoDB:
    """MongoDB database connection manager."""
    
    _client: Optional[AsyncIOMotorClient] = None
    _db = None
    
    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        """Get or create MongoDB client."""
        if cls._client is None:
            connection_string = os.getenv("MONGODB_URI")
            if not connection_string:
                raise ValueError(
                    "MONGODB_URI environment variable is required. "
                    "Get your connection string from MongoDB Atlas."
                )
            # Create MongoDB client with connection string
            # For mongodb+srv://, SSL/TLS is handled automatically
            # But we need to ensure connection string has proper parameters
            try:
                # Ensure connection string has retryWrites and w=majority
                if 'retryWrites' not in connection_string:
                    if '?' in connection_string:
                        connection_string += '&retryWrites=true&w=majority'
                    else:
                        connection_string += '?retryWrites=true&w=majority'
                
                # Use ServerApi version 1 (recommended by MongoDB Atlas)
                cls._client = AsyncIOMotorClient(
                    connection_string,
                    server_api=ServerApi('1'),
                    serverSelectionTimeoutMS=30000,  # 30 seconds
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                )
                print(f"✅ MongoDB client created successfully")
                print(f"Connection string: {connection_string[:50]}...")
            except Exception as e:
                print(f"❌ Error creating MongoDB client: {e}")
                print("\n⚠️ IMPORTANT: IP Address not whitelisted!")
                print("\nPlease do the following:")
                print("1. In MongoDB Atlas dashboard, click 'Add Current IP Address' button in the yellow banner")
                print("   OR go to: Network Access → Add IP Address → Allow Access from Anywhere (0.0.0.0/0)")
                print("2. Wait 1-2 minutes for changes to apply")
                print("3. Restart backend server")
                print("\nOther checks:")
                print("- MONGODB_URI format: mongodb+srv://username:password@cluster.net/?retryWrites=true&w=majority")
                print("- Username and password are correct")
                print("- Password doesn't contain special characters (or is URL encoded)")
                raise
        return cls._client
    
    @classmethod
    def get_database(cls):
        """Get database instance."""
        if cls._db is None:
            client = cls.get_client()
            db_name = os.getenv("MONGODB_DB_NAME", "hanh_matching")
            cls._db = client[db_name]
        return cls._db
    
    @classmethod
    async def close(cls):
        """Close MongoDB connection."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None

