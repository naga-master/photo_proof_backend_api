"""Check existing data in database"""

from app.db.session import SessionLocal
from app.db import models

db = SessionLocal()

print(f'Projects: {db.query(models.Project).count()}')
print(f'Clients: {db.query(models.Client).count()}')
print(f'Service Packages: {db.query(models.ServicePackage).count()}')
print(f'Users: {db.query(models.User).count()}')
print()

print('--- Sample Projects ---')
for p in db.query(models.Project).limit(5).all():
    print(f'{p.id} - {p.name} (status: {p.status}, client_id: {p.client_id})')

print()
print('--- Sample Clients ---')
for c in db.query(models.Client).limit(5).all():
    print(f'{c.id} - {c.name} ({c.email})')

print()
print('--- Sample Packages ---')
for pkg in db.query(models.ServicePackage).limit(5).all():
    print(f'{pkg.id} - {pkg.name} (${pkg.price})')

db.close()
