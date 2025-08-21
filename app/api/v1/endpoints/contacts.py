"""
Contacts Management Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.contact import Contact
from app.schemas.contact import ContactResponse, ContactsStats, ContactFilter

router = APIRouter()

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