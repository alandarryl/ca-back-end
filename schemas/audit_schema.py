from pydantic import BaseModel, Field
from typing import List, Dict, Union, Any

class CompanyAuditSchema(BaseModel):
    identite: Union[str, Dict[str, Any], List[Any]] = Field(
        default="information non trouvée", 
        description="Date de création, siège, effectif, dirigeants."
    )
    activite: Union[str, Dict[str, Any], List[Any]] = Field(
        default="information non trouvée", 
        description="Produits/services, marché cible."
    )
    finances: Union[str, Dict[str, Any], List[Any]] = Field(
        default="information non trouvée", 
        description="Chiffre d'affaires, levées de fonds."
    )
    marche: Union[str, Dict[str, Any], List[Any]] = Field(
        default="information non trouvée", 
        description="Concurrents, positionnement."
    )
    culture: Union[str, Dict[str, Any], List[Any]] = Field(
        default="information non trouvée", 
        description="Valeurs, ambiance, politique RH."
    )
    actualites: Union[str, Dict[str, Any], List[Any]] = Field(
        default="information non trouvée", 
        description="Annonces récentes, recrutements."
    )
    swot: Union[str, Dict[str, Any], List[Any]] = Field(
        default="information non trouvée", 
        description="Forces, faiblesses, opportunités, menaces."
    )
    conseils: Union[str, Dict[str, Any], List[Any]] = Field(
        default="information non trouvée", 
        description="Conseils personnalisés selon l'objectif."
    )