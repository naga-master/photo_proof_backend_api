"""Data rights endpoints for DPDPA compliance."""

import json
import os
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..db.models import (
    User,
    UserConsent,
    DataExportRequest,
    AccountDeletionRequest,
    Contract,
)
from ..schemas.users import UserRead
from ..schemas.data_rights import (
    ConsentCreate,
    ConsentResponse,
    ConsentPreferences,
    ConsentWithdraw,
    DataExportRequest as DataExportRequestSchema,
    DataExportResponse,
    DataCorrectionRequest,
    DataCorrectionResponse,
    AccountDeletionRequest as AccountDeletionRequestSchema,
    AccountDeletionResponse,
    DataSummary,
    PrivacySettingsResponse,
)
from ..core.dependencies import get_current_user
from ..services.auth_service import AuthService

router = APIRouter(tags=["Data Rights"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# Consent Management
@router.get("/consent", response_model=ConsentPreferences)
async def get_consent_preferences(
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's consent preferences."""
    consents = db.query(UserConsent).filter(
        UserConsent.user_id == current_user.id,
        UserConsent.withdrawal_timestamp.is_(None),
    ).all()
    
    # If NO consent records exist, return all false (user needs to consent)
    if not consents:
        return ConsentPreferences(
            essential=False,
            marketing_emails=False,
            sms_notifications=False,
            analytics=False,
        )
    
    # Build preferences from consents
    prefs = ConsentPreferences(
        essential=False,  # Default to false, will be set if consent exists
        marketing_emails=False,
        sms_notifications=False,
        analytics=False,
    )
    for consent in consents:
        if hasattr(prefs, consent.consent_type):
            setattr(prefs, consent.consent_type, consent.consent_given)
    
    return prefs


@router.put("/consent", response_model=ConsentResponse)
async def update_consent(
    consent_data: ConsentCreate,
    request: Request,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update or create a consent."""
    # Check if consent already exists
    existing = db.query(UserConsent).filter(
        UserConsent.user_id == current_user.id,
        UserConsent.consent_type == consent_data.consent_type,
        UserConsent.withdrawal_timestamp.is_(None),
    ).first()
    
    if existing:
        # Update existing consent
        existing.consent_given = consent_data.consent_given
        existing.consent_version = consent_data.consent_version
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new consent
    ip_address = consent_data.ip_address or get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    
    new_consent = UserConsent(
        user_id=current_user.id,
        consent_type=consent_data.consent_type,
        consent_given=consent_data.consent_given,
        consent_version=consent_data.consent_version,
        ip_address=ip_address,
        user_agent=user_agent,
        consent_metadata=consent_data.consent_metadata,
    )
    
    db.add(new_consent)
    db.commit()
    db.refresh(new_consent)
    
    # Update user's summary consent field
    if consent_data.consent_type == "essential" and consent_data.consent_given:
        # Fetch the actual User model from DB to update it
        user_model = db.query(User).filter(User.id == current_user.id).first()
        if user_model:
            user_model.consent_given = True
            user_model.consent_timestamp = datetime.utcnow()
            user_model.consent_version = consent_data.consent_version
            user_model.consent_ip_address = ip_address
            db.commit()
    
    return new_consent


@router.post("/consent/withdraw", response_model=ConsentResponse)
async def withdraw_consent(
    withdraw_data: ConsentWithdraw,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Withdraw a consent."""
    # Find the active consent
    consent = db.query(UserConsent).filter(
        UserConsent.user_id == current_user.id,
        UserConsent.consent_type == withdraw_data.consent_type,
        UserConsent.withdrawal_timestamp.is_(None),
    ).first()
    
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active consent found for this type",
        )
    
    # Cannot withdraw essential consent
    if withdraw_data.consent_type == "essential":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Essential consent cannot be withdrawn. Delete your account instead.",
        )
    
    # Mark as withdrawn
    consent.withdrawal_timestamp = datetime.utcnow()
    consent.consent_given = False
    consent.updated_at = datetime.utcnow()
    
    if withdraw_data.reason:
        consent.consent_metadata = consent.consent_metadata or {}
        consent.consent_metadata["withdrawal_reason"] = withdraw_data.reason
    
    db.commit()
    db.refresh(consent)
    
    return consent


# Data Access (Right to Know)
@router.get("/summary", response_model=DataSummary)
async def get_data_summary(
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get summary of user's data."""
    # Get counts
    contracts_count = db.query(func.count(Contract.id)).filter(
        Contract.client_id == current_user.id
    ).scalar() or 0
    
    # Get active consents
    active_consents = db.query(UserConsent).filter(
        UserConsent.user_id == current_user.id,
        UserConsent.consent_given == True,
        UserConsent.withdrawal_timestamp.is_(None),
    ).all()
    
    consent_types = [c.consent_type for c in active_consents]
    
    # Get data exports count
    exports_count = db.query(func.count(DataExportRequest.id)).filter(
        DataExportRequest.user_id == current_user.id
    ).scalar() or 0
    
    # Get deletion requests count
    deletions_count = db.query(func.count(AccountDeletionRequest.id)).filter(
        AccountDeletionRequest.user_id == current_user.id
    ).scalar() or 0
    
    return DataSummary(
        user_id=current_user.id,
        user_name=current_user.name,
        user_email=current_user.email,
        created_at=current_user.created_at,
        last_login=current_user.last_login_at,
        contracts_count=contracts_count,
        active_consents=consent_types,
        data_exports_count=exports_count,
        deletion_requests_count=deletions_count,
    )


# Data Portability (Right to Export)
@router.post("/export", response_model=DataExportResponse)
async def request_data_export(
    export_request: DataExportRequestSchema,
    request: Request,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Request export of user data."""
    ip_address = get_client_ip(request)
    
    # Create export request
    new_export = DataExportRequest(
        user_id=current_user.id,
        export_format=export_request.export_format,
        include_contracts=export_request.include_contracts,
        include_signatures=export_request.include_signatures,
        include_activity_logs=export_request.include_activity_logs,
        status="pending",
        ip_address=ip_address,
        expires_at=datetime.utcnow() + timedelta(hours=24),  # Link expires in 24h
    )
    
    db.add(new_export)
    db.commit()
    db.refresh(new_export)
    
    # TODO: Trigger background job to generate export
    # For now, we'll generate it synchronously
    try:
        export_data = _generate_export_data(current_user, export_request, db)
        
        # Save to file (in production, use S3 or similar)
        export_filename = f"photoproof_data_{current_user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        export_path = f"/tmp/{export_filename}"  # In production, use proper storage
        
        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2, default=str)
        
        file_size = os.path.getsize(export_path)
        
        # Update export request
        new_export.status = "completed"
        new_export.file_path = export_path
        new_export.file_size_bytes = file_size
        new_export.download_url = f"/v2/data-rights/export/{new_export.id}/download"
        new_export.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(new_export)
        
    except Exception as e:
        new_export.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate export: {str(e)}",
        )
    
    return new_export


@router.get("/export/{export_id}/download")
async def download_data_export(
    export_id: str,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download an exported data file."""
    export_request = db.query(DataExportRequest).filter(
        DataExportRequest.id == export_id,
        DataExportRequest.user_id == current_user.id,
    ).first()
    
    if not export_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export request not found",
        )
    
    if export_request.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export is not ready. Status: {export_request.status}",
        )
    
    # Check if expired
    if export_request.expires_at and datetime.utcnow() > export_request.expires_at:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Download link has expired",
        )
    
    # Update downloaded timestamp
    export_request.downloaded_at = datetime.utcnow()
    db.commit()
    
    # Return file (in production, redirect to S3 URL)
    from fastapi.responses import FileResponse
    return FileResponse(
        export_request.file_path,
        media_type="application/json",
        filename=os.path.basename(export_request.file_path),
    )


def _generate_export_data(user: User, export_request: DataExportRequestSchema, db: Session) -> dict:
    """Generate export data for user."""
    data = {
        "export_id": str(datetime.utcnow().timestamp()),
        "generated_at": datetime.utcnow().isoformat(),
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login_at.isoformat() if user.last_login_at else None,
        },
        "consents": [],
        "contracts": [],
        "data_exports": [],
    }
    
    # Add consents
    consents = db.query(UserConsent).filter(UserConsent.user_id == user.id).all()
    data["consents"] = [
        {
            "type": c.consent_type,
            "given": c.consent_given,
            "timestamp": c.consent_timestamp.isoformat() if c.consent_timestamp else None,
            "withdrawn": c.withdrawal_timestamp.isoformat() if c.withdrawal_timestamp else None,
        }
        for c in consents
    ]
    
    # Add contracts if requested
    if export_request.include_contracts:
        contracts = db.query(Contract).filter(Contract.client_id == user.id).all()
        data["contracts"] = [
            {
                "id": c.id,
                "title": c.title,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "signed_at": c.signed_at.isoformat() if c.signed_at else None,
            }
            for c in contracts
        ]
    
    return data


# Data Correction (Right to Rectify)
@router.put("/correct", response_model=DataCorrectionResponse)
async def correct_user_data(
    correction: DataCorrectionRequest,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Correct/update user data."""
    updated_fields = []
    
    # Fetch the actual User model from DB
    user_model = db.query(User).filter(User.id == current_user.id).first()
    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if correction.name and correction.name != current_user.name:
        user_model.name = correction.name
        updated_fields.append("name")
    
    if correction.email and correction.email != current_user.email:
        # Check if email already exists
        existing = db.query(User).filter(User.email == correction.email).first()
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use",
            )
        user_model.email = correction.email
        user_model.email_verified = False  # Need to re-verify
        updated_fields.append("email")
    
    if correction.phone and correction.phone != current_user.phone:
        user_model.phone = correction.phone
        updated_fields.append("phone")
    
    if updated_fields:
        db.commit()
        return DataCorrectionResponse(
            success=True,
            message=f"Updated {len(updated_fields)} field(s)",
            updated_fields=updated_fields,
        )
    
    return DataCorrectionResponse(
        success=False,
        message="No changes detected",
        updated_fields=[],
    )


# Account Deletion (Right to Erasure)
@router.post("/delete-account", response_model=AccountDeletionResponse)
async def request_account_deletion(
    deletion_request: AccountDeletionRequestSchema,
    request: Request,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Request account deletion."""
    # Fetch user model to verify password
    user_model = db.query(User).filter(User.id == current_user.id).first()
    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Verify password
    if not AuthService.verify_password(deletion_request.password, user_model.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )
    
    # Check if user confirmed
    if not deletion_request.confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must confirm account deletion",
        )
    
    # Check for active contracts (7-year retention requirement)
    seven_years_ago = datetime.utcnow() - timedelta(days=7*365)
    active_contracts = db.query(Contract).filter(
        Contract.client_id == current_user.id,
        Contract.signed_at > seven_years_ago,
    ).count()
    
    can_delete = active_contracts == 0
    
    ip_address = get_client_ip(request)
    
    # Create deletion request
    new_deletion = AccountDeletionRequest(
        user_id=current_user.id,
        reason=deletion_request.reason,
        confirmation=True,
        status="approved" if can_delete else "rejected",
        rejection_reason="Active contracts must be retained for 7 years" if not can_delete else None,
        active_contracts_count=active_contracts,
        can_delete=can_delete,
        deletion_date=datetime.utcnow() if can_delete else None,
        ip_address=ip_address,
    )
    
    db.add(new_deletion)
    db.commit()
    db.refresh(new_deletion)
    
    # If can delete, anonymize user immediately
    if can_delete:
        _anonymize_user(user_model, db)
        new_deletion.completed_at = datetime.utcnow()
        new_deletion.status = "completed"
        db.commit()
    
    return new_deletion


