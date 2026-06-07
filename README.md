# Jarvis Assistant

Jarvis is an AI-powered personal assistant for iOS and Android, built as a learning-focused backend project.

The current backend milestone is a minimal FastAPI structure with:

- centralized app configuration
- router-based endpoint organization
- a typed health-check response schema
- Bruno collection support for manual API testing

## Backend Setup

Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the FastAPI server:

```powershell
uvicorn app.main:app --reload
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

## Health Check

The first endpoint is:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok",
  "service": "jarvis-backend"
}
```

## Bruno

Bruno is used for manual API testing. The collection should live inside the project so the saved requests can be committed with the backend.

Use the local server URL:

```text
http://127.0.0.1:8000
```
