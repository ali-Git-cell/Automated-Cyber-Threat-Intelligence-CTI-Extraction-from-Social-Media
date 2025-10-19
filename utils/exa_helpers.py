from exa_py import Exa
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def get_exa_client():
    exa_api_key = os.getenv("EXA_API_KEY")
    if not exa_api_key:
        raise ValueError("EXA_API_KEY not found. Please check your .env file.")
    
    exa_client = Exa(api_key = exa_api_key)
    print("✅ Exa client initialized.")
    return exa_client

def search_cyber_threats(query: str):
    exa_client = get_exa_client()
    result = exa_client.search_and_contents(query, summary = True)

    items = []
    for idx, item in enumerate(result.results[:5]):
        summary_text = item.summary or "No summary available."
        if len(summary_text) > 1000:
            summary_text = summary_text[:1000] + "..."

        items.append(
            f"{idx+1}. Title: {item.title}. "
            f"URL: {item.url}. "
            f"Date: {item.published_date}. "
            f"Summary: {summary_text}."
        )

    return " ".join(items)
        
        
        
def cross_validate_with_exa(messages, top_n=10):
    """
    Cross-check a list of CTI messages with Exa.ai.
    Returns a list of dicts: {message, status, exa_results}.
    """
    validated = []
    for msg in messages[:top_n]:
        query = msg[:200]  # trim long Telegram text for searching
        exa_results = search_cyber_threats(query)

        if exa_results and len(exa_results) > 0:
            status = "Confirmed"
        else:
            status = "Emerging"

        if exa_results.strip():
            validated.append({
                "message": msg,
                "status": "Known Threat",
                "exa_results": exa_results
            })
        else:
            validated.append({
                "message": msg,
                "status": "Early Signal",
                "exa_results": "No external validation found"
            })
    return validated