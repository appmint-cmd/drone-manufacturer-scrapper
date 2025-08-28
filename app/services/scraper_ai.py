import re
import json

def extract_json_from_response(text: str) -> dict:
    """
    Extract JSON object from AI response, ignoring extra commentary.
    """
    try:
        # Try direct parse first
        return json.loads(text)
    except:
        pass

    # Remove code fences if present
    text = re.sub(r"^```json|```$", "", text.strip(), flags=re.MULTILINE)

    # Find JSON block using regex
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # Fallback: return as raw text
    return {"raw_text": text}
import re
import requests
from bs4 import BeautifulSoup

def fetch_with_contact_page(url: str) -> str:
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract homepage text
        main_text = soup.get_text(" ", strip=True)

        # Look for contact/about/support/reach link
        contact_link = None
        for a in soup.find_all("a", href=True):
            if re.search(r"(contact|about|support|reach)", a.get_text().lower()):
                contact_link = a["href"]
                break

        extra_text = ""
        if contact_link:
            if not contact_link.startswith("http"):
                contact_link = url.rstrip("/") + "/" + contact_link.lstrip("/")
            try:
                r2 = requests.get(contact_link, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                r2.raise_for_status()
                extra_text = BeautifulSoup(r2.text, "html.parser").get_text(" ", strip=True)
            except Exception:
                pass

        return main_text + "\n\n" + extra_text
    except Exception as e:
        return ""
