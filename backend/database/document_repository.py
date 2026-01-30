"""Document repository for MongoDB operations."""
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from database.mongodb import MongoDB


class DocumentRepository:
    """Repository for document operations."""
    
    def __init__(self):
        self.db = MongoDB.get_database()
        self.collection = self.db.documents
    
    async def create_document(self, document_data: dict) -> str:
        """Create a new document record."""
        document_data['created_at'] = datetime.utcnow()
        result = await self.collection.insert_one(document_data)
        return str(result.inserted_id)
    
    async def get_document_by_id(self, document_id: str) -> Optional[dict]:
        """Get document by ID."""
        doc = await self.collection.find_one({"_id": ObjectId(document_id)})
        if doc:
            doc['id'] = str(doc['_id'])
            del doc['_id']
        return doc
    
    async def get_documents_by_user(self, user_id: str) -> List[dict]:
        """Get all documents for a user."""
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)
        documents = []
        async for doc in cursor:
            doc['id'] = str(doc['_id'])
            del doc['_id']
            documents.append(doc)
        return documents
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document."""
        result = await self.collection.delete_one({"_id": ObjectId(document_id)})
        return result.deleted_count > 0

