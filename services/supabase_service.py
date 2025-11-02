from supabase import create_client, Client
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SupabaseService:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.bucket_name = os.getenv("SUPABASE_BUCKET_NAME", "resumes")
        
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        try:
            buckets = self.supabase.storage.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            
            if self.bucket_name not in bucket_names:
                logger.info(f"Creating bucket {self.bucket_name}...")
                self.supabase.storage.create_bucket(self.bucket_name, public=False)
        except Exception as e:
            logger.warning(f"Could not verify bucket existence: {e}")
    
    async def upload_file(self, file_content: bytes, filename: str) -> dict:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"{timestamp}_{filename}"
            
            try:
                response = self.supabase.storage.from_(self.bucket_name).upload(
                    file_path,
                    file_content,
                    file_options={"content-type": "application/octet-stream"}
                )
                logger.info(f"Successfully uploaded file to storage: {file_path}")
            except Exception as storage_error:
                logger.error(f"Storage upload error: {storage_error}")
                error_str = str(storage_error)
                if "row-level security" in error_str.lower() or "unauthorized" in error_str.lower() or "403" in error_str:
                    raise Exception(f"Storage permission denied. Please check bucket permissions and RLS policies. Error: {storage_error}")
                raise Exception(f"Failed to upload file to storage: {storage_error}")
            
            try:
                file_url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
            except Exception as e:
                logger.warning(f"Could not get public URL: {e}")
                file_url = None
            
            metadata = {
                "id": file_path,
                "filename": filename,
                "file_path": file_path,
                "file_url": file_url,
                "created_at": datetime.now().isoformat(),
                "size": len(file_content)
            }
            
            try:
                db_response = self.supabase.table("resume_files").insert(metadata).execute()
                if db_response.data and len(db_response.data) > 0:
                    metadata["id"] = db_response.data[0].get("id", file_path)
                    logger.info("Metadata saved to database table")
            except Exception as db_error:
                error_str = str(db_error)
                if "row-level security" in error_str.lower() or "rls" in error_str.lower():
                    logger.info("Skipping database metadata save (RLS policy). Using file_path as ID.")
                else:
                    logger.warning(f"Could not save to database table (optional), using file_path as ID: {db_error}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error uploading file to Supabase: {e}")
            if "Failed to upload file to storage" in str(e) or "Storage permission denied" in str(e):
                raise
            raise Exception(f"Failed to upload file to Supabase: {str(e)}")
