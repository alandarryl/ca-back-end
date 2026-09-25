from pydantic import BaseModel, Field
from typing import List

class CompanyAuditSchema(BaseModel):
    company_name: str = Field(description="Nom officiel de l'entreprise")
    summary: str = Field(description="Résumé de l'activité principale de l'entreprise en 2 phrases")
    products_and_services: List[str] = Field(description="Liste des produits ou services principaux offerts")
    company_culture: List[str] = Field(description="Mots-clés ou valeurs représentant la culture d'entreprise")
    interview_questions: List[str] = Field(description="3 à 5 questions pertinentes à poser lors d'un entretien")
    recent_news: List[str] = Field(description="Faits marquants ou actualités récentes trouvées")