def _anonymize_user(user: User, db: Session):
    """Anonymize user data (soft delete)."""
    user.name = f"Deleted User {user.id[:8]}"
    user.email = f"deleted_{user.id}@internal.photoproof.com"
    user.username = f"deleted_{user.id}"
    user.phone = None
    user.is_active = False
    user.deleted_at = datetime.utcnow()
    user.password_hash = None
    
    # Keep contracts but anonymize
    contracts = db.query(Contract).filter(Contract.client_id == user.id).all()
    for contract in contracts:
        contract.client_name = "Deleted User"
        contract.client_email = f"deleted@internal"
    
    db.commit()


@router.get("/privacy-settings", response_model=PrivacySettingsResponse)
async def get_privacy_settings(
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get complete privacy settings for user."""
    # Get consent preferences
    consent_prefs = await get_consent_preferences(current_user, db)
    
    # Get data summary
    data_summary = await get_data_summary(current_user, db)
    
    # Check for pending deletion
    pending_deletion = db.query(AccountDeletionRequest).filter(
        AccountDeletionRequest.user_id == current_user.id,
        AccountDeletionRequest.status == "pending",
    ).first()
    
    # Check if can delete
    seven_years_ago = datetime.utcnow() - timedelta(days=7*365)
    active_contracts = db.query(Contract).filter(
        Contract.client_id == current_user.id,
        Contract.signed_at > seven_years_ago,
    ).count()
    
    return PrivacySettingsResponse(
        consent_preferences=consent_prefs,
        data_summary=data_summary,
        has_pending_deletion_request=pending_deletion is not None,
        can_delete_account=active_contracts == 0,
        active_contracts_count=active_contracts,
    )
