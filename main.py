from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.search_service import search_company_info
from services.ai_service import generate_company_audit
from services.pdf_service import generate_audit_pdf
from schemas.audit_schema import CompanyAuditSchema

app = FastAPI(
    title="Company Audit API",
    description="API de génération d'audits d'entreprises pour entretiens",
    version="1.0.0"
)

# Configuration CORS (à placer tout de suite après FastAPI())
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Déclaration des modèles Pydantic (avant leur utilisation dans les routes)
class AuditRequest(BaseModel):
    company_name: str

# Routes de l'API
@app.get("/")
def read_root():
    return {"message": "API Company Audit fonctionnelle"}

@app.post("/api/audit", response_model=CompanyAuditSchema)
async def create_audit(request: AuditRequest):
    if not request.company_name.strip():
        raise HTTPException(status_code=400, detail="Le nom de l'entreprise ne peut pas être vide.")
    
    try:
        raw_data = search_company_info(request.company_name)
        audit = generate_company_audit(request.company_name, raw_data)
        return audit
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la génération de l'audit : {str(e)}"
        )

@app.post("/api/audit/pdf")
async def create_audit_pdf(request: AuditRequest):
    """
    Génère un audit et renvoie directement le fichier PDF téléchargeable.
    """
    if not request.company_name.strip():
        raise HTTPException(status_code=400, detail="Le nom de l'entreprise ne peut pas être vide.")
    
    try:
        raw_data = search_company_info(request.company_name)
        audit = generate_company_audit(request.company_name, raw_data)
        
        pdf_buffer = generate_audit_pdf(audit)
        
        filename = f"audit_{request.company_name.lower().replace(' ', '_')}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la génération du PDF : {str(e)}"
        )