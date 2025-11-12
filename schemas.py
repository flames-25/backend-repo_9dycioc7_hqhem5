"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from datetime import datetime

# Core CRM Schemas

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    role: Literal["admin", "manager", "rep"] = Field("rep")
    team: Optional[str] = Field(None, description="Team or territory name")
    is_active: bool = Field(True)

class Account(BaseModel):
    name: str
    industry: Optional[str] = None
    size: Optional[str] = Field(None, description="Company size e.g., 11-50")
    region: Optional[str] = None
    tags: List[str] = []

class Contact(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    account_id: Optional[str] = Field(None, description="Linked Account _id")
    title: Optional[str] = None
    tags: List[str] = []

class Lead(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Literal["new", "contacted", "qualified", "lost"] = "new"
    source: Optional[str] = Field(None, description="Website, Campaign, Referral, etc.")
    owner_id: Optional[str] = Field(None, description="Assigned User _id")
    score: Optional[int] = Field(None, ge=0, le=100)
    notes: Optional[str] = None

class Deal(BaseModel):
    title: str
    account_id: Optional[str] = None
    contact_id: Optional[str] = None
    value: float = 0.0
    close_date: Optional[datetime] = None
    stage: str = Field("prospecting", description="Pipeline stage")
    probability: Optional[int] = Field(None, ge=0, le=100)
    lost_reason: Optional[str] = None
    owner_id: Optional[str] = None

class Task(BaseModel):
    type: Literal["call", "meeting", "follow-up", "email"] = "follow-up"
    title: str
    due_date: Optional[datetime] = None
    priority: Literal["low", "medium", "high"] = "medium"
    owner_id: Optional[str] = None
    related_type: Optional[Literal["lead", "contact", "deal", "account"]] = None
    related_id: Optional[str] = None
    notes: Optional[str] = None
    completed: bool = False

class Activity(BaseModel):
    subject: str
    type: Literal["note", "call", "email", "meeting", "status-change"] = "note"
    user_id: Optional[str] = None
    related_type: Optional[Literal["lead", "contact", "deal", "account"]] = None
    related_id: Optional[str] = None
    details: Optional[str] = None

# Example schemas (kept for reference)
class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
