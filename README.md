# Resume Processing API - FastAPI Application

A FastAPI application that accepts resume uploads, extracts candidate information using Hugging Face ML models, and stores data in Supabase and MongoDB.

## Quick Start

**✅ All credentials are pre-configured in `.env` file - ready to use immediately!**

### 1. Create and Activate Virtual Environment

python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

### 2. Run Application

python main.py

Or

uvicorn main:app --reload --host 127.0.0.1 --port 8000

### 3. Access API

- **API Docs:** `http://localhost:8000/docs`
- **API Root:** `http://localhost:8000`

## API Endpoints

1. **POST** `/upload` - Upload resume (PDF/DOCX)
2. **GET** `/candidates` - List all candidates
3. **GET** `/candidate/{candidate_id}` - Get candidate details
4. **POST** `/ask/{candidate_id}` - Ask question about candidate

Use the interactive API docs at `http://localhost:8000/docs` to test all endpoints.

## Pre-Configured Setup

`.env` file already contains all required credentials (Supabase, MongoDB, Hugging Face)
 Supabase integration configured and tested
MongoDB Atlas connection configured
Hugging Face API key configured
All dependencies listed in `requirements.txt`


