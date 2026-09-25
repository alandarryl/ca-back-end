# Remplace cette ligne :
# from duckduckgo_search import DDGS

# Par celle-ci :
from ddgs import DDGS

def search_company_info(company_name: str) -> str:
    """
    Recherche des informations sur une entreprise via DuckDuckGo
    et retourne une synthèse textuelle brute.
    """
    query = f"{company_name} entreprise produits culture actualités"
    results_text = []

    with DDGS() as ddgs:
        # On récupère les 5 premiers résultats du web
        results = ddgs.text(query, max_results=5)
        
        for result in results:
            title = result.get("title", "")
            snippet = result.get("body", "")
            results_text.append(f"Titre: {title}\nRésumé: {snippet}\n")

    return "\n---\n".join(results_text)

# if __name__ == "__main__":
#     print("Test du module de recherche pour 'Doctolib'...\n")
#     data = search_company_info("Doctolib")
#     print(data)