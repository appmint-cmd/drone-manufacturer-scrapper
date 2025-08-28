
from sqlalchemy.orm import Session
from app import models, schemas

def create_company(db: Session, company: schemas.DroneCompanyCreate):
	db_company = models.DroneCompany(**company.dict())
	db.add(db_company)
	db.commit()
	db.refresh(db_company)
	return db_company

def get_companies(db: Session, skip: int = 0, limit: int = 10):
	return db.query(models.DroneCompany).offset(skip).limit(limit).all()
