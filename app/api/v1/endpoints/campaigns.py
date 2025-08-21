"""
SMS Campaigns Management Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.campaign import Campaign
from app.schemas.campaign import CampaignResponse, CampaignCreate, CampaignStats

router = APIRouter()

@router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get campaigns list"""
    
    query = select(Campaign)
    
    if status:
        query = query.where(Campaign.status == status)
    
    query = query.offset(offset).limit(limit).order_by(Campaign.created_at.desc())
    
    result = await db.execute(query)
    campaigns = result.scalars().all()
    
    return campaigns

@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create new SMS campaign"""
    
    db_campaign = Campaign(
        name=campaign.name,
        message_template=campaign.message_template,
        target_states=campaign.target_states,
        target_ladas=campaign.target_ladas,
        target_cities=campaign.target_cities,
        scheduled_at=campaign.scheduled_at,
        max_recipients=campaign.max_recipients,
        send_rate_per_minute=campaign.send_rate_per_minute,
        status="DRAFT"
    )
    
    db.add(db_campaign)
    await db.commit()
    await db.refresh(db_campaign)
    
    return db_campaign

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get specific campaign"""
    
    query = select(Campaign).where(Campaign.id == campaign_id)
    result = await db.execute(query)
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return campaign

@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get campaign statistics"""
    
    # Verify campaign exists
    campaign_query = select(Campaign).where(Campaign.id == campaign_id)
    campaign_result = await db.execute(campaign_query)
    campaign = campaign_result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return CampaignStats(
        campaign_id=campaign_id,
        total_recipients=campaign.sent_count,
        delivered_count=campaign.delivered_count,
        failed_count=campaign.failed_count,
        pending_count=max(0, campaign.sent_count - campaign.delivered_count - campaign.failed_count),
        delivery_rate=campaign.delivered_count / campaign.sent_count * 100 if campaign.sent_count > 0 else 0
    )

@router.post("/{campaign_id}/start")
async def start_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Start campaign execution"""
    
    query = select(Campaign).where(Campaign.id == campaign_id)
    result = await db.execute(query)
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Campaign is not in DRAFT status")
    
    # Update campaign status
    campaign.status = "RUNNING"
    await db.commit()
    
    # TODO: Queue campaign for processing by Celery workers
    
    return {"message": "Campaign started successfully", "campaign_id": campaign_id}