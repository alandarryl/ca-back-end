from pydantic import BaseModel, Field
from typing import List, Union

class CompanyAuditSchema(BaseModel):
    identite: str = Field(default="information non trouvée", description="Date de création, siège, effectif, dirigeants.")
    activite: str = Field(default="information non trouvée", description="Produits/services, marché cible.")
    finances: str = Field(default="information non trouvée", description="Chiffre d'affaires, levées de fonds.")
    marche: Union[str, List[str]] = Field(default="information non trouvée", description="Concurrents, positionnement.")
    culture: Union[str, List[str]] = Field(default="information non trouvée", description="Valeurs, ambiance, politique RH.")
    actualites: Union[str, List[str]] = Field(default="information non trouvée", description="Annonces récentes, recrutements.")
    swot: Union[str, dict] = Field(default="information non trouvée", description="Forces, faiblesses, opportunités, menaces.")
    conseils: Union[str, List[str]] = Field(default="information non trouvée", description="Conseils personnalisés selon l'objectif.")