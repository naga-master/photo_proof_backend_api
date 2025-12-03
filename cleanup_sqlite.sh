#!/bin/bash
# SQLite Cleanup Script - Remove all SQLite references and files
# This system is now PostgreSQL-only

set -e

echo "🧹 Cleaning up SQLite references and files..."

# Navigate to project root
cd "$(dirname "$0")"

# Remove SQLite database files
echo "📁 Removing SQLite database files..."
find . -name "*.db" -type f -not -path "./node_modules/*" -not -path "./venv/*" -exec rm -v {} \;
find . -name "*.sqlite" -type f -not -path "./node_modules/*" -not -path "./venv/*" -exec rm -v {} \;
find . -name "*.sqlite3" -type f -not -path "./node_modules/*" -not -path "./venv/*" -exec rm -v {} \;

# Remove SQLite migration scripts (keep PostgreSQL ones)
echo "📁 Removing SQLite-specific migration scripts..."
rm -rfv scripts/sqlite_to_postgres_migration/ 2>/dev/null || true

# List remaining SQLite references in code (for manual review)
echo ""
echo "📝 Checking for remaining SQLite references in code..."
echo "   (These may need manual review):"
grep -r "sqlite" --include="*.py" --exclude-dir=venv --exclude-dir=node_modules . 2>/dev/null | grep -v "^Binary" | head -20 || echo "   ✅ No SQLite references found in Python files"

echo ""
echo "✅ SQLite cleanup complete!"
echo ""
echo "📊 System is now PostgreSQL-only"
echo "   Database: photo_proof_production"
echo "   User: photo_proof_user"
echo ""
