"""
Seed products for the photo proof store.
Run this script to populate the database with products, options, and mockup images.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.models import Product, ProductOption, ProductMockupImage
from app.db.models.base import Base

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

products_data = [
    {
        'name': 'Lustre Print',
        'product_type': 'print',
        'short_description': 'Professional quality prints with a subtle sheen.',
        'detailed_description': 'Our Lustre Prints are a classic choice, offering the color saturation of a glossy finish with the fingerprint resistance of matte. Printed on archival quality paper, these prints are designed to last a lifetime.',
        'base_price': 10.00,
        'is_active': True,
        'specs': {
            'Paper Type': 'Kodak Endura Professional',
            'Finish': 'Lustre (Semi-Matte)',
            'Archival Quality': '100+ years',
        },
        'sizes': [
            {'size': '4x6', 'price': 10},
            {'size': '5x7', 'price': 20},
            {'size': '8x10', 'price': 30},
            {'size': '11x14', 'price': 40},
            {'size': '16x20', 'price': 60},
            {'size': '20x30', 'price': 85},
        ],
        'types': [
            {'name': 'Lustre'},
            {'name': 'Glossy'},
            {'name': 'Deep Matte'},
        ],
        'mockup_images': [
            'data/images/lustre_print.jpg',
        ],
    },
    {
        'name': 'Fine Art Print',
        'product_type': 'fine_art',
        'short_description': 'Museum-quality prints on textured, heavyweight paper.',
        'detailed_description': 'Elevate your photos with our Fine Art Prints. Using archival inks on acid-free, textured paper, these prints offer exceptional image permanence and a stunning, artistic feel.',
        'base_price': 90.00,
        'is_active': True,
        'specs': {
            'Paper Type': 'Archival Matte or Textured Rag',
            'Inks': 'Pigment-based archival inks',
            'Weight': '310 gsm',
        },
        'sizes': [
            {'size': '11x14', 'price': 90},
            {'size': '16x20', 'price': 120},
            {'size': '20x30', 'price': 150},
        ],
        'types': None,
        'mockup_images': [
            'data/images/fine_art.jpg',
        ],
    },
    {
        'name': 'Digital File',
        'product_type': 'digital',
        'short_description': 'High-resolution digital downloads of your photos.',
        'detailed_description': 'Get a high-resolution digital copy of your favorite photos, perfect for sharing online, printing on your own, or for archival purposes. Delivered instantly via email.',
        'base_price': 25.00,
        'is_active': True,
        'specs': {
            'Resolution': '300 DPI JPEG',
            'Delivery': 'Instant Download',
            'License': 'Personal Use',
        },
        'sizes': [
            {'size': 'Single Photo', 'price': 25},
            {'size': 'Full Gallery', 'price': 500},
        ],
        'types': None,
        'mockup_images': [
            'data/images/digital_file.jpg',
        ],
    },
    {
        'name': 'Gallery Wrapped Canvas',
        'product_type': 'canvas',
        'short_description': 'A timeless, ready-to-hang piece of art.',
        'detailed_description': 'Your photo is printed on high-quality canvas and stretched over a sturdy wooden frame. With a classic gallery wrap, this piece is ready to hang and admire right out of the box.',
        'base_price': 150.00,
        'is_active': True,
        'specs': {
            'Material': 'Archival-grade canvas',
            'Frame': '1.5" deep solid wood',
            'Finish': 'Protective UV-resistant coating',
        },
        'sizes': [
            {'size': '16x20', 'price': 150},
            {'size': '24x36', 'price': 250},
        ],
        'types': None,
        'mockup_images': [
            'data/images/gellery_wrapped_canvas.webp',
        ],
    },
    {
        'name': 'Metal Print',
        'product_type': 'metal',
        'short_description': 'Vibrant, high-gloss prints on a sleek aluminum panel.',
        'detailed_description': 'Make your images pop with a Metal Print. Your photo is infused directly into a sheet of aluminum for a brilliant, durable, and modern display. Comes with a float mount for a stunning wall presentation.',
        'base_price': 220.00,
        'is_active': True,
        'specs': {
            'Material': 'Dye-infused Aluminum',
            'Finish': 'High Gloss',
            'Features': 'Waterproof, scratch-resistant',
        },
        'sizes': [
            {'size': '16x20', 'price': 220},
            {'size': '24x36', 'price': 350},
        ],
        'types': None,
        'mockup_images': [
            'data/images/metal_print.jpeg',
        ],
    },
    {
        'name': 'Photo Album',
        'product_type': 'album',
        'short_description': 'A beautiful, custom-designed album of your day.',
        'detailed_description': 'A handcrafted, lay-flat album featuring your selected images. Choose from a variety of cover materials and customization options to create a perfect heirloom.',
        'base_price': 800.00,
        'is_active': True,
        'specs': {
            'Pages': '20-50 thick, lay-flat pages',
            'Cover': 'Linen or Leather options',
            'Design': 'Custom layout included',
        },
        'sizes': [
            {'size': '10x10 Album', 'price': 800},
        ],
        'types': None,
        'mockup_images': [
            'data/images/photo_album.webp',
        ],
    },
]


def seed_products(db: Session):
    """Seed products into the database."""
    print("Starting product seeding...")
    
    # Check if products already exist
    existing_count = db.query(Product).count()
    if existing_count > 0:
        print(f"⚠️  Database already has {existing_count} products.")
        response = input("Do you want to delete all existing products and re-seed? (yes/no): ")
        if response.lower() != 'yes':
            print("Seeding cancelled.")
            return
        
        # Delete existing products (cascade will delete options and images)
        print("Deleting existing products...")
        db.query(ProductMockupImage).delete()
        db.query(ProductOption).delete()
        db.query(Product).delete()
        db.commit()
        print("✓ Deleted existing products")
    
    # Seed products
    for product_data in products_data:
        print(f"\nCreating product: {product_data['name']}")
        
        # Create product
        product = Product(
            name=product_data['name'],
            product_type=product_data['product_type'],
            short_description=product_data['short_description'],
            detailed_description=product_data['detailed_description'],
            base_price=product_data['base_price'],
            is_active=product_data['is_active'],
            specs=product_data['specs'],
        )
        db.add(product)
        db.flush()  # Get product.id
        
        # Add size options
        for size_data in product_data['sizes']:
            option = ProductOption(
                product_id=product.id,
                option_type='size',
                name=size_data['size'],
                price_modifier=size_data['price'] - product_data['base_price'],
            )
            db.add(option)
            print(f"  + Size option: {size_data['size']} (₹{size_data['price']})")
        
        # Add type options if present
        if product_data['types']:
            for type_data in product_data['types']:
                option = ProductOption(
                    product_id=product.id,
                    option_type='type',
                    name=type_data['name'],
                    price_modifier=0.0,
                )
                db.add(option)
                print(f"  + Type option: {type_data['name']}")
        
        # Add mockup images
        for idx, image_url in enumerate(product_data['mockup_images']):
            mockup = ProductMockupImage(
                product_id=product.id,
                image_url=image_url,
                display_order=idx,
            )
            db.add(mockup)
            print(f"  + Mockup image {idx + 1}")
        
        db.commit()
        print(f"✓ Created product: {product.name} (ID: {product.id})")
    
    print(f"\n✅ Successfully seeded {len(products_data)} products!")
    
    # Print summary
    print("\n" + "="*60)
    print("PRODUCTS SUMMARY")
    print("="*60)
    for product_data in products_data:
        print(f"• {product_data['name']} ({product_data['product_type']})")
        print(f"  Base Price: ₹{product_data['base_price']}")
        print(f"  Size Options: {len(product_data['sizes'])}")
        if product_data['types']:
            print(f"  Type Options: {len(product_data['types'])}")
        print(f"  Mockup Images: {len(product_data['mockup_images'])}")
        print()


def main():
    """Main function to run the seeding."""
    db = SessionLocal()
    try:
        seed_products(db)
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
