#!/usr/bin/env python3
"""
Seed products into the database
"""
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Product, ProductOption

def seed_products():
    """Seed products into database"""
    db: Session = SessionLocal()
    
    try:
        # Clear existing products
        print("Clearing existing products...")
        db.query(ProductOption).delete()
        db.query(Product).delete()
        db.commit()
        
        products_data = [
            {
                'id': 'prints',
                'name': 'Lustre Print',
                'short_description': 'Professional quality prints with a subtle sheen.',
                'detailed_description': 'Our Lustre Prints are a classic choice, offering the color saturation of a glossy finish with the fingerprint resistance of matte. Printed on archival quality paper, these prints are designed to last a lifetime.',
                'specs': {
                    'Paper Type': 'Kodak Endura Professional',
                    'Finish': 'Lustre (Semi-Matte)',
                    'Archival Quality': '100+ years',
                },
                'mockup_images': [
                    'data/images/lustre_print.jpg',
                ],
                'sizes': [
                    ('4x6', 10),
                    ('5x7', 20),
                    ('8x10', 30),
                    ('11x14', 40),
                    ('16x20', 60),
                    ('20x30', 85),
                ],
                'types': [
                    ('Lustre', 0),
                    ('Glossy', 5),
                    ('Deep Matte', 5),
                ],
            },
            {
                'id': 'fine-art',
                'name': 'Fine Art Print',
                'short_description': 'Museum-quality prints on textured, heavyweight paper.',
                'detailed_description': 'Elevate your photos with our Fine Art Prints. Using archival inks on acid-free, textured paper, these prints offer exceptional image permanence and a stunning, artistic feel.',
                'specs': {
                    'Paper Type': 'Archival Matte or Textured Rag',
                    'Inks': 'Pigment-based archival inks',
                    'Weight': '310 gsm',
                },
                'mockup_images': [
                    'data/images/fine_art.jpg',
                ],
                'sizes': [
                    ('11x14', 90),
                    ('16x20', 120),
                    ('20x30', 150),
                ],
                'types': [],
            },
            {
                'id': 'digitals',
                'name': 'Digital File',
                'short_description': 'High-resolution digital downloads of your photos.',
                'detailed_description': 'Get a high-resolution digital copy of your favorite photos, perfect for sharing online, printing on your own, or for archival purposes. Delivered instantly via email.',
                'specs': {
                    'Resolution': '300 DPI JPEG',
                    'Delivery': 'Instant Download',
                    'License': 'Personal Use',
                },
                'mockup_images': [
                    'data/images/digital_file.jpg',
                ],
                'sizes': [
                    ('Single Photo', 25),
                    ('Full Gallery', 500),
                ],
                'types': [],
            },
            {
                'id': 'canvases',
                'name': 'Gallery Wrapped Canvas',
                'short_description': 'A timeless, ready-to-hang piece of art.',
                'detailed_description': 'Your photo is printed on high-quality canvas and stretched over a sturdy wooden frame. With a classic gallery wrap, this piece is ready to hang and admire right out of the box.',
                'specs': {
                    'Material': 'Archival-grade canvas',
                    'Frame': '1.5" deep solid wood',
                    'Finish': 'Protective UV-resistant coating',
                },
                'mockup_images': [
                    'data/images/gellery_wrapped_canvas.webp',
                ],
                'sizes': [
                    ('16x20', 150),
                    ('24x36', 250),
                ],
                'types': [],
            },
            {
                'id': 'metal',
                'name': 'Metal Print',
                'short_description': 'Vibrant, high-gloss prints on a sleek aluminum panel.',
                'detailed_description': 'Make your images pop with a Metal Print. Your photo is infused directly into a sheet of aluminum for a brilliant, durable, and modern display. Comes with a float mount for a stunning wall presentation.',
                'specs': {
                    'Material': 'Dye-infused Aluminum',
                    'Finish': 'High Gloss',
                    'Features': 'Waterproof, scratch-resistant',
                },
                'mockup_images': [
                    'data/images/metal_print.webp',
                ],
                'sizes': [
                    ('16x20', 220),
                    ('24x36', 350),
                ],
                'types': [],
            },
            {
                'id': 'albums',
                'name': 'Photo Album',
                'short_description': 'A beautiful, custom-designed album of your day.',
                'detailed_description': 'A handcrafted, lay-flat album featuring your selected images. Choose from a variety of cover materials and customization options to create a perfect heirloom.',
                'specs': {
                    'Pages': '20-50 thick, lay-flat pages',
                    'Cover': 'Linen or Leather options',
                    'Design': 'Custom layout included',
                },
                'mockup_images': [
                    'data/images/photo_album.webp',
                ],
                'sizes': [
                    ('10x10 Album', 800),
                ],
                'types': [],
            },
        ]
        
        for prod_data in products_data:
            print(f"\nCreating product: {prod_data['name']}")
            
            # Create product
            product = Product(
                id=prod_data['id'],
                name=prod_data['name'],
                short_description=prod_data['short_description'],
                detailed_description=prod_data['detailed_description'],
                specs=prod_data['specs'],
                mockup_images=prod_data['mockup_images'],
                is_active=True
            )
            db.add(product)
            db.flush()
            
            # Create size options
            for idx, (size_name, price) in enumerate(prod_data['sizes']):
                option = ProductOption(
                    product_id=product.id,
                    option_type='size',
                    name=size_name,
                    price=price,
                    order_index=idx,
                    is_active=True
                )
                db.add(option)
                print(f"  - Size: {size_name} (₹{price})")
            
            # Create type options
            for idx, (type_name, price_modifier) in enumerate(prod_data['types']):
                option = ProductOption(
                    product_id=product.id,
                    option_type='type',
                    name=type_name,
                    price=price_modifier,
                    order_index=idx,
                    is_active=True
                )
                db.add(option)
                print(f"  - Type: {type_name} (+₹{price_modifier})")
        
        db.commit()
        print("\n✅ Products seeded successfully!")
        
    except Exception as e:
        print(f"\n❌ Error seeding products: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_products()
