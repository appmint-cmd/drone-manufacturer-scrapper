from fastapi import FastAPI, Depends, Query, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app import models, database, schemas, crud
from app.services.scraper import scrape_and_parse
import os
import re
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, unquote

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Drone Directory API")
models.Base.metadata.create_all(bind=database.engine)
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def is_url(text: str) -> bool:
    """Check if the input text looks like a URL"""
    return bool(re.match(r"https?://", text))

def clean_duckduckgo_url(url: str) -> str:
    """Extract clean URL from DuckDuckGo redirect URLs"""
    if "duckduckgo.com/l/" in url:
        try:
            # Parse the redirect URL
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # Look for the actual URL in query parameters
            if 'uddg' in query_params:
                actual_url = unquote(query_params['uddg'][0])
                return actual_url
            elif 'u' in query_params:
                actual_url = unquote(query_params['u'][0])
                return actual_url
        except Exception:
            pass
    
    return url

def search_company_website(company_name: str) -> str:
    """Search for company website using DuckDuckGo"""
    try:
        # Add drone-specific search terms to get more relevant results
        search_query = f"{company_name} drone UAV company official website"
        search_url = f"https://duckduckgo.com/html/?q={search_query.replace(' ', '+')}"
        resp = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Find first result link
        result = soup.find("a", class_="result__a")
        if result and result.get("href"):
            url = result["href"]
            # Clean the URL if it's a DuckDuckGo redirect
            clean_url = clean_duckduckgo_url(url)
            return clean_url
    except Exception as e:
        print(f"Error searching for company website: {e}")
    
    return ""

def company_exists(db: Session, website: str, name: str) -> bool:
    """Check if company already exists in database"""
    if website:
        existing = db.query(models.DroneCompany).filter(
            models.DroneCompany.website == website
        ).first()
        if existing:
            return True
    
    if name:
        existing = db.query(models.DroneCompany).filter(
            models.DroneCompany.name.ilike(f"%{name}%")
        ).first()
        if existing:
            return True
    
    return False

@app.get("/")
def read_root():
    return {"message": "Drone Directory API is running 🚀"}

@app.post("/ui/scrape")
def ui_scrape(request: Request, query: str = Form(...), db: Session = Depends(get_db)):
    """Handle scraping from UI - accepts both company names and URLs"""
    try:
        if is_url(query):
            # Direct URL provided
            url = query
            company_name = query
        else:
            # Company name provided - search for website
            company_name = query
            url = search_company_website(query)
            
            if not url:
                # If we can't find a website, show error
                return templates.TemplateResponse("dashboard.html", {
                    "request": request, 
                    "companies": db.query(models.DroneCompany).all(),
                    "error": f"Could not find website for company: {company_name}"
                })

        # Check if company already exists
        if company_exists(db, url, company_name):
            companies = db.query(models.DroneCompany).all()
            return templates.TemplateResponse("dashboard.html", {
                "request": request, 
                "companies": companies,
                "error": f"Company already exists in directory: {company_name}"
            })

        # Scrape the website
        scraped = scrape_and_parse(url)
        
        # Check if this is not a drone company
        if scraped.get("error") == "Not a drone company":
            companies = db.query(models.DroneCompany).all()
            return templates.TemplateResponse("dashboard.html", {
                "request": request, 
                "companies": companies,
                "error": f"Company '{company_name}' is not drone-related: {scraped.get('reason', 'Company does not operate in the drone industry')}"
            })
        
        # Check for warnings about non-drone companies
        if scraped.get("warning"):
            companies = db.query(models.DroneCompany).all()
            return templates.TemplateResponse("dashboard.html", {
                "request": request, 
                "companies": companies,
                "warning": f"Warning for '{company_name}': {scraped.get('warning')}. Please verify this is a drone company before adding."
            })
        
        if not scraped.get("name"):
            scraped["name"] = company_name
        
        if not scraped.get("website"):
            scraped["website"] = url

        # Save to database
        db_company = models.DroneCompany(
            name=scraped.get("name"),
            website=scraped.get("website"),
            email=", ".join(scraped.get("emails", [])),
            phone=", ".join(scraped.get("phones", [])),
            address=", ".join(scraped.get("addresses", [])),
            description=scraped.get("description"),
            category=scraped.get("category"),
        )
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        
        return RedirectResponse(url="/ui/?success=true", status_code=303)
        
    except Exception as e:
        # Handle any errors during scraping
        companies = db.query(models.DroneCompany).all()
        return templates.TemplateResponse("dashboard.html", {
            "request": request, 
            "companies": companies,
            "error": f"Error scraping: {str(e)}"
        })

