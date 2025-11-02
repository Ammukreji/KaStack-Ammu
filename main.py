from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging

from services.supabase_service import SupabaseService
from services.mongodb_service import MongoDBService
from services.resume_processor import ResumeProcessor
from services.qa_service import QAService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Resume Processing API",
    description="API for uploading resumes, extracting candidate information, and Q&A",
    version="1.0.0"
)

supabase_service = SupabaseService()
mongodb_service = MongoDBService()
resume_processor = ResumeProcessor()
qa_service = QAService()


@app.on_event("startup")
async def startup_event():
    try:
        mongodb_service.connect()
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing MongoDB: {e}")
        logger.warning("Application will continue, but MongoDB features will not work until connection is fixed.")


@app.on_event("shutdown")
async def shutdown_event():
    mongodb_service.disconnect()


@app.get("/")
async def root():
    return {
        "message": "Resume Processing API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload",
            "candidates": "/candidates",
            "candidate": "/candidate/{id}",
            "ask": "/ask/{candidate_id}"
        }
    }


@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in ['pdf', 'docx']:
            raise HTTPException(
                status_code=400, 
                detail="Only PDF and DOCX files are supported"
            )
        
        file_content = await file.read()
        
        logger.info(f"Uploading file {file.filename} to Supabase...")
        supabase_metadata = await supabase_service.upload_file(
            file_content, 
            file.filename
        )
        
        logger.info("Extracting text from resume...")
        resume_text = resume_processor.extract_text(file_content, file_ext)
        
        logger.info("Processing resume with ML model...")
        candidate_data = resume_processor.process_resume(resume_text)
        
        candidate_document = {
            "candidate_id": supabase_metadata["id"],
            "education": candidate_data.get("education", {}),
            "experience": candidate_data.get("experience", {}),
            "skills": candidate_data.get("skills", []),
            "hobbies": candidate_data.get("hobbies", []),
            "certifications": candidate_data.get("certifications", []),
            "projects": candidate_data.get("projects", []),
            "introduction": candidate_data.get("introduction", ""),
            "metadata": {
                "filename": file.filename,
                "upload_time": supabase_metadata.get("created_at"),
                "supabase_file_id": supabase_metadata.get("id")
            }
        }
        
        logger.info("Saving candidate data to MongoDB...")
        mongo_id = mongodb_service.insert_candidate(candidate_document)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Resume uploaded and processed successfully",
                "candidate_id": supabase_metadata["id"],
                "mongo_id": str(mongo_id),
                "supabase_metadata": supabase_metadata
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")


@app.get("/candidates")
async def get_candidates():
    try:
        candidates = mongodb_service.get_all_candidates()
        
        summary_list = []
        for candidate in candidates:
            summary_list.append({
                "candidate_id": candidate.get("candidate_id"),
                "mongo_id": str(candidate.get("_id")),
                "filename": candidate.get("metadata", {}).get("filename"),
                "upload_time": candidate.get("metadata", {}).get("upload_time"),
                "skills": candidate.get("skills", []),
                "introduction": candidate.get("introduction", "")[:200] + "..." if len(candidate.get("introduction", "")) > 200 else candidate.get("introduction", "")
            })
        
        return JSONResponse(
            status_code=200,
            content={
                "count": len(summary_list),
                "candidates": summary_list
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching candidates: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching candidates: {str(e)}")


@app.get("/candidate/{candidate_id}")
async def get_candidate(candidate_id: str):
    try:
        candidate = mongodb_service.get_candidate_by_id(candidate_id)
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        candidate["_id"] = str(candidate["_id"])
        
        return JSONResponse(
            status_code=200,
            content=candidate
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching candidate: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching candidate: {str(e)}")


class QuestionRequest(BaseModel):
    question: str


@app.post("/ask/{candidate_id}")
async def ask_question(candidate_id: str, request: QuestionRequest):
    try:
        candidate = mongodb_service.get_candidate_by_id(candidate_id)
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        logger.info(f"Processing question: {request.question}")
        answer = await qa_service.answer_question(
            question=request.question,
            candidate_data=candidate
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "candidate_id": candidate_id,
                "question": request.question,
                "answer": answer
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
