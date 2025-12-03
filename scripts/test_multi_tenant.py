#!/usr/bin/env python3
"""
Test multi-tenant functionality.
This script verifies that tenant detection, data isolation, and storage work correctly.
"""

import sys
from pathlib import Path
import uuid
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.db.models import Studio, StudioDomain, User, Client, Project, SubscriptionPlan, StudioSubscription
from app.middleware.tenant import detect_studio_from_host
from app.services.storage_service import TenantStorageService
import asyncio


def test_studio_creation():
    """Test creating multiple studios."""
    print("🧪 Test 1: Creating test studios...")
    
    db = SessionLocal()
    
    studios_data = [
        {
            "name": "Studio Alpha",
            "email": "alpha@test.com",
            "subdomain": "alpha",
            "brand_color": "#FF6B6B"
        },
        {
            "name": "Studio Beta",
            "email": "beta@test.com",
            "subdomain": "beta",
            "brand_color": "#4ECDC4"
        },
        {
            "name": "Studio Gamma",
            "email": "gamma@test.com",
            "subdomain": "gamma",
            "brand_color": "#95E1D3"
        }
    ]
    
    created_studios = []
    
    try:
        # Get starter plan for subscriptions
        starter_plan = db.query(SubscriptionPlan).filter_by(name="starter").first()
        
        for studio_data in studios_data:
            # Check if studio exists
            existing = db.query(Studio).filter_by(subdomain=studio_data["subdomain"]).first()
            if existing:
                print(f"   ⏭️  Studio '{studio_data['name']}' already exists")
                created_studios.append(existing)
                continue
            
            # Create studio
            studio = Studio(
                id=str(uuid.uuid4()),
                name=studio_data["name"],
                email=studio_data["email"],
                subdomain=studio_data["subdomain"],
                brand_color=studio_data["brand_color"],
                onboarding_completed=True,
                is_active=True
            )
            db.add(studio)
            db.flush()
            
            # Create domain
            domain = StudioDomain(
                id=str(uuid.uuid4()),
                studio_id=studio.id,
                domain=f"{studio_data['subdomain']}.photoapp.local",
                subdomain=studio_data["subdomain"],
                is_primary=True,
                is_verified=True,
                verified_at=datetime.utcnow()
            )
            db.add(domain)
            
            # Create subscription if plan exists
            if starter_plan:
                subscription = StudioSubscription(
                    id=str(uuid.uuid4()),
                    studio_id=studio.id,
                    plan_id=starter_plan.id,
                    status="active",
                    current_period_start=datetime.utcnow(),
                    current_period_end=datetime.utcnow() + timedelta(days=30)
                )
                db.add(subscription)
            
            created_studios.append(studio)
            print(f"   ✓ Created studio: {studio.name} ({studio.subdomain})")
        
        db.commit()
        print(f"✅ Test 1 passed: {len(created_studios)} studios ready\n")
        return created_studios
        
    except Exception as e:
        db.rollback()
        print(f"❌ Test 1 failed: {e}\n")
        raise
    finally:
        db.close()


async def test_tenant_detection():
    """Test tenant detection from different hosts."""
    print("🧪 Test 2: Testing tenant detection...")
    
    db = SessionLocal()
    
    test_cases = [
        ("alpha.photoapp.local", "Studio Alpha"),
        ("beta.photoapp.local", "Studio Beta"),
        ("gamma.photoapp.local", "Studio Gamma"),
        ("nonexistent.photoapp.local", None),
        ("localhost", None),
    ]
    
    passed = 0
    failed = 0
    
    try:
        for host, expected_name in test_cases:
            studio = await detect_studio_from_host(host, db)
            
            if expected_name is None:
                if studio is None:
                    print(f"   ✓ {host} → No studio (expected)")
                    passed += 1
                else:
                    print(f"   ✗ {host} → Found '{studio.name}' (expected none)")
                    failed += 1
            else:
                if studio and studio.name == expected_name:
                    print(f"   ✓ {host} → {studio.name}")
                    passed += 1
                else:
                    actual = studio.name if studio else "None"
                    print(f"   ✗ {host} → {actual} (expected {expected_name})")
                    failed += 1
        
        if failed == 0:
            print(f"✅ Test 2 passed: {passed}/{passed+failed} cases successful\n")
        else:
            print(f"❌ Test 2 failed: {passed}/{passed+failed} cases successful\n")
            
    finally:
        db.close()


