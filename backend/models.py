from pydantic import BaseModel
from typing import List, Optional

class EmailFinderRequest(BaseModel):
    domain: str
    fullName: str # Made required

class CheckEmailRequest(BaseModel):
    email: str
    fullName: Optional[str] = None  # Optional for fallback search

class BulkSearchItem(BaseModel):
    domain: str
    fullName: str

class BulkSearchJsonRequest(BaseModel):
    searches: List[BulkSearchItem]

class EmailFinderResponse(BaseModel):
    status: str
    email: Optional[str] = None
    patternsTested: List[str] = []
    smtpLogs: List[str] = []
    catchAll: bool = False
    mxRecords: List[str] = []
    debugInfo: str = ""
    errorMessage: Optional[str] = None
