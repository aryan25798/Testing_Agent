"""
Custom Agent Management API Endpoints.
Allows the user to build, configure, and manage specialized custom testing agents.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.models.entities import CustomAgent

router = APIRouter(prefix="/custom-agents", tags=["Custom Agents"])


class CustomAgentCreate(BaseModel):
    name: str
    description: str = ""
    category: str = "Specialized QA"
    system_instructions: str
    provider: str = "gemini"
    model_id: str = "gemini-2.5-flash"


class CustomAgentRead(BaseModel):
    id: str
    name: str
    description: str | None = None
    category: str
    system_instructions: str
    provider: str
    model_id: str
    is_active: bool
    created_at: str

    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=List[dict])
def list_custom_agents(db: Session = Depends(get_db)):
    agents = db.query(CustomAgent).filter(CustomAgent.is_active == True).order_by(CustomAgent.created_at.desc()).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "category": a.category,
            "system_instructions": a.system_instructions,
            "provider": a.provider,
            "model_id": a.model_id,
            "is_active": a.is_active,
            "created_at": a.created_at.isoformat() if a.created_at else "",
        }
        for a in agents
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_custom_agent(payload: CustomAgentCreate, db: Session = Depends(get_db)):
    agent = CustomAgent(
        name=payload.name,
        description=payload.description,
        category=payload.category,
        system_instructions=payload.system_instructions,
        provider=payload.provider,
        model_id=payload.model_id,
        is_active=True,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return {
        "status": "success",
        "id": agent.id,
        "name": agent.name,
        "category": agent.category,
    }


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(CustomAgent).filter(CustomAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db.delete(agent)
    db.commit()
    return None
