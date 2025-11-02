from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from typing import Optional, List, Dict
import os
import logging

logger = logging.getLogger(__name__)


class MongoDBService:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGODB_URI")
        if not self.mongo_uri:
            raise ValueError("MONGODB_URI must be set in environment variables")
        
        self.db_name = os.getenv("MONGODB_DATABASE", "resume_db")
        self.collection_name = os.getenv("MONGODB_COLLECTION", "candidates")
        
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None
    
    def connect(self):
        try:
            if "mongodb+srv://" in self.mongo_uri or "mongodb://" in self.mongo_uri:
                self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
                self.client.admin.command('ping')
                logger.info("MongoDB connection test successful")
            else:
                raise ValueError("Invalid MongoDB URI format")
            
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            try:
                self.collection.create_index("candidate_id", unique=True)
            except Exception as e:
                logger.info(f"Index may already exist: {e}")
            
            logger.info(f"Connected to MongoDB database: {self.db_name}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error connecting to MongoDB: {error_msg}")
            if "authentication failed" in error_msg.lower() or "bad auth" in error_msg.lower():
                raise Exception(
                    "MongoDB authentication failed. Please check:\n"
                    "1. Your username and password in the connection string\n"
                    "2. If password has special characters, URL encode them (@=%40, :=%3A, etc.)\n"
                    "3. The database user exists and has proper permissions\n"
                    "4. Your IP address is whitelisted in MongoDB Atlas Network Access"
                )
            raise
    
    def disconnect(self):
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    def insert_candidate(self, candidate_data: Dict) -> str:
        if self.collection is None:
            try:
                self.connect()
            except Exception as e:
                raise Exception(f"MongoDB not connected and reconnection failed: {e}")
        
        try:
            result = self.collection.insert_one(candidate_data)
            logger.info(f"Inserted candidate with ID: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error inserting candidate: {e}")
            raise
    
    def get_all_candidates(self) -> List[Dict]:
        if self.collection is None:
            raise Exception("MongoDB not connected. Call connect() first.")
        
        try:
            candidates = list(self.collection.find())
            return candidates
        except Exception as e:
            logger.error(f"Error fetching all candidates: {e}")
            raise
    
    def get_candidate_by_id(self, candidate_id: str) -> Optional[Dict]:
        if self.collection is None:
            raise Exception("MongoDB not connected. Call connect() first.")
        
        try:
            candidate = self.collection.find_one({"candidate_id": candidate_id})
            return candidate
        except Exception as e:
            logger.error(f"Error fetching candidate by ID: {e}")
            raise
