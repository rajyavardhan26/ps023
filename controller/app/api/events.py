from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from controller.app.database import get_db
from controller.app.models import VMEvent
from controller.app.schemas import VMEventResponse

router = APIRouter(prefix="/events", tags=["Audit Events"])

@router.get("", response_model=List[VMEventResponse])
def get_events(
    limit: int = Query(50, ge=1, le=200),
    vm_id: Optional[int] = None,
    node_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(VMEvent)
    if vm_id:
        query = query.filter(VMEvent.vm_id == vm_id)
    if node_id:
        query = query.filter(VMEvent.node_id == node_id)
    
    events = query.order_by(desc(VMEvent.timestamp)).limit(limit).all()
    return events
