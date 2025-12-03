"""
Feature Flags Configuration

AI-safe architecture: Feature flags allow safe rollout of new features
and quick rollback without code changes.

Usage:
    from app.core.features import features, is_feature_enabled
    if is_feature_enabled('new_upload_flow'):
        ...
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Set


@dataclass
class FeatureFlags:
    """Feature flags for the Photo Proof API."""
    
    # Upload features
    parallel_uploads: bool = True
    resumable_uploads: bool = True
    upload_compression: bool = True
    background_processing: bool = True
    
    # Project features
    folder_support: bool = True
    photo_versioning: bool = True
    batch_operations: bool = True
    
    # Client features
    client_self_registration: bool = False
    client_notifications: bool = True
    client_data_export: bool = True
    
    # Payment features
    online_payments: bool = False
    invoice_reminders: bool = True
    automated_receipts: bool = False
    
    # Security features
    rate_limiting: bool = True
    audit_logging: bool = True
    two_factor_auth: bool = False
    
    # AI features
    auto_tagging: bool = False
    facial_recognition: bool = False
    smart_cropping: bool = False
    
    # Debug/Dev
    debug_mode: bool = False
    mock_external_services: bool = False
    
    def __post_init__(self):
        """Load overrides from environment variables."""
        for flag_name in self.__dataclass_fields__:
            env_key = f"FEATURE_{flag_name.upper()}"
            env_value = os.getenv(env_key)
            if env_value is not None:
                setattr(self, flag_name, env_value.lower() in ('true', '1', 'yes'))


# Singleton instance
features = FeatureFlags()


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled."""
    if not hasattr(features, feature_name):
        return False
    return getattr(features, feature_name, False)


def get_enabled_features() -> Set[str]:
    """Get set of all enabled feature names."""
    return {
        name for name in features.__dataclass_fields__
        if getattr(features, name, False)
    }


def get_disabled_features() -> Set[str]:
    """Get set of all disabled feature names."""
    return {
        name for name in features.__dataclass_fields__
        if not getattr(features, name, False)
    }


def get_all_features() -> Dict[str, bool]:
    """Get dictionary of all features and their status."""
    return {
        name: getattr(features, name, False)
        for name in features.__dataclass_fields__
    }
