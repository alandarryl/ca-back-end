from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.search_service import search_company_info
from services.ai_service import generate_company_audit
from schemas.audit_schema import CompanyAuditSchema

app = FastAPI(
    title="Company Audit API",
    description="API de génération d'audits d'entreprises pour entretiens",
    version="1.0.0"
)

# Configuration CORS pour autoriser Next.js (par défaut http://localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuditRequest(BaseModel):
    company_name: str

@app.get("/")
def read_root():
    return {"message": "API Company Audit fonctionnelle"}

@app.post("/api/audit", response_model=CompanyAuditSchema)
async def create_audit(request: AuditRequest):
    if not request.company_name.strip():
        raise HTTPException(status_code=400, detail="Le nom de l'entreprise ne peut pas être vide.")
    
    try:
        # 1. Recherche d'informations brutes
        raw_data = search_company_info(request.company_name)
        
        # 2. Analyse et génération via Gemini
        audit = generate_company_audit(request.company_name, raw_data)
        
        return audit
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la génération de l'audit : {str(e)}"
        )