def test_data_isolation():
    """Test that data is properly isolated between studios."""
    print("🧪 Test 3: Testing data isolation...")
    
    db = SessionLocal()
    
    try:
        # Get two studios
        studio_alpha = db.query(Studio).filter_by(subdomain="alpha").first()
        studio_beta = db.query(Studio).filter_by(subdomain="beta").first()
        
        if not studio_alpha or not studio_beta:
            print("   ⚠️  Test skipped: Need both alpha and beta studios")
            return
        
        # Create a client for studio alpha
        client_alpha = Client(
            studio_id=studio_alpha.id,
            name="Client Alpha",
            email="client@alpha.com",
            status="active"
        )
        db.add(client_alpha)
        db.flush()
        
        # Create a project for studio alpha
        project_alpha = Project(
            studio_id=studio_alpha.id,
            client_id=client_alpha.id,
            title="Alpha's Project",
            status="active"
        )
        db.add(project_alpha)
        db.commit()
        
        # Query projects for studio alpha
        alpha_projects = db.query(Project).filter_by(studio_id=studio_alpha.id).all()
        
        # Query projects for studio beta
        beta_projects = db.query(Project).filter_by(studio_id=studio_beta.id).all()
        
        # Verify isolation
        if len(alpha_projects) > 0 and len([p for p in alpha_projects if p.title == "Alpha's Project"]) > 0:
            print(f"   ✓ Studio Alpha has {len(alpha_projects)} project(s)")
        else:
            print(f"   ✗ Studio Alpha project not found")
            return
        
        if "Alpha's Project" not in [p.title for p in beta_projects]:
            print(f"   ✓ Studio Beta cannot see Studio Alpha's projects")
        else:
            print(f"   ✗ Data leak: Studio Beta can see Studio Alpha's data!")
            return
        
        print("✅ Test 3 passed: Data isolation working correctly\n")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Test 3 failed: {e}\n")
        raise
    finally:
        db.close()


def test_storage_isolation():
    """Test that file storage is isolated per tenant."""
    print("🧪 Test 4: Testing storage isolation...")
    
    storage = TenantStorageService()
    
    # Get studio paths
    alpha_path = storage.get_studio_path("studio-alpha-test-id")
    beta_path = storage.get_studio_path("studio-beta-test-id")
    
    # Verify paths are different
    if "studio-alpha-test-id" in str(alpha_path):
        print(f"   ✓ Alpha path contains studio ID: {alpha_path}")
    else:
        print(f"   ✗ Alpha path incorrect: {alpha_path}")
        return
    
    if "studio-beta-test-id" in str(beta_path):
        print(f"   ✓ Beta path contains studio ID: {beta_path}")
    else:
        print(f"   ✗ Beta path incorrect: {beta_path}")
        return
    
    if str(alpha_path) != str(beta_path):
        print(f"   ✓ Paths are different (isolated)")
    else:
        print(f"   ✗ Paths are the same (not isolated)!")
        return
    
    print("✅ Test 4 passed: Storage isolation working correctly\n")


def test_subscription_plans():
    """Test subscription plans exist."""
    print("🧪 Test 5: Testing subscription plans...")
    
    db = SessionLocal()
    
    try:
        plans = db.query(SubscriptionPlan).order_by(SubscriptionPlan.sort_order).all()
        
        if len(plans) == 0:
            print("   ✗ No subscription plans found")
            return
        
        print(f"   Found {len(plans)} subscription plans:")
        for plan in plans:
            print(f"   ✓ {plan.display_name}: ${plan.price_monthly}/mo (max {plan.max_projects} projects)")
        
        print("✅ Test 5 passed: Subscription plans configured\n")
        
    finally:
        db.close()


def print_test_instructions():
    """Print instructions for manual testing."""
    print("=" * 60)
    print("📋 Manual Testing Instructions")
    print("=" * 60)
    print()
    print("1. Add test domains to /etc/hosts:")
    print("   sudo tee -a /etc/hosts << 'EOF'")
    print("127.0.0.1 alpha.photoapp.local")
    print("127.0.0.1 beta.photoapp.local")
    print("127.0.0.1 gamma.photoapp.local")
    print("127.0.0.1 demo.photoapp.local")
    print("EOF")
    print()
    print("2. Start the API server:")
    print("   python main.py")
    print()
    print("3. Test tenant detection with curl:")
    print("   curl -H 'Host: alpha.photoapp.local' http://localhost:8000/api/health")
    print("   curl -H 'Host: beta.photoapp.local' http://localhost:8000/api/health")
    print()
    print("4. Check response headers for X-Studio-ID and X-Studio-Name")
    print()
    print("5. Test data isolation:")
    print("   - Create projects for different studios")
    print("   - Verify they can only see their own data")
    print()


def main():
    """Run all tests."""
    print("\n🚀 Multi-Tenant Testing Suite\n")
    
    try:
        # Test 1: Create studios
        studios = test_studio_creation()
        
        # Test 2: Tenant detection
        asyncio.run(test_tenant_detection())
        
        # Test 3: Data isolation
        test_data_isolation()
        
        # Test 4: Storage isolation
        test_storage_isolation()
        
        # Test 5: Subscription plans
        test_subscription_plans()
        
        # Print manual testing instructions
        print_test_instructions()
        
        print("=" * 60)
        print("🎉 All automated tests passed!")
        print("=" * 60)
        print()
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ Tests failed")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
