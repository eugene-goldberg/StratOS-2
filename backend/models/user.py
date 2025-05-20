from pydantic import BaseModel, Field, EmailStr
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None

class UserCreate(UserBase):
    """Model for user registration"""
    password: str

class UserUpdate(BaseModel):
    """Model for updating user information"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    password: Optional[str] = None

class UserInDB(UserBase):
    """Internal user model for database operations"""
    id: UUID = Field(default_factory=uuid4)
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Data extracted from token"""
    user_id: Optional[UUID] = None
    email: Optional[str] = None

class UserResponse(UserBase):
    """User model returned to clients"""
    id: UUID
    is_active: bool
    created_at: datetime