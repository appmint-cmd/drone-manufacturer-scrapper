import logging
import re
import time

import os
import google.generativeai as genai
from app.services.scraper_ai import extract_json_from_response
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logging.error("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")
    raise ValueError("GEMINI_API_KEY environment variable is required")

genai.configure(api_key=api_key)

def parse_company_info(raw_text: str) -> dict:
    """
    Use Gemini to parse company details from raw text.
    """
    prompt = f"""
    You are an AI that extracts structured company directory data EXCLUSIVELY for a drone industry database.
    
    IMPORTANT: Only process companies that are DIRECTLY related to drones, UAVs, or aerial robotics. 
    This includes:
    - Drone manufacturers and suppliers
    - Drone service providers (aerial photography, surveying, delivery)
    - Drone software and technology companies
    - Drone training and certification centers
    - Drone parts and accessories manufacturers
    - Aerial robotics companies
    
    DO NOT process companies from other industries like hotels, restaurants, retail, etc.
    
    From the following webpage text, extract ONLY if it's a drone-related company:
    - name
    - website
    - emails (list)
    - phones (list)
    - addresses (list)
    - description (2-3 sentence summary of what the company does)
    - category (MUST be one of: Drone Manufacturer, Drone Services, Drone Software, Drone Training, Drone Parts, Aerial Robotics, or similar drone-specific category)
    - company_type (Manufacturer, Services, Software, Training, Parts, Robotics)
    - region (India, USA, Europe, etc.)
    
    If the company is NOT drone-related, return: {{"error": "Not a drone company", "reason": "Company does not operate in the drone industry"}}
    
    Return JSON only. If any field is missing, return null.

    Text:
    {raw_text}
    """

    logger = logging.getLogger("ai_parser")
    start_time = time.time()
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        elapsed = time.time() - start_time
        logger.info(f"Gemini response time: {elapsed:.2f}s")
        text = response.text.strip()
        # Remove code fences and markdown
        text = re.sub(r"^```json|```$", "", text, flags=re.MULTILINE).strip()
        # Find JSON block using regex
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            json_str = match.group(0)
        else:
            json_str = text
        import json
        try:
            result = json.loads(json_str)
        except Exception:
            # Fallback: try to extract with regex
            logger.error(f"JSON parsing failed, fallback to regex cleanup. Raw: {text}")
            result = extract_json_from_response(text)
        
        # Check if this is not a drone company
        if result.get("error") == "Not a drone company":
            logger.warning(f"Non-drone company detected: {result.get('reason', 'Unknown')}")
            return result
        
        # Validate that this is a drone company
        if not is_drone_company(result):
            logger.warning(f"Company validation failed - may not be drone-related: {result.get('name', 'Unknown')}")
            result["warning"] = "Company may not be drone-related - please verify"
        
        # Normalize and clean up fields
        def normalize_email(val, fallback=None):
            emails = []
            if isinstance(val, list):
                emails.extend([v for v in val if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v)])
            elif isinstance(val, str):
                emails.extend([v for v in re.findall(r"[\w\.-]+@[\w\.-]+", val) if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v)])
            if fallback:
                if isinstance(fallback, list):
                    emails.extend([v for v in fallback if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v)])
                elif isinstance(fallback, str):
                    emails.extend([v for v in re.findall(r"[\w\.-]+@[\w\.-]+", fallback) if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v)])
            return list(set(emails))
        def normalize_phone(val, fallback=None):
            phones = []
            if isinstance(val, list):
                phones.extend([re.sub(r"\D", "", v) for v in val if re.sub(r"\D", "", v)])
            elif isinstance(val, str):
                phones.extend([re.sub(r"\D", "", v) for v in re.findall(r"[+]?\d[\d\s\-()]+", val)])
            if fallback:
                if isinstance(fallback, list):
                    phones.extend([re.sub(r"\D", "", v) for v in fallback if re.sub(r"\D", "", v)])
                elif isinstance(fallback, str):
                    emails.extend([v for v in re.findall(r"[\w\.-]+@[\w\.-]+", fallback) if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v)])
            return list(set(phones))
        def normalize_address(val, fallback=None):
            addresses = []
            if isinstance(val, list):
                addresses.extend([v.strip().replace("\n", " ") for v in val if v.strip()])
            elif isinstance(val, str):
                addresses.extend([v.strip().replace("\n", " ") for v in re.split(r"\*|\n|,", val) if v.strip()])
            if fallback:
                if isinstance(fallback, list):
                    addresses.extend([v.strip().replace("\n", " ") for v in fallback if v.strip()])
                elif isinstance(fallback, str):
                    addresses.extend([v.strip().replace("\n", " ") for v in re.split(r"\*|\n|,", fallback) if v.strip()])
            return list(set(addresses))
        result["emails"] = normalize_email(result.get("emails", None), result.get("email", None))
        result["phones"] = normalize_phone(result.get("phones", None), result.get("phone", None))
        result["addresses"] = normalize_address(result.get("addresses", None), result.get("address", None))
        # Remove old single-value fields
        result.pop("email", None)
        result.pop("phone", None)
        result.pop("address", None)
        # Log success
        logger.info(f"Scrape success for input. Result: {result}")
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Gemini error: {str(e)} | Time: {elapsed:.2f}s")
        # Handle Gemini quota, timeout, or internal errors
        error_msg = str(e)
        if "429" in error_msg:
            return {"error": "Gemini API quota exceeded", "details": error_msg}
        if "500" in error_msg:
            return {"error": "Gemini internal error", "details": error_msg}
        return {
            "error": error_msg,
            "raw_response": getattr(locals().get('response', None), 'text', None)
        }

def is_drone_company(result: dict) -> bool:
    """Validate if the company is drone-related"""
    # Check category
    category = result.get("category", "").lower()
    drone_keywords = [
        "drone", "uav", "uavs", "quadcopter", "multirotor", "aerial", "robotics",
        "unmanned", "autonomous", "flight", "aviation", "helicopter", "aircraft"
    ]
    
    if any(keyword in category for keyword in drone_keywords):
        return True
    
    # Check description
    description = result.get("description", "").lower()
    if any(keyword in description for keyword in drone_keywords):
        return True
    
    # Check company name
    name = result.get("name", "").lower()
    if any(keyword in name for keyword in drone_keywords):
        return True
    
    return False
