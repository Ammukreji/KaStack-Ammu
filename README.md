# Resume Processing API - FastAPI Application

A FastAPI application that accepts resume uploads, extracts candidate information using Hugging Face ML models, and stores data in Supabase and MongoDB.

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Ammukreji/KaStack-Ammu.git
cd KaStack-Ammu
```

### 2. Set Up Environment Variables

Copy the example environment file and configure with your credentials:

```bash
copy .env.example .env
```

Edit `.env` file with your actual credentials:
- Supabase URL and API key
- MongoDB Atlas connection string
- Hugging Face API key

### 3. Create and Activate Virtual Environment

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. Run Application

```bash
python main.py
```

Or

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 5. Access API

- **API Docs:** `http://localhost:8000/docs`
- **API Root:** `http://localhost:8000`

## API Endpoints

1. **POST** `/upload` - Upload resume (PDF/DOCX)
2. **GET** `/candidates` - List all candidates
3. **GET** `/candidate/{candidate_id}` - Get candidate details
4. **POST** `/ask/{candidate_id}` - Ask question about candidate

Use the interactive API docs at `http://localhost:8000/docs` to test all endpoints.

## Environment Variables

See `.env.example` for required environment variables. Create a `.env` file based on the example:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon/public key
- `SUPABASE_BUCKET_NAME` - Storage bucket name (default: resumes)
- `MONGODB_URI` - MongoDB connection string
- `MONGODB_DATABASE` - Database name (default: resume_db)
- `MONGODB_COLLECTION` - Collection name (default: candidates)
- `HUGGINGFACE_API_KEY` - Your Hugging Face API token
- `HF_EXTRACTION_MODEL` - Model for text extraction
- `HF_QA_MODEL` - Model for Q&A endpoint

## Setup Requirements

- Ensure MongoDB Atlas IP whitelist includes your IP address
- Configure Supabase storage bucket RLS policies for uploads
- Get Hugging Face API key from https://huggingface.co/settings/tokens


