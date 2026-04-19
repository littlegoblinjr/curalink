import httpx
import json
from typing import List, Dict, Any

async def search_pubmed_metadata(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Fast search for titles and IDs only (High Recall)."""
    async with httpx.AsyncClient() as client:
        try:
            # Step A: Get IDs
            search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            search_params = {"db": "pubmed", "term": query, "retmax": limit, "retmode": "json"}
            resp = await client.get(search_url, params=search_params)
            
            if resp.status_code != 200: return []
            id_list = resp.json().get("esearchresult", {}).get("idlist", [])
            if not id_list: return []
            
            # Step B: Get Titles using esummary
            summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            summary_params = {"db": "pubmed", "id": ",".join(id_list), "retmode": "json"}
            summary_resp = await client.get(summary_url, params=summary_params)
            
            if summary_resp.status_code != 200: return []
            raw_data = summary_resp.json().get("result", {})
            
            titles = []
            for pmid in id_list:
                body = raw_data.get(pmid, {})
                titles.append({
                    "pmid": pmid,
                    "title": body.get("title", ""),
                    "date": body.get("pubdate", ""),
                    "source": "PubMed",
                    "summary": "" 
                })
            return titles
        except Exception as e:
            print(f"PubMed Metadata Search Error: {e}")
            return []

async def fetch_pubmed_abstracts(id_list: List[str]) -> List[Dict[str, Any]]:
    """Deep fetch for full abstracts of specific PMIDs (High Precision)."""
    if not id_list: return []
    async with httpx.AsyncClient() as client:
        try:
            url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            params = {"db": "pubmed", "id": ",".join(id_list), "retmode": "text", "rettype": "medline"}
            resp = await client.get(url, params=params)
            if resp.status_code != 200: return []
            return parse_medline(resp.text)
        except Exception as e:
            print(f"PubMed Abstract Fetch Error: {e}")
            return []

def parse_medline(text: str) -> List[Dict[str, Any]]:
    """Simple parser for MEDLINE text format to extract Title, Abstract, and PMCID."""
    articles = []
    current = {}
    for line in text.split("\n"):
        if line.startswith("PMID- "):
            if current: articles.append(current)
            current = {"pmid": line[6:].strip(), "title": "", "abstract": "", "date": "", "pmc": ""}
        elif line.startswith("TI  - "): current["title"] = line[6:].strip()
        elif line.startswith("AB  - "): current["abstract"] = line[6:].strip()
        elif line.startswith("DP  - "): current["date"] = line[6:].strip()
        elif line.startswith("PMC - "): current["pmc"] = line[6:].strip()
        elif line.startswith("AU  - "):
            if "authors" not in current: current["authors"] = []
            current["authors"].append(line[6:].strip())
        elif line.startswith("      ") and "abstract" in current and current["abstract"]:
            current["abstract"] += " " + line.strip()
            
    if current: articles.append(current)
    return articles

async def fetch_pmc_fulltext(pmc_id: str) -> str:
    """Fetches full text from PMC if available (Open Access)."""
    if not pmc_id: return ""
    async with httpx.AsyncClient() as client:
        try:
            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmc_id}&retmode=text&rettype=medline"
            resp = await client.get(url)
            if resp.status_code != 200: return ""
            return resp.text[:5000] 
        except Exception as e:
            print(f"PMC FullText Fetch Error: {e}")
            return ""

async def search_openalex(query: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetches broad academic results from OpenAlex."""
    async with httpx.AsyncClient() as client:
        try:
            url = "https://api.openalex.org/works"
            params = {"search": query, "per-page": limit, "sort": "relevance_score:desc"}
            resp = await client.get(url, params=params, timeout=15.0)
            if resp.status_code != 200: return []
            return resp.json().get("results", [])
        except Exception as e:
            print(f"OpenAlex Search Error: {e}")
            return []

async def search_clinical_trials(condition: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetches real-world trial data from ClinicalTrials.gov."""
    async with httpx.AsyncClient() as client:
        try:
            url = "https://clinicaltrials.gov/api/v2/studies"
            params = {
                "query.cond": condition,
                "pageSize": limit,
                "format": "json"
            }
            resp = await client.get(url, params=params, timeout=15.0)
            
            # CRITICAL: Check status code and content type
            if resp.status_code != 200:
                print(f"ClinicalTrials.gov API returned status {resp.status_code}")
                return []
            
            try:
                data = resp.json()
                return data.get("studies", [])
            except json.JSONDecodeError:
                print("ClinicalTrials.gov returned non-JSON content.")
                return []
        except Exception as e:
            print(f"ClinicalTrials.gov Search Error: {e}")
            return []
