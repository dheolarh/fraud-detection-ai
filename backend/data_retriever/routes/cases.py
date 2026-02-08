"""
Cases API Routes
Endpoints for case management including transaction selection and resolve/reopen
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import json
import random
import string

from storage.database import get_db
from storage.models import Case
from clients.banking_client import get_banking_client

router = APIRouter(prefix="/api/cases", tags=["cases"])


# Schemas
class TransactionReference(BaseModel):
    id: str
    type: str  # "transaction" or "login"


class CaseCreate(BaseModel):
    title: str
    description: str
    priority: str
    affected_transactions: List[TransactionReference] = []


def generate_case_id():
    """Generate a unique case ID"""
    return f"CASE-{''.join(random.choices(string.digits, k=6))}"


@router.get("/available-transactions/{user_id}")
async def get_available_transactions(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all available transactions and anomalies for selection.
    
    Returns a unified list of:
    - Transactions from banking backend
    - Fraud alerts (transaction anomalies)
    - Suspicious logins (login anomalies)
    """
    try:
        import httpx
        
        # Fetch transactions from banking backend
        async with httpx.AsyncClient() as client:
            # Get transactions
            txn_response = await client.get(
                f"http://localhost:8001/api/transactions",
                params={"user_id": user_id, "limit": 5000},  # Banking backend max limit
                timeout=10.0
            )
            if txn_response.status_code == 200:
                response_data = txn_response.json()
                transactions = response_data.get('transactions', [])
            else:
                transactions = []
            
            # Get fraud alerts
            fraud_response = await client.get(
                f"http://localhost:8000/api/fraud/alerts/{user_id}",
                timeout=10.0
            )
            fraud_alerts = fraud_response.json() if fraud_response.status_code == 200 else []
            
            # Get suspicious logins
            login_response = await client.get(
                f"http://localhost:8000/api/suspicious-logins/{user_id}",
                timeout=10.0
            )
            suspicious_logins = login_response.json() if login_response.status_code == 200 else []
        
        # Format all items for selection
        available_items = []
        
        # Add transactions
        for txn in transactions:
            available_items.append({
                "id": txn.get('transaction_id'),
                "type": "transaction",
                "display_type": "Transaction",
                "amount": txn.get('amount'),
                "currency": txn.get('currency') or txn.get('bank_currency'),
                "location": txn.get('location'),
                "timestamp": txn.get('timestamp'),
                "status": txn.get('status'),
                "risk_score": None
            })
        
        # Add fraud alerts
        for alert in fraud_alerts:
            available_items.append({
                "id": alert.get('transaction_id'),
                "type": "transaction",
                "display_type": "Fraud Alert",
                "amount": alert.get('amount'),
                "currency": None,
                "location": alert.get('location'),
                "timestamp": alert.get('timestamp'),
                "status": alert.get('verdict'),
                "risk_score": alert.get('risk_score') or alert.get('final_risk_score')
            })
        
        # Add suspicious logins
        for login in suspicious_logins:
            available_items.append({
                "id": login.get('id'),
                "type": "login",
                "display_type": "Login Anomaly",
                "amount": None,
                "currency": None,
                "location": login.get('location'),
                "timestamp": login.get('timestamp'),
                "status": login.get('verdict'),
                "risk_score": login.get('risk_score')
            })
        
        # Remove duplicates by ID
        seen_ids = set()
        unique_items = []
        for item in available_items:
            if item['id'] not in seen_ids:
                seen_ids.add(item['id'])
                unique_items.append(item)
        
        # Sort by timestamp (most recent first)
        unique_items.sort(
            key=lambda x: x.get('timestamp', '') or '',
            reverse=True
        )
        
        return unique_items
        
    except Exception as e:
        print(f"Error in get_available_transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching available transactions: {str(e)}")


@router.post("")
async def create_case(
    case_data: CaseCreate,
    db: Session = Depends(get_db)
):
    """Create a new case with affected transactions."""
    try:
        new_case = Case(
            case_id=generate_case_id(),
            title=case_data.title,
            description=case_data.description,
            priority=case_data.priority,
            status="open",
            affected_transactions=json.dumps([t.dict() for t in case_data.affected_transactions]),
            created_at=datetime.utcnow()
        )
        
        db.add(new_case)
        db.commit()
        db.refresh(new_case)
        
        return {
            "case_id": new_case.case_id,
            "title": new_case.title,
            "description": new_case.description,
            "priority": new_case.priority,
            "status": new_case.status,
            "affected_transactions": json.loads(new_case.affected_transactions) if new_case.affected_transactions else [],
            "created_at": new_case.created_at.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating case: {str(e)}")


@router.put("/{case_id}")
async def update_case(
    case_id: str,
    case_update: CaseCreate,
    db: Session = Depends(get_db)
):
    """
    Update an existing case
    """
    try:
        # Find the case
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Update fields
        case.title = case_update.title
        case.description = case_update.description
        case.priority = case_update.priority
        case.affected_transactions = json.dumps([
            {"id": t.id, "type": t.type} for t in case_update.affected_transactions
        ])
        
        db.commit()
        db.refresh(case)
        
        return {
            "case_id": case.case_id,
            "title": case.title,
            "description": case.description,
            "priority": case.priority,
            "status": case.status,
            "affected_transactions": json.loads(case.affected_transactions) if case.affected_transactions else [],
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating case: {str(e)}")


@router.put("/{case_id}/resolve")
async def resolve_case(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Resolve a case.
    - Updates status to 'resolved'
    - Sets resolved_at timestamp
    - Anomalies attached to this case will be filtered out from anomaly table
    """
    try:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        
        if not case:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        case.status = "resolved"
        case.resolved_at = datetime.utcnow()
        
        db.commit()
        db.refresh(case)
        
        return {
            "case_id": case.case_id,
            "title": case.title,
            "status": case.status,
            "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None,
            "affected_transactions": json.loads(case.affected_transactions) if case.affected_transactions else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resolving case: {str(e)}")


@router.put("/{case_id}/reopen")
async def reopen_case(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Reopen a resolved case.
    - Updates status to 'open'
    - Clears resolved_at timestamp
    - Anomalies attached to this case will reappear in anomaly table
    """
    try:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        
        if not case:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        case.status = "open"
        case.resolved_at = None
        
        db.commit()
        db.refresh(case)
        
        return {
            "case_id": case.case_id,
            "title": case.title,
            "status": case.status,
            "resolved_at": None,
            "affected_transactions": json.loads(case.affected_transactions) if case.affected_transactions else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error reopening case: {str(e)}")


@router.get("")
async def get_all_cases(
    status: Optional[str] = Query(None, description="Filter by status: open, resolved, or all"),
    db: Session = Depends(get_db)
):
    """Get all cases, optionally filtered by status."""
    try:
        query = db.query(Case)
        
        if status and status != "all":
            query = query.filter(Case.status == status)
        
        cases = query.order_by(Case.created_at.desc()).all()
        
        return [
            {
                "case_id": case.case_id,
                "title": case.title,
                "description": case.description,
                "priority": case.priority,
                "status": case.status,
                "affected_transactions": json.loads(case.affected_transactions) if case.affected_transactions else [],
                "created_at": case.created_at.isoformat(),
                "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None
            }
            for case in cases
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cases: {str(e)}")
