"""Workflow automation API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.workflows import (
    WorkflowRead,
    WorkflowTemplate,
    CreateWorkflowRequest,
    WorkflowExecution,
    WorkflowStats,
    AutomationRule,
)
from app.schemas.users import UserRead
from app.services.workflow_service import WorkflowService


router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


@router.get("/", response_model=List[WorkflowRead])
async def get_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get all workflows for the studio."""
    service = WorkflowService(db)
    return await service.get_studio_workflows(
        current_user.studio_id, skip, limit, active_only
    )


@router.get("/templates", response_model=List[WorkflowTemplate])
async def get_workflow_templates(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get available workflow templates."""
    service = WorkflowService(db)
    return await service.get_workflow_templates(category)


@router.get("/stats", response_model=WorkflowStats)
async def get_workflow_stats(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get workflow execution statistics."""
    service = WorkflowService(db)
    return await service.get_workflow_stats(current_user.studio_id)


@router.post("/", response_model=WorkflowRead)
async def create_workflow(
    request: CreateWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Create a new workflow."""
    service = WorkflowService(db)
    return await service.create_workflow(current_user.studio_id, request)


@router.get("/{workflow_id}", response_model=WorkflowRead)
async def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get a specific workflow."""
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id)
    
    if not workflow or workflow.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found"
        )
    
    return workflow


@router.put("/{workflow_id}/activate")
async def activate_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Activate a workflow."""
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id)
    
    if not workflow or workflow.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found"
        )
    
    await service.activate_workflow(workflow_id)
    return {"message": "Workflow activated"}


@router.put("/{workflow_id}/deactivate")
async def deactivate_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Deactivate a workflow."""
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id)
    
    if not workflow or workflow.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found"
        )
    
    await service.deactivate_workflow(workflow_id)
    return {"message": "Workflow deactivated"}


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    trigger_data: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Manually execute a workflow."""
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id)
    
    if not workflow or workflow.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found"
        )
    
    execution = await service.execute_workflow(workflow_id, trigger_data or {})
    return {"message": "Workflow executed", "execution_id": execution.id}


@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecution])
async def get_workflow_executions(
    workflow_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get execution history for a workflow."""
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id)
    
    if not workflow or workflow.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found"
        )
    
    return await service.get_workflow_executions(workflow_id, skip, limit)


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Delete a workflow."""
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id)
    
    if not workflow or workflow.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found"
        )
    
    await service.delete_workflow(workflow_id)
    return {"message": "Workflow deleted"}


@router.get("/automation/rules", response_model=List[AutomationRule])
async def get_automation_rules(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get AI-suggested automation rules."""
    service = WorkflowService(db)
    return await service.get_automation_suggestions(current_user.studio_id)


@router.post("/automation/rules/{rule_id}/apply")
async def apply_automation_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Apply an automation rule to create a workflow."""
    service = WorkflowService(db)
    rule = await service.get_automation_rule(rule_id)
    
    if not rule:
        raise HTTPException(
            status_code=404,
            detail="Automation rule not found"
        )
    
    workflow = await service.apply_automation_rule(current_user.studio_id, rule_id)
    return {"message": "Automation rule applied", "workflow_id": workflow.id}


@router.post("/templates/{template_id}/apply")
async def apply_workflow_template(
    template_id: str,
    name: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Apply a workflow template."""
    service = WorkflowService(db)
    template = await service.get_workflow_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail="Workflow template not found"
        )
    
    workflow = await service.apply_template(current_user.studio_id, template_id, name)
    return {"message": "Template applied", "workflow_id": workflow.id}