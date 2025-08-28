
from sqlalchemy import Column, Integer, String
from app.database import Base

class DroneCompany(Base):
	__tablename__ = "drone_companies"

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String, index=True, nullable=False)
	website = Column(String, nullable=True)
	email = Column(String, nullable=True)
	phone = Column(String, nullable=True)
	address = Column(String, nullable=True)
	category = Column(String, nullable=True)
	description = Column(String, nullable=True)
