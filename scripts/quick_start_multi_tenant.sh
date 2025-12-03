#!/bin/bash
# Quick Start Script for Multi-Tenant Setup
# This script initializes the database and runs tests

set -e  # Exit on error

echo "🚀 Multi-Tenant Quick Start"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the photo_proof_api directory"
    exit 1
fi

# Step 1: Install dependencies
echo -e "${BLUE}📦 Step 1: Checking Python dependencies...${NC}"
if command -v pip &> /dev/null; then
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  pip not found, skipping dependency install${NC}"
fi
echo ""

# Step 2: Initialize database
echo -e "${BLUE}🔨 Step 2: Initializing multi-tenant database...${NC}"
python scripts/init_multi_tenant_db.py
echo ""

# Step 3: Run tests
echo -e "${BLUE}🧪 Step 3: Running multi-tenant tests...${NC}"
python scripts/test_multi_tenant.py
echo ""

# Step 4: Setup /etc/hosts
echo -e "${BLUE}📝 Step 4: Setting up local domains...${NC}"
echo -e "${YELLOW}You need to add these domains to /etc/hosts:${NC}"
echo ""
echo "127.0.0.1 demo.photoapp.local"
echo "127.0.0.1 alpha.photoapp.local"
echo "127.0.0.1 beta.photoapp.local"
echo "127.0.0.1 gamma.photoapp.local"
echo ""
echo -e "${YELLOW}Run this command:${NC}"
echo ""
echo "sudo tee -a /etc/hosts << 'EOF'"
echo "127.0.0.1 demo.photoapp.local"
echo "127.0.0.1 alpha.photoapp.local"
echo "127.0.0.1 beta.photoapp.local"
echo "127.0.0.1 gamma.photoapp.local"
echo "EOF"
echo ""

# Ask if user wants to add domains
read -p "Add domains to /etc/hosts automatically? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Adding domains to /etc/hosts (requires sudo)...${NC}"
    sudo tee -a /etc/hosts << 'EOF'
127.0.0.1 demo.photoapp.local
127.0.0.1 alpha.photoapp.local
127.0.0.1 beta.photoapp.local
127.0.0.1 gamma.photoapp.local
EOF
    echo -e "${GREEN}✅ Domains added${NC}"
else
    echo -e "${YELLOW}⏭️  Skipped - add manually when ready${NC}"
fi
echo ""

# Step 5: Instructions
echo "================================"
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "================================"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo ""
echo "1. Start the API server:"
echo "   ${YELLOW}python main.py${NC}"
echo ""
echo "2. Test tenant detection:"
echo "   ${YELLOW}curl -H 'Host: demo.photoapp.local' http://localhost:8000/api/health${NC}"
echo ""
echo "3. Get studio theme:"
echo "   ${YELLOW}curl -H 'Host: alpha.photoapp.local' http://localhost:8000/api/studio/current${NC}"
echo ""
echo "4. View API docs:"
echo "   ${YELLOW}http://localhost:8000/docs${NC}"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "   - MULTI_TENANT_IMPLEMENTATION.md - Complete guide"
echo "   - scripts/README.md - Scripts documentation"
echo ""
echo -e "${GREEN}Happy multi-tenanting! 🏢${NC}"
