"""
Dashboard Endpoints (sin autenticación para testing inicial)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from datetime import datetime, timedelta
import math

from app.core.database import get_db
from app.core.cache import dashboard_cache
from app.models.contact import Contact
from app.schemas.contact import (
    ContactResponse, PaginatedContactResponse, ContactStatsEnhanced
)

router = APIRouter()

@router.get("/test")
async def test_dashboard():
    """Test endpoint simple para verificar funcionamiento"""
    return {
        "status": "OK",
        "message": "Dashboard endpoints working",
        "timestamp": datetime.utcnow()
    }

@router.get("/test-db")
async def test_dashboard_db(db: AsyncSession = Depends(get_db)):
    """Test endpoint con conexión a DB"""
    try:
        # Query simple
        result = await db.execute(select(func.count(Contact.id)))
        count = result.scalar()

        return {
            "status": "OK",
            "total_contacts": count,
            "message": "Database connection working"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "message": "Database connection failed"
        }

@router.get("/contacts", response_model=PaginatedContactResponse)
async def get_dashboard_contacts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    search_query: Optional[str] = Query(None, description="Search in phone numbers"),
    state: Optional[str] = Query(None, description="Filter by state name"),
    municipality: Optional[str] = Query(None, description="Filter by municipality"),
    lada: Optional[str] = Query(None, description="Filter by LADA code"),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated contacts for dashboard (no auth for testing)"""

    # Build base query
    query = select(Contact).where(Contact.opt_out_at.is_(None))

    # Apply filters
    if search_query:
        query = query.where(
            or_(
                Contact.phone_national.ilike(f"%{search_query}%"),
                Contact.phone_e164.ilike(f"%{search_query}%"),
                Contact.full_name.ilike(f"%{search_query}%")
            )
        )

    if state:
        query = query.where(Contact.state_name.ilike(f"%{state}%"))

    if municipality:
        query = query.where(Contact.municipality.ilike(f"%{municipality}%"))

    if lada:
        query = query.where(Contact.lada == lada)

    # Get total count for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_contacts = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    paginated_query = query.offset(offset).limit(page_size).order_by(Contact.created_at.desc())

    result = await db.execute(paginated_query)
    contacts = result.scalars().all()

    # Calculate pagination info
    total_pages = math.ceil(total_contacts / page_size) if total_contacts > 0 else 1

    return PaginatedContactResponse(
        data=contacts,
        total=total_contacts,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get enhanced contacts statistics for dashboard (no auth for testing)"""

    # Check cache first
    cached_stats = await dashboard_cache.get_stats()
    if cached_stats:
        return cached_stats

    try:
        # Optimized single query for all counts
        counts_query = select(
            func.count(Contact.id).label("total"),
            func.count().filter(Contact.opt_out_at.is_(None)).label("active"),
            func.count().filter(Contact.is_mobile == True).label("mobile")
        )

        counts_result = await db.execute(counts_query)
        counts = counts_result.fetchone()

        total_contacts = counts.total or 0
        active_contacts = counts.active or 0
        mobile_contacts = counts.mobile or 0

        # Contacts by state (top 15 for charts)
        state_query = select(
            Contact.state_name,
            func.count(Contact.id).label("count")
        ).where(
            Contact.state_name.is_not(None)
        ).group_by(Contact.state_name).order_by(func.count(Contact.id).desc()).limit(15)

        state_result = await db.execute(state_query)
        contacts_by_state = {
            row.state_name: row.count
            for row in state_result.fetchall()
        }

        # Contacts by LADA (top 10 for charts)
        lada_query = select(
            Contact.lada,
            func.count(Contact.id).label("count")
        ).where(
            Contact.lada.is_not(None)
        ).group_by(Contact.lada).order_by(func.count(Contact.id).desc()).limit(10)

        lada_result = await db.execute(lada_query)
        contacts_by_lada = {
            row.lada: row.count
            for row in lada_result.fetchall()
        }

        # Recent extractions (placeholder)
        recent_extractions = 23

        # Calculate growth rate (mock)
        growth_rate = 12.3

        stats_data = {
            "total_contacts": total_contacts,
            "active_contacts": active_contacts,
            "mobile_contacts": mobile_contacts,
            "contacts_by_state": contacts_by_state,
            "contacts_by_lada": contacts_by_lada,
            "recent_extractions": recent_extractions,
            "growth_rate": growth_rate
        }

        # Cache the results
        await dashboard_cache.set_stats(stats_data)

        return stats_data

    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "message": "Stats calculation failed"
        }

@router.get("/states", response_model=List[str])
async def get_dashboard_states(
    db: AsyncSession = Depends(get_db)
):
    """Get list of available states (no auth for testing)"""
    query = select(Contact.state_name).distinct().where(
        Contact.state_name.is_not(None)
    ).order_by(Contact.state_name)

    result = await db.execute(query)
    states = [row.state_name for row in result.fetchall()]

    return states

@router.get("/ladas", response_model=List[str])
async def get_dashboard_ladas(
    db: AsyncSession = Depends(get_db)
):
    """Get list of available LADA codes (no auth for testing)"""
    query = select(Contact.lada).distinct().where(
        Contact.lada.is_not(None)
    ).order_by(Contact.lada)

    result = await db.execute(query)
    ladas = [row.lada for row in result.fetchall()]

    return ladas
