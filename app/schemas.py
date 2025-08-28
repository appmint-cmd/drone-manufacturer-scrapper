
from pydantic import BaseModel

class DroneCompanyBase(BaseModel):
	name: str
	website: str | None = None
	email: str | None = None
	phone: str | None = None
	address: str | None = None

class DroneCompanyCreate(DroneCompanyBase):
	pass

class DroneCompany(DroneCompanyBase):
	id: int

	class Config:
		orm_mode = True
