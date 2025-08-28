
from app.services.ai_parser import parse_company_info
from app.services.scraper_ai import fetch_with_contact_page

def scrape_and_parse(url: str) -> dict:
    raw_text = fetch_with_contact_page(url)
    return parse_company_info(raw_text)
