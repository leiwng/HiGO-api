# /app/models/pet.py
from pydantic import BaseModel, Field
from datetime import date

class VaccinationRecord(BaseModel):
    vaccine: str
    date: date

class MedicalHistory(BaseModel):
    date: date
    diagnosis: str

class PetInfo(BaseModel):
    pet_id: str = Field(..., description="宠物ID")
    name: str = Field(..., description="宠物名称")
    species: str = Field(..., description="物种 (e.g., 'canine', 'feline')")
    breed: str = Field(..., description="品种")
    age: int = Field(..., description="年龄")
    weight: float = Field(..., description="体重 (kg)")
    vaccination_records: list[VaccinationRecord] = Field([], description="疫苗记录")
    medical_history: list[MedicalHistory] = Field([], description="医疗历史")

class PetBreed(BaseModel):
    id: int
    name: str
    category: str
