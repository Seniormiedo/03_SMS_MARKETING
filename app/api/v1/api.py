"""
API v1 Router - Main API router that includes all endpoint modules
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, contacts, campaigns, health, dashboard

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
