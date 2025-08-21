"""
Authentication Schemas
"""

from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    """Token data schema"""
    username: Optional[str] = None

class UserLogin(BaseModel):
    """User login schema"""
    username: str
    password: str

class UserResponse(BaseModel):
    """User response schema"""
    username: str
    role: str
    permissions: list[str]