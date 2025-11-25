from pydantic import BaseModel
from typing import List, Optional

class EmailFinderRequest(BaseModel):
    domain: str
    fullName: str # Made required

class EmailFinderResponse(BaseModel):
    status: str
    email: Optional[str] = None
    patternsTested: List[str] = []
    smtpLogs: List[str] = []
    catchAll: bool = False
    mxRecords: List[str] = []
    debugInfo: str = ""
    errorMessage: Optional[str] = None
