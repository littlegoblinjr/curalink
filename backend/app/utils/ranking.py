from typing import List, Dict, Any
import re
from datetime import datetime

def normalize_results(raw_data: List[Dict[str, Any]], source: str) -> List[Dict[str, Any]]:
    """
    Standardizes data from different APIs into a unified format.
    Ensures every object has: title, summary, source, date, and url.
    """
    normalized = []
    
    if source == "pubmed":
        for article in raw_data:
            normalized.append({
                "title": article.get("title", ""),
                "summary": article.get("abstract", ""), 
                "authors": ", ".join(article.get("authors", [])),
                "source": "PubMed",
                "date": article.get("date", ""),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{article.get('pmid')}/",
                "pmc": article.get("pmc", ""),
                "score": 0
            })
            
    elif source == "openalex":
        for work in raw_data:
            authors = [a.get("author", {}).get("display_name", "") for a in work.get("authorships", [])]
            normalized.append({
                "title": work.get("display_name", ""),
                "summary": work.get("abstract_inverted_index", {}),
                "authors": ", ".join(authors),
                "source": "OpenAlex",
                "date": work.get("publication_date", ""),
                "url": work.get("doi") or work.get("id"),
                "score": 0
            })
            
    elif source == "clinical_trials":
        for study in raw_data:
            info = study.get("protocolSection", {})
            ident = info.get("identificationModule", {})
            status = info.get("statusModule", {})
            elig = info.get("eligibilityModule", {})
            locs = info.get("contactsLocationsModule", {})
            
            normalized.append({
                "title": ident.get("officialTitle") or ident.get("briefTitle", ""),
                "summary": info.get("descriptionModule", {}).get("briefSummary", ""),
                "source": "ClinicalTrials.gov",
                "date": status.get("startDateStruct", {}).get("date", ""),
                "url": f"https://clinicaltrials.gov/study/{ident.get('nctId')}",
                "status": status.get("overallStatus", "Unknown"),
                "eligibility": elig.get("eligibilityCriteria", "Not specified"),
                "location": locs.get("locations", [{}])[0].get("facility", "N/A"),
                "contact": locs.get("centralContacts", [{}])[0].get("email", "N/A"),
                "score": 0
            })
            
    return normalized

def rank_and_filter(results: List[Dict[str, Any]], query: str, disease: str, top_n: int = 8) -> List[Dict[str, Any]]:
    """
    Ranks the normalized results based on keyword overlap in the title 
    and applies a recency boost.
    """
    query_words = set(re.findall(r'\w+', query.lower()))
    # Match the base name of the disease (remove 's or disease suffixes)
    base_disease = re.sub(r"('s|disease|disorder)$", "", disease.strip(), flags=re.IGNORECASE).strip()
    disease_pattern = re.compile(rf"\b{re.escape(base_disease)}\b", re.IGNORECASE)
    
    # Extract "Core Intent" keywords
    intent_keywords = [w for w in query_words if w not in set(re.findall(r'\w+', base_disease.lower()))]
    
    for item in results:
        title_text = item['title'].lower()
        summary_text = str(item.get('summary', '')).lower()
        
        # 1. Condition Filter
        if disease_pattern.search(title_text):
            item['score'] += 30 
        elif disease_pattern.search(summary_text):
            item['score'] += 10
            
        # 2. INTENT MATCHING (Crucial for Precision)
        intent_title_matches = [w for w in intent_keywords if w in title_text]
        intent_summary_matches = [w for w in intent_keywords if w in summary_text]
        
        item['score'] += (len(intent_title_matches) * 25) 
        item['score'] += (len(intent_summary_matches) * 5)
        
        # Hard Penalty: If NONE of the intent keywords are in the paper, it's irrelevant filler
        if intent_keywords and not intent_title_matches and not intent_summary_matches:
            item['score'] -= 60

        # 2.5 GEOGRAPHIC MATCH (The Toronto Boost)
        # If a study mentions the user's city in the facility or description, boost it.
        if item.get('location') and any(word.lower() in item['location'].lower() for word in query_words):
             item['score'] += 40
        elif any(word.lower() in summary_text for word in query_words) and any(word.lower() in summary_text for word in re.findall(r'\w+', str(item.get('location', '')))):
             item['score'] += 20

        # 3. Recency Boost
        current_year = datetime.now().year
        item_year = re.search(r'\d{4}', str(item['date']))
        if item_year:
            year_val = int(item_year.group())
            if year_val == current_year:
                item['score'] += 5
            elif year_val >= current_year - 2:
                item['score'] += 3
            elif year_val >= current_year - 5:
                item['score'] += 1  # Relevant era bonus
            
    # Sort by score descending - allow all results so the AI can judge
    ranked = sorted(results, key=lambda x: x['score'], reverse=True)
    
    return ranked[:top_n]
