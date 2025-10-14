"""Workflow automation schemas."""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


class WorkflowStatus(str):
    """Workflow execution status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowTrigger(BaseModel):
    """Workflow trigger definition."""
    type: str  # 'manual', 'time_based', 'event_based'
    conditions: Dict[str, Any]
    schedule: Optional[str] = None  # Cron expression for time-based


class WorkflowAction(BaseModel):
    """Workflow action definition."""
    id: str
    type: str  # 'send_email', 'create_invoice', 'update_status', 'notify'
    parameters: Dict[str, Any]
    order: int
    delay_minutes: Optional[int] = None


class WorkflowTemplate(BaseModel):
    """Pre-built workflow template."""
    id: str
    name: str
    description: str
    category: str
    trigger: Optional[WorkflowTrigger] = None
    actions: List[WorkflowAction] = []
    steps: List['WorkflowStep'] = []
    estimated_duration: Optional[int] = None  # days
    is_premium: bool = False
    is_active: bool = True
    tags: List[str] = []


class WorkflowStep(BaseModel):
    """Individual step in a workflow."""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    duration_days: Optional[int] = None
    order: Optional[int] = None
    is_completed: bool = False


class Workflow(BaseModel):
    """Workflow instance."""
    id: str
    name: str
    studio_id: str
    project_id: Optional[str] = None
    template_id: Optional[str] = None
    status: str
    steps: List[WorkflowStep] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


class WorkflowExecution(BaseModel):
    """Workflow execution record."""
    id: str
    workflow_id: str
    step_id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    trigger_data: Optional[Dict[str, Any]] = None
    action_results: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TaskReminder(BaseModel):
    """Task reminder information."""
    id: str
    title: str
    description: Optional[str] = None
    due_date: datetime
    priority: str = "medium"  # low, medium, high, critical
    project_id: Optional[str] = None
    client_id: Optional[str] = None
    is_completed: bool = False
    created_at: Optional[datetime] = None


class WorkflowRequest(BaseModel):
    """Request to create a workflow."""
    name: str
    project_id: Optional[str] = None
    template_id: Optional[str] = None
    description: Optional[str] = None


class WorkflowRead(BaseModel):
    """Workflow read schema."""
    id: str
    studio_id: str
    name: str
    description: Optional[str] = None
    status: str
    trigger: WorkflowTrigger
    actions: List[WorkflowAction]
    is_active: bool = True
    execution_count: int = 0
    last_execution: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateWorkflowRequest(BaseModel):
    """Request to create a workflow."""
    name: str
    description: Optional[str] = None
    trigger: Dict[str, Any]
    actions: List[Dict[str, Any]]
    is_active: bool = True


class WorkflowExecution(BaseModel):
    """Workflow execution record."""
    id: str
    workflow_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    trigger_data: Dict[str, Any]
    action_results: List[Dict[str, Any]]
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class WorkflowStats(BaseModel):
    """Workflow execution statistics."""
    total_workflows: int
    active_workflows: int
    total_executions: int
    success_rate: float
    recent_executions: List[WorkflowExecution]


class AutomationRule(BaseModel):
    """Smart automation rule."""
    id: str
    name: str
    description: str
    pattern: str  # AI-detected pattern
    suggested_action: Dict[str, Any]
    confidence_score: float
    usage_count: int = 0
    is_enabled: bool = False
    created_at: datetime