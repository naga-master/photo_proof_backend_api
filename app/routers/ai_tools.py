"""AI Tools router for managing AI tool configurations."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.schemas import UserRead
from app.services.ai_tools_service import AIToolsService
from app.core.permissions import require_use_ai_tools
from app.schemas.ai_tools import (
    AIToolCreate,
    AIToolUpdate,
    AIToolResponse,
    AIToolListResponse,
)


router = APIRouter()


@router.get("/ai-tools", response_model=AIToolListResponse)
def get_ai_tools(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(require_use_ai_tools)
):
    """
    Get all AI tools.
    
    Query Parameters:
    - active_only: Filter to only return active tools (default: True)
    
    Returns:
    - List of AI tools with thumbnail paths
    - Tools are ordered by order_index
    """
    try:
        service = AIToolsService(db)
        tools = service.get_all_tools(active_only=active_only)
        
        return AIToolListResponse(
            tools=[AIToolResponse.model_validate(tool) for tool in tools],
            total=len(tools)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch AI tools: {str(e)}"
        )


@router.get("/ai-tools/{tool_id}", response_model=AIToolResponse)
def get_ai_tool(
    tool_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(require_use_ai_tools)
):
    """Get a specific AI tool by ID."""
    try:
        service = AIToolsService(db)
        tool = service.get_tool_by_id(tool_id)
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI tool with ID {tool_id} not found"
            )
        
        return AIToolResponse.model_validate(tool)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch AI tool: {str(e)}"
        )


@router.post("/ai-tools", response_model=AIToolResponse, status_code=status.HTTP_201_CREATED)
def create_ai_tool(
    tool_data: AIToolCreate,
    current_user: UserRead = Depends(require_use_ai_tools),
    db: Session = Depends(get_db)
):
    """Create a new AI tool. Requires canUseAITools permission."""
    try:
        service = AIToolsService(db)
        tool = service.create_tool(tool_data)
        
        return AIToolResponse.model_validate(tool)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create AI tool: {str(e)}"
        )


@router.patch("/ai-tools/{tool_id}", response_model=AIToolResponse)
def update_ai_tool(
    tool_id: str,
    tool_data: AIToolUpdate,
    current_user: UserRead = Depends(require_use_ai_tools),
    db: Session = Depends(get_db)
):
    """Update an existing AI tool. Requires canUseAITools permission."""
    try:
        service = AIToolsService(db)
        tool = service.update_tool(tool_id, tool_data)
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI tool with ID {tool_id} not found"
            )
        
        return AIToolResponse.model_validate(tool)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update AI tool: {str(e)}"
        )


@router.delete("/ai-tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ai_tool(
    tool_id: str,
    current_user: UserRead = Depends(require_use_ai_tools),
    db: Session = Depends(get_db)
):
    """Delete an AI tool. Requires canUseAITools permission."""
    try:
        service = AIToolsService(db)
        success = service.delete_tool(tool_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI tool with ID {tool_id} not found"
            )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete AI tool: {str(e)}"
        )
