#!/usr/bin/env python3
"""
Initialize multi-tenant database tables.
This script creates all the new multi-tenant tables using SQLAlchemy models.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import engine
from app.db.models import Base, SubscriptionPlan
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta


def create_tables():
    """Create all database tables."""
    print("🔨 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully")


def seed_subscription_plans():
    """Seed default subscription plans."""
    print("\n📦 Seeding subscription plans...")
    
    session = Session(bind=engine)
    
    # Check if plans already exist
    existing_count = session.query(SubscriptionPlan).count()
    if existing_count > 0:
        print(f"⏭️  Subscription plans already exist ({existing_count} plans), skipping seed")
        session.close()
        return
    
    plans = [
        SubscriptionPlan(
            id=str(uuid.uuid4()),
            name="starter",
            display_name="Starter Plan",
            description="Perfect for individual photographers starting out",
            price_monthly=29.00,
            price_yearly=290.00,
            max_projects=10,
            max_storage_gb=10,
            max_users=1,
            max_clients=50,
            features={
                "custom_domain": False,
                "white_label": False,
                "api_access": False,
                "priority_support": False,
                "max_photo_variants": 3
            },
            is_active=True,
            is_visible=True,
            sort_order=1
        ),
        SubscriptionPlan(
            id=str(uuid.uuid4()),
            name="professional",
            display_name="Professional Plan",
            description="For growing photography studios",
            price_monthly=99.00,
            price_yearly=990.00,
            max_projects=100,
            max_storage_gb=100,
            max_users=5,
            max_clients=500,
            features={
                "custom_domain": True,
                "white_label": True,
                "api_access": True,
                "priority_support": False,
                "max_photo_variants": 5,
                "advanced_analytics": True
            },
            is_active=True,
            is_visible=True,
            sort_order=2
        ),
        SubscriptionPlan(
            id=str(uuid.uuid4()),
            name="enterprise",
            display_name="Enterprise Plan",
            description="For large studios with advanced needs",
            price_monthly=299.00,
            price_yearly=2990.00,
            max_projects=999999,
            max_storage_gb=1000,
            max_users=20,
            max_clients=999999,
            features={
                "custom_domain": True,
                "white_label": True,
                "api_access": True,
                "priority_support": True,
                "max_photo_variants": 10,
                "advanced_analytics": True,
                "custom_integrations": True,
                "dedicated_support": True
            },
            is_active=True,
            is_visible=True,
            sort_order=3
        )
    ]
    
    try:
        for plan in plans:
            session.add(plan)
            print(f"   ✓ Added plan: {plan.display_name} (${plan.price_monthly}/mo)")
        
        session.commit()
        print(f"✅ Seeded {len(plans)} subscription plans")
    except Exception as e:
        session.rollback()
        print(f"❌ Error seeding plans: {e}")
        raise
    finally:
        session.close()


def create_sample_studio():
    """Create a sample studio for testing."""
    print("\n🏢 Creating sample studio...")
    
    from app.db.models import Studio, StudioDomain, StudioSubscription
    
    session = Session(bind=engine)
    
    try:
        # Check if sample studio exists
        existing_studio = session.query(Studio).filter_by(subdomain="demo").first()
        if existing_studio:
            print(f"⏭️  Sample studio already exists: {existing_studio.name}")
            session.close()
            return
        
        # Get starter plan
        starter_plan = session.query(SubscriptionPlan).filter_by(name="starter").first()
        if not starter_plan:
            print("❌ Starter plan not found. Run seed_subscription_plans first.")
            session.close()
            return
        
        # Create studio
        studio = Studio(
            id=str(uuid.uuid4()),
            name="Demo Photography Studio",
            email="demo@photoproof.com",
            subdomain="demo",
            brand_color="#6366F1",
            typography="System Default (Inter & Cormorant)",
            onboarding_completed=True,
            onboarding_step="completed",
            is_active=True
        )
        session.add(studio)
        session.flush()  # Get studio.id
        
        # Create domain
        domain = StudioDomain(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            domain="demo.photoapp.local",
            subdomain="demo",
            is_primary=True,
            is_verified=True,
            verified_at=datetime.utcnow()
        )
        session.add(domain)
        
        # Create subscription
        subscription = StudioSubscription(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            plan_id=starter_plan.id,
            status="trial",
            trial_ends_at=datetime.utcnow() + timedelta(days=14),
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        session.add(subscription)
        
        session.commit()
        
        print(f"✅ Created sample studio:")
        print(f"   Name: {studio.name}")
        print(f"   Subdomain: {studio.subdomain}")
        print(f"   Domain: {domain.domain}")
        print(f"   Studio ID: {studio.id}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating sample studio: {e}")
        raise
    finally:
        session.close()


def main():
    """Main initialization function."""
    print("🚀 Initializing Multi-Tenant Database\n")
    
    try:
        # Step 1: Create tables
        create_tables()
        
        # Step 2: Seed subscription plans
        seed_subscription_plans()
        
        # Step 3: Create sample studio
        create_sample_studio()
        
        print("\n" + "="*50)
        print("🎉 Multi-tenant database initialized successfully!")
        print("="*50)
        print("\n📝 Next steps:")
        print("   1. Add entry to /etc/hosts:")
        print("      sudo echo '127.0.0.1 demo.photoapp.local' >> /etc/hosts")
        print("   2. Start the API server:")
        print("      python main.py")
        print("   3. Test tenant detection:")
        print("      curl -H 'Host: demo.photoapp.local' http://localhost:8000/api/health")
        print()
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
