#!/bin/bash

echo "=========================================="
echo "Verifying Backend_v4 Merge"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check function
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (missing)"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (missing)"
        return 1
    fi
}

cd ~/SanHark_25_02/backend

echo "1. Checking Crawler Modules..."
check_dir "chat/crawler_modules"
check_file "chat/crawler_modules/crawler_precedent.py"
check_file "chat/crawler_modules/crawler_law_rlt.py"
check_file "chat/crawler_modules/crawler_term.py"
check_file "chat/crawler_modules/law_api_config.py"
check_file "chat/crawler_modules/data_models.py"
echo ""

echo "2. Checking Management Commands..."
check_dir "chat/management"
check_dir "chat/management/commands"
check_file "chat/management/commands/export_and_clean_logs.py"
echo ""

echo "3. Checking Core Files..."
check_file "chat/__init__.py"
check_file "chat/apps.py"
check_file "chat/data_processor.py"
check_file "db_search.py"
echo ""

echo "4. Checking Scripts..."
check_dir "scripts"
check_file "scripts/index_data.py"
echo ""

echo "5. Checking Logs Directory..."
check_dir "chat/logs"
echo ""

echo "6. Checking Configuration..."
check_file ".env"
if grep -q "LAW_API_KEY" .env; then
    echo -e "${GREEN}✓${NC} LAW_API_KEY found in .env"
else
    echo -e "${RED}✗${NC} LAW_API_KEY missing in .env"
fi
echo ""

echo "7. Checking Documentation..."
cd ~/SanHark_25_02
check_file "MERGE_SUMMARY.md"
check_file "QUICKSTART_MERGED.md"
echo ""

echo "8. Checking Python Imports..."
cd ~/SanHark_25_02/backend
python3 << EOF
import sys
sys.path.insert(0, '.')

errors = []

try:
    from chat.crawler_modules import crawler_precedent
    print("${GREEN}✓${NC} crawler_precedent imports successfully")
except Exception as e:
    print("${RED}✗${NC} crawler_precedent import failed:", str(e))
    errors.append("crawler_precedent")

try:
    from chat import apps
    print("${GREEN}✓${NC} chat.apps imports successfully")
except Exception as e:
    print("${RED}✗${NC} chat.apps import failed:", str(e))
    errors.append("apps")

try:
    from chat import data_processor
    print("${GREEN}✓${NC} data_processor imports successfully")
except Exception as e:
    print("${RED}✗${NC} data_processor import failed:", str(e))
    errors.append("data_processor")

if errors:
    print("\n${RED}Some imports failed. Check dependencies.${NC}")
    sys.exit(1)
else:
    print("\n${GREEN}All imports successful!${NC}")
EOF

echo ""
echo "=========================================="
echo "Verification Complete!"
echo "=========================================="
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Run: cd ~/SanHark_25_02/backend && python manage.py migrate"
echo "2. Run: python manage.py runserver"
echo "3. Check for initialization messages"
echo "4. Test crawler: python manage.py shell"
echo "5. Read QUICKSTART_MERGED.md for detailed instructions"
echo ""
