"""
Contacts Management Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta
import math

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.contact import Contact
from app.schemas.contact import (
    ContactResponse, ContactsStats, ContactFilter,
    PaginatedContactResponse, ContactStatsEnhanced, ContactFilters
)

router = APIRouter()

@router.get("/", response_model=PaginatedContactResponse)
async def get_contacts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    search_query: Optional[str] = Query(None, description="Search in phone numbers"),
    state: Optional[str] = Query(None, description="Filter by state name"),
    municipality: Optional[str] = Query(None, description="Filter by municipality"),
    lada: Optional[str] = Query(None, description="Filter by LADA code"),
    date_start: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    date_end: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get paginated contacts with filters"""

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

    if date_start:
        start_date = datetime.strptime(date_start, "%Y-%m-%d")
        query = query.where(Contact.created_at >= start_date)

    if date_end:
        end_date = datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1)
        query = query.where(Contact.created_at < end_date)

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

@router.get("/stats", response_model=ContactsStats)
async def get_contacts_stats(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get contacts statistics"""

    # Total contacts
    total_query = select(func.count(Contact.id))
    total_result = await db.execute(total_query)
    total_contacts = total_result.scalar()

    # Active contacts
    active_query = select(func.count(Contact.id)).where(
        and_(Contact.status == "ACTIVE", Contact.opt_out_at.is_(None))
    )
    active_result = await db.execute(active_query)
    active_contacts = active_result.scalar()

    # Mobile contacts
    mobile_query = select(func.count(Contact.id)).where(Contact.is_mobile == True)
    mobile_result = await db.execute(mobile_query)
    mobile_contacts = mobile_result.scalar()

    # By state
    state_query = select(
        Contact.state_code,
        Contact.state_name,
        func.count(Contact.id).label("count")
    ).group_by(Contact.state_code, Contact.state_name).order_by(func.count(Contact.id).desc()).limit(10)

    state_result = await db.execute(state_query)
    top_states = [
        {"state_code": row.state_code, "state_name": row.state_name, "count": row.count}
        for row in state_result
    ]

    return ContactsStats(
        total_contacts=total_contacts or 0,
        active_contacts=active_contacts or 0,
        mobile_contacts=mobile_contacts or 0,
        opt_out_contacts=total_contacts - active_contacts if total_contacts and active_contacts else 0,
        top_states=top_states
    )

@router.get("/stats-enhanced", response_model=ContactStatsEnhanced)
async def get_contacts_stats_enhanced(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get enhanced contacts statistics for dashboard"""

    # Total contacts
    total_query = select(func.count(Contact.id))
    total_result = await db.execute(total_query)
    total_contacts = total_result.scalar() or 0

    # Active contacts (not opted out)
    active_query = select(func.count(Contact.id)).where(Contact.opt_out_at.is_(None))
    active_result = await db.execute(active_query)
    active_contacts = active_result.scalar() or 0

    # Mobile contacts
    mobile_query = select(func.count(Contact.id)).where(Contact.is_mobile == True)
    mobile_result = await db.execute(mobile_query)
    mobile_contacts = mobile_result.scalar() or 0

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

    # Recent extractions (placeholder - will be real in Phase 2)
    recent_extractions = 23  # Mock data for now

    # Calculate growth rate (mock for now)
    growth_rate = 12.3

    return ContactStatsEnhanced(
        total_contacts=total_contacts,
        active_contacts=active_contacts,
        mobile_contacts=mobile_contacts,
        contacts_by_state=contacts_by_state,
        contacts_by_lada=contacts_by_lada,
        recent_extractions=recent_extractions,
        growth_rate=growth_rate
    )

@router.get("/search")
async def search_contacts(
    q: Optional[str] = Query(None, description="Search query"),
    state_code: Optional[str] = Query(None, description="Filter by state code"),
    lada: Optional[str] = Query(None, description="Filter by LADA"),
    status: Optional[str] = Query("ACTIVE", description="Filter by status"),
    limit: int = Query(100, le=1000, description="Limit results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Search contacts with filters"""

    query = select(Contact)

    # Apply filters
    if status:
        query = query.where(Contact.status == status)

    if state_code:
        query = query.where(Contact.state_code == state_code)

    if lada:
        query = query.where(Contact.lada == lada)

    if q:
        query = query.where(
            Contact.full_name.ilike(f"%{q}%") |
            Contact.phone_national.ilike(f"%{q}%")
        )

    # Always exclude opted out contacts unless specifically requested
    if status != "OPTED_OUT":
        query = query.where(Contact.opt_out_at.is_(None))

    # Apply pagination
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    contacts = result.scalars().all()

    return {
        "contacts": contacts,
        "total": len(contacts),
        "offset": offset,
        "limit": limit
    }

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get specific contact by ID"""

    query = select(Contact).where(Contact.id == contact_id)
    result = await db.execute(query)
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return contact

@router.get("/states", response_model=List[str])
async def get_states(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get list of available states"""
    query = select(Contact.state_name).distinct().where(
        Contact.state_name.is_not(None)
    ).order_by(Contact.state_name)

    result = await db.execute(query)
    states = [row.state_name for row in result.fetchall()]

    return states

@router.get("/municipalities", response_model=List[str])
async def get_municipalities(
    state: Optional[str] = Query(None, description="Filter by state"),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get list of municipalities, optionally filtered by state"""
    query = select(Contact.municipality).distinct().where(
        Contact.municipality.is_not(None)
    )

    if state:
        query = query.where(Contact.state_name.ilike(f"%{state}%"))

    query = query.order_by(Contact.municipality)

    result = await db.execute(query)
    municipalities = [row.municipality for row in result.fetchall()]

    return municipalities

@router.get("/ladas", response_model=List[str])
async def get_ladas(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get list of available LADA codes"""
    query = select(Contact.lada).distinct().where(
        Contact.lada.is_not(None)
    ).order_by(Contact.lada)

    result = await db.execute(query)
    ladas = [row.lada for row in result.fetchall()]

    return ladas
