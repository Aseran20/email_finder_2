from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import EmailFinderRequest, EmailFinderResponse
from core.email_finder import EmailFinder

app = FastAPI(title="Email Finder MVP")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

finder = EmailFinder()

@app.post("/api/find-email", response_model=EmailFinderResponse)
async def find_email(request: EmailFinderRequest):
    if not request.domain:
        raise HTTPException(status_code=400, detail="Domain is required")
        
    if not request.fullName:
        raise HTTPException(status_code=400, detail="Full name is required")

    try:
        result = finder.find_email(request.domain, request.fullName)
        return result
    except Exception as e:
        return EmailFinderResponse(
            status="error",
            errorMessage=str(e),
            debugInfo="Internal Server Error"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
