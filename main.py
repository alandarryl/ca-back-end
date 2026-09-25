import ollama
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.search_service import search_company_info
from services.ai_service import generate_company_audit
from services.pdf_service import generate_audit_pdf
from schemas.audit_schema import CompanyAuditSchema

app = FastAPI(
    title="Company Audit API",
    description="API de génération d'audits d'entreprises pour entretiens",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèle de requête avec gestion multi-provider & objectif
class AuditRequest(BaseModel):
    company_name: str
    provider: str = Field(default="ollama", description="Fournisseur : 'ollama' ou 'gemini'")
    model_name: str = Field(default="qwen2.5:1.5b", description="Nom du modèle LLM")
    objectif: str = Field(default="general", description="candidature, entretien, collaboration, etude_marche, general")

@app.get("/")
def read_root():
    return {"message": "API Company Audit fonctionnelle"}

@app.get("/api/models")
def get_available_models():
    """Renvoie la liste des modèles disponibles."""
    local_models = []
    try:
        list_res = ollama.list()
        # Modèles sous forme d'objets (ollama-python >= 0.3.0) ou de dicts
        for m in list_res.get('models', []):
            name = getattr(m, 'model', None) or (m.get('model') or m.get('name') if isinstance(m, dict) else None)
            if name:
                local_models.append(name)
    except Exception:
        pass  # Ollama est éteint ou indisponible

    return {
        "providers": {
            "ollama": local_models,
            "gemini": ["gemini-2.5-flash", "gemini-3.8-flash"]
        }
    }

@app.post("/api/audit", response_model=CompanyAuditSchema)
async def create_audit(request: AuditRequest):
    if not request.company_name.strip():
        raise HTTPException(status_code=400, detail="Le nom de l'entreprise ne peut pas être vide.")
    
    try:
        raw_data = search_company_info(request.company_name)
        
        # Passage du paramètre 'objectif'
        audit = generate_company_audit(
            company_name=request.company_name, 
            raw_data=raw_data,
            provider=request.provider,
            model_name=request.model_name,
            objectif=request.objectif
        )
        return audit
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la génération de l'audit : {str(e)}"
        )

@app.post("/api/audit/pdf")
async def create_audit_pdf(request: AuditRequest):
    """Génère un audit et renvoie directement le fichier PDF téléchargeable."""
    if not request.company_name.strip():
        raise HTTPException(status_code=400, detail="Le nom de l'entreprise ne peut pas être vide.")
    
    try:
        raw_data = search_company_info(request.company_name)
        
        # Passage du paramètre 'objectif'
        audit = generate_company_audit(
            company_name=request.company_name, 
            raw_data=raw_data,
            provider=request.provider,
            model_name=request.model_name,
            objectif=request.objectif
        )
        
        pdf_buffer = generate_audit_pdf(audit, company_name=request.company_name)
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