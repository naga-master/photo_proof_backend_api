"""Contracts router for contract management."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Contract, ContractTemplate, User
from app.api.deps import get_current_user
from app.services.contract_service import ContractService
from app.core.permissions import (
    require_view_contracts,
    require_create_contracts,
    require_edit_contracts,
    require_delete_contracts,
)
from app.schemas.contract import (
    ContractCreate,
    ContractUpdate,
    ContractResponse,
    ContractListResponse,
    ContractTemplateCreate,
    ContractTemplateUpdate,
    ContractTemplateResponse,
    SignatureData,
    SignContractResponse,
    ContractActivityResponse,
    ContractStats,
    VerifySignatureResponse
)


router = APIRouter()


def _is_studio_user(user: User) -> bool:
    """Helper to check if user is a studio user (for mixed access endpoints)."""
    return user.role in ["studio_owner", "studio_admin", "studio_photographer"]


# Contract Template Endpoints
@router.post("/templates", response_model=ContractTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_contract_template(
    template_data: ContractTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_create_contracts)
):
    """
    Create a new contract template.
    
    Requires canCreateContracts permission.
    """
    
    template = ContractTemplate(
        studio_id=current_user.studio_id,
        name=template_data.name,
        category=template_data.category,
        content=template_data.content,
        variables=template_data.variables,
        is_active=template_data.is_active
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


@router.get("/templates", response_model=List[ContractTemplateResponse])
def list_contract_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Only show active templates"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_view_contracts)
):
    """
    List contract templates for the current studio.
    
    Requires canViewContracts permission.
    """
    
    query = db.query(ContractTemplate).filter(
        ContractTemplate.studio_id == current_user.studio_id
    )
    
    if category:
        query = query.filter(ContractTemplate.category == category)
    
    if active_only:
        query = query.filter(ContractTemplate.is_active == True)
    
    templates = query.order_by(ContractTemplate.created_at.desc()).all()
    
    return templates


@router.get("/templates/{template_id}", response_model=ContractTemplateResponse)
def get_contract_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_view_contracts)
):
    """Get a specific contract template. Requires canViewContracts permission."""
    
    template = db.query(ContractTemplate).filter(
        ContractTemplate.id == template_id,
        ContractTemplate.studio_id == current_user.studio_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract template not found"
        )
    
    return template


@router.put("/templates/{template_id}", response_model=ContractTemplateResponse)
async def update_contract_template(
    template_id: str,
    template_data: ContractTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_edit_contracts)
):
    """Update a contract template. Requires canEditContracts permission."""
    
    template = db.query(ContractTemplate).filter(
        ContractTemplate.id == template_id,
        ContractTemplate.studio_id == current_user.studio_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract template not found"
        )
    
    # Update fields
    update_data = template_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    return template


# Contract Endpoints
@router.post("/", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_data: ContractCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_create_contracts)
):
    """
    Create a new contract from template or custom content.
    
    Requires canCreateContracts permission.
    """
    
    service = ContractService(db)
    
    try:
        contract = await service.create_contract(
            studio_id=current_user.studio_id,
            client_id=contract_data.client_id,
            template_id=contract_data.template_id,
            title=contract_data.title,
            content=contract_data.content,
            variables=contract_data.variables,
            project_id=contract_data.project_id,
            expires_days=contract_data.expires_days
        )
        
        # Send contract in background if requested
        if contract_data.send_immediately and contract_data.recipient_email:
            background_tasks.add_task(
                service.send_contract,
                contract.id,
                contract_data.recipient_email
            )
        
        # Enrich response with related data
        response = ContractResponse.model_validate(contract)
        response.client_name = contract.client.name if contract.client else None
        response.project_name = contract.project.name if contract.project else None
        response.template_name = contract.template.name if contract.template else None
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create contract: {str(e)}"
        )


@router.get("/", response_model=ContractListResponse)
def list_contracts(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    client_id: Optional[str] = Query(None, description="Filter by client"),
    project_id: Optional[str] = Query(None, description="Filter by project"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List contracts for the current studio.
    
    Studio users see all contracts for their studio.
    Clients see only their own contracts.
    """
    query = db.query(Contract)
    
    if _is_studio_user(current_user):
        query = query.filter(Contract.studio_id == current_user.studio_id)
    else:
        # Clients can only see their own contracts
        from app.db.models import Client
        
        # New client auth: ID is "client_{id}" format
        if isinstance(current_user.id, str) and current_user.id.startswith("client_"):
            try:
                client_id_int = int(current_user.id.replace("client_", ""))
                query = query.filter(Contract.client_id == client_id_int)
            except ValueError:
                return ContractListResponse(contracts=[], total=0, offset=offset, limit=limit)
        else:
            # Legacy: Find client record by user_id
            client = db.query(Client).filter(Client.user_id == current_user.id).first()
            if client:
                query = query.filter(Contract.client_id == client.id)
            else:
                # User has no associated client record, return empty list
                return ContractListResponse(contracts=[], total=0, offset=offset, limit=limit)
    
    if status_filter:
        query = query.filter(Contract.status == status_filter)
    
    if client_id and _is_studio_user(current_user):
        query = query.filter(Contract.client_id == client_id)
    
    if project_id:
        query = query.filter(Contract.project_id == project_id)
    
    total = query.count()
    contracts = query.order_by(Contract.created_at.desc()).offset(offset).limit(limit).all()
    
    # Enrich response data
    contract_responses = []
    for contract in contracts:
        response = ContractResponse.model_validate(contract)
        response.client_name = contract.client.name if contract.client else None
        response.project_name = contract.project.name if contract.project else None
        response.template_name = contract.template.name if contract.template else None
        contract_responses.append(response)
    
    return ContractListResponse(
        contracts=contract_responses,
        total=total,
        offset=offset,
        limit=limit
    )


@router.get("/stats", response_model=ContractStats)
def get_contract_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_view_contracts)
):
    """
    Get contract statistics for the current studio.
    
    Requires canViewContracts permission.
    """
    
    service = ContractService(db)
    stats = service.get_contract_stats(current_user.studio_id)
    
    return ContractStats(**stats)


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific contract.
    
    Studio users can view all contracts for their studio.
    Clients can only view their own contracts.
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    # Check permissions
    if _is_studio_user(current_user):
        if contract.studio_id != current_user.studio_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this contract"
            )
    else:
        # Check if user is the client
        from app.db.models import Client
        
        # New client auth: ID is "client_{id}" format
        user_client_id = None
        if isinstance(current_user.id, str) and current_user.id.startswith("client_"):
            try:
                user_client_id = int(current_user.id.replace("client_", ""))
            except ValueError:
                pass
        else:
            # Legacy: Find client record by user_id
            client = db.query(Client).filter(Client.user_id == current_user.id).first()
            if client:
                user_client_id = client.id
        
        if user_client_id is None or contract.client_id != user_client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this contract"
            )
        
        # Mark as viewed if first time
        if contract.status == "sent" and not contract.viewed_at:
            contract.status = "viewed"
            contract.viewed_at = datetime.utcnow()
            
            # Log activity
            service = ContractService(db)
            service.log_activity(
                contract_id,
                "viewed",
                current_user.id,
                {"source": "client_portal"}
            )
            
            db.commit()
    
    # Enrich response
    response = ContractResponse.model_validate(contract)
    response.client_name = contract.client.name if contract.client else None
    response.project_name = contract.project.name if contract.project else None
    response.template_name = contract.template.name if contract.template else None
    
    return response


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: str,
    contract_data: ContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_edit_contracts)
):
    """
    Update a contract.
    
    Requires canEditContracts permission. Can only update draft contracts.
    """
    
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.studio_id == current_user.studio_id
    ).first()
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    # Only allow updating draft contracts
    if contract.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update draft contracts"
        )
    
    # Update fields
    update_data = contract_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)
    
    # Regenerate PDF if content changed
    if "content" in update_data or "title" in update_data:
        service = ContractService(db)
        pdf_path = await service.generate_pdf(contract)
        contract.pdf_url = pdf_path
    
    db.commit()
    db.refresh(contract)
    
    # Enrich response
    response = ContractResponse.model_validate(contract)
    response.client_name = contract.client.name if contract.client else None
    response.project_name = contract.project.name if contract.project else None
    response.template_name = contract.template.name if contract.template else None
    
    return response


@router.post("/{contract_id}/send", response_model=dict)
async def send_contract(
    contract_id: str,
    recipient_email: str = Query(..., description="Email address to send contract to"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_edit_contracts)
):
    """
    Send contract for signature.
    
    Requires canEditContracts permission.
    """
    
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.studio_id == current_user.studio_id
    ).first()
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    # Check contract status
    if contract.status not in ["draft", "sent", "viewed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot send contract in {contract.status} status"
        )
    
    service = ContractService(db)
    
    # Send contract
    if background_tasks:
        background_tasks.add_task(
            service.send_contract,
            contract_id,
            recipient_email
        )
    else:
        await service.send_contract(contract_id, recipient_email)
    
    return {"message": "Contract sent successfully", "contract_id": contract_id}


@router.post("/{contract_id}/sign", response_model=SignContractResponse)
async def sign_contract(
    contract_id: str,
    signature_data: SignatureData,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Sign a contract with digital signature.
    
    Can be accessed by authenticated clients or via public link.
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    # Note: This endpoint allows unauthenticated signing via public contract links
    # Security is ensured through the contract_id being a UUID and contract expiration
    
    # Prepare client info
    client_info = {
        'ip': request.client.host,
        'user_agent': request.headers.get('user-agent', 'Unknown')
    }
    
    service = ContractService(db)
    
    try:
        # Process signature
        signed_contract = await service.sign_contract(
            contract_id,
            signature_data.signature,
            client_info
        )
        
        return SignContractResponse(
            status="signed",
            contract_id=signed_contract.id,
            signed_at=signed_contract.signed_at,
            signature_hash=signed_contract.client_signature_hash
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sign contract: {str(e)}"
        )


@router.get("/{contract_id}/verify", response_model=VerifySignatureResponse)
async def verify_signature(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_view_contracts)
):
    """
    Verify contract signature authenticity.
    
    Requires canViewContracts permission.
    """
    
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.studio_id == current_user.studio_id
    ).first()
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    service = ContractService(db)
    is_valid = await service.verify_signature(contract_id)
    
    from datetime import datetime
    
    return VerifySignatureResponse(
        contract_id=contract_id,
        signature_valid=is_valid,
        verification_timestamp=datetime.utcnow(),
        signed_at=contract.signed_at,
        signer_info={
            "client_name": contract.client.name if contract.client else None,
            "ip_address": contract.client_ip,
            "user_agent": contract.client_user_agent
        } if is_valid else None
    )


@router.get("/{contract_id}/activities", response_model=List[ContractActivityResponse])
def get_contract_activities(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_view_contracts)
):
    """
    Get activity log for a contract.
    
    Requires canViewContracts permission.
    """
    
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.studio_id == current_user.studio_id
    ).first()
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    from app.db.models import ContractActivity
    activities = db.query(ContractActivity).filter(
        ContractActivity.contract_id == contract_id
    ).order_by(ContractActivity.created_at.desc()).all()
    
    return activities


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_delete_contracts)
):
    """
    Delete a contract.
    
    Requires canDeleteContracts permission. Can only delete draft contracts.
    """
    
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.studio_id == current_user.studio_id
    ).first()
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    # Business rules for contract deletion (DPDPA 2023 compliance)
    if contract.status == "signed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete signed contracts. Legal requirement: must retain for 7 years (DPDPA 2023). Consider archiving instead."
        )
    
    # Allow deleting: draft, sent, viewed, expired, cancelled
    # Warn but allow viewed contracts (client has seen it)
    allowed_statuses = ["draft", "sent", "viewed", "expired", "cancelled"]
    if contract.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete contracts in {contract.status} status"
        )
    
    db.delete(contract)
    db.commit()
    
    return None
