"""Initialize MongoDB database with collections and indexes."""
import asyncio
from database.mongodb import MongoDB


async def init_database():
    """Initialize database collections and indexes."""
    try:
        db = MongoDB.get_database()
        
        # Create collections if they don't exist
        collections = ['users', 'documents', 'registrations']
        for collection_name in collections:
            # Check if collection exists
            existing_collections = await db.list_collection_names()
            if collection_name not in existing_collections:
                # Create collection by inserting and deleting a dummy document
                await db[collection_name].insert_one({"_init": True})
                await db[collection_name].delete_one({"_init": True})
                print(f"✓ Created collection: {collection_name}")
            else:
                print(f"✓ Collection already exists: {collection_name}")
        
        # Create indexes
        print("\nCreating indexes...")
        
        # Users indexes
        await db.users.create_index("google_id", unique=True)
        await db.users.create_index("email")
        print("✓ Created indexes for users collection")
        
        # Documents indexes
        await db.documents.create_index("user_id")
        await db.documents.create_index("created_at")
        print("✓ Created indexes for documents collection")
        
        # Registrations indexes
        await db.registrations.create_index("student_id")
        await db.registrations.create_index("professor_id")
        await db.registrations.create_index("document_id")
        await db.registrations.create_index("status")
        print("✓ Created indexes for registrations collection")
        
        print("\n✅ Database initialization completed!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_database())