@app.post("/scrape-ai", response_model=schemas.DroneCompany)
def scrape_with_ai(query: str = Form(...), db: Session = Depends(get_db)):
    """API endpoint for scraping - accepts both company names and URLs"""
    if is_url(query):
        url = query
    else:
        url = search_company_website(query)
        if not url:
            raise HTTPException(status_code=400, detail=f"Could not find website for company: {query}")
    
    # Check if company already exists
    if company_exists(db, url, query):
        raise HTTPException(status_code=409, detail="Company already exists in directory")
    
    scraped = scrape_and_parse(url)
    
    # Check if this is not a drone company
    if scraped.get("error") == "Not a drone company":
        raise HTTPException(status_code=400, detail=f"Company is not drone-related: {scraped.get('reason', 'Company does not operate in the drone industry')}")
    
    # Check for warnings about non-drone companies
    if scraped.get("warning"):
        raise HTTPException(status_code=400, detail=f"Warning: {scraped.get('warning')}. Please verify this is a drone company.")
    
    # Save to DB
    db_company = models.DroneCompany(
        name=scraped.get("name"),
        website=scraped.get("website"),
        email=", ".join(scraped.get("emails", [])),
        phone=", ".join(scraped.get("phones", [])),
        address=", ".join(scraped.get("addresses", [])),
        description=scraped.get("description"),
        category=scraped.get("category"),
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

@app.get("/search", response_class=HTMLResponse)
def search_companies(request: Request, query: str = "", db: Session = Depends(get_db)):
    q = f"%{query}%"
    results = db.query(models.DroneCompany).filter(
        models.DroneCompany.name.ilike(q) |
        models.DroneCompany.category.ilike(q) |
        models.DroneCompany.email.ilike(q) |
        models.DroneCompany.phone.ilike(q) |
        models.DroneCompany.description.ilike(q)
    ).all()
    return templates.TemplateResponse("search.html", {"request": request, "results": results, "query": query})

@app.get("/ui/", response_class=HTMLResponse)
def ui_dashboard(request: Request, db: Session = Depends(get_db)):
    companies = db.query(models.DroneCompany).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "companies": companies})

@app.post("/companies/", response_model=schemas.DroneCompany)
def create_company(company: schemas.DroneCompanyCreate, db: Session = Depends(get_db)):
    return crud.create_company(db=db, company=company)

@app.get("/companies/", response_model=list[schemas.DroneCompany])
def list_companies(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_companies(db=db, skip=skip, limit=limit)

@app.post("/cleanup-duplicates")
def cleanup_duplicates(db: Session = Depends(get_db)):
    """Clean up duplicate entries in the database"""
    try:
        # Get all companies
        companies = db.query(models.DroneCompany).all()
        cleaned_count = 0
        
        # Group by website (most reliable identifier)
        website_groups = {}
        for company in companies:
            if company.website:
                clean_website = clean_duckduckgo_url(company.website)
                if clean_website not in website_groups:
                    website_groups[clean_website] = []
                website_groups[clean_website].append(company)
        
        # Remove duplicates, keeping the one with most complete data
        for website, company_list in website_groups.items():
            if len(company_list) > 1:
                # Keep the company with most complete data
                best_company = max(company_list, key=lambda c: sum([
                    1 if c.name else 0,
                    1 if c.email else 0,
                    1 if c.phone else 0,
                    1 if c.description else 0,
                    1 if c.category else 0
                ]))
                
                # Update the best company's website to clean version
                if website != best_company.website:
                    best_company.website = website
                
                # Delete duplicates
                for company in company_list:
                    if company.id != best_company.id:
                        db.delete(company)
                        cleaned_count += 1
        
        # Also clean up individual company websites
        for company in companies:
            if company.website and "duckduckgo.com" in company.website:
                clean_website = clean_duckduckgo_url(company.website)
                if clean_website != company.website:
                    company.website = clean_website
        
        db.commit()
        
        return {
            "message": f"Cleanup completed. Removed {cleaned_count} duplicate entries and cleaned {len(companies)} URLs.",
            "cleaned_duplicates": cleaned_count,
            "total_companies": len(companies)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")
