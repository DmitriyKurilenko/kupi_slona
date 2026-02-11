#!/bin/bash
set -e

# Database Restore Script for Kupi Slona Production
# This script restores a PostgreSQL database from a backup

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/postgres}"
PROJECT_DIR="${PROJECT_DIR:-/root/kupi_slona}"
ENV_FILE="${ENV_FILE:-$PROJECT_DIR/.env}"
COMPOSE_FILE="${COMPOSE_FILE:-$PROJECT_DIR/docker-compose.prod.yml}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Kupi Slona Database Restore ===${NC}"

# Check if backup file was provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <backup_file.sql.gz>${NC}"
    echo ""
    echo -e "${YELLOW}Available backups:${NC}"
    if [ -d "$BACKUP_DIR" ]; then
        ls -lh "$BACKUP_DIR"/kupi_slona_*.sql.gz 2>/dev/null || echo "No backups found"
    else
        echo "Backup directory not found: $BACKUP_DIR"
    fi
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    # Try prepending backup directory
    BACKUP_FILE="$BACKUP_DIR/$1"
    if [ ! -f "$BACKUP_FILE" ]; then
        echo -e "${RED}ERROR: Backup file not found: $1${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Backup file found: $BACKUP_FILE${NC}"
echo -e "${YELLOW}Backup size: $(du -h $BACKUP_FILE | cut -f1)${NC}"

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    echo -e "${GREEN}✓ Environment file loaded${NC}"
else
    echo -e "${RED}ERROR: Environment file not found: $ENV_FILE${NC}"
    exit 1
fi

# Set defaults
DB_NAME="${DB_NAME:-elephant_shop}"
DB_USER="${DB_USER:-postgres}"
CONTAINER_NAME="${CONTAINER_NAME:-kupi_slona-db-1}"

# Confirmation prompt
echo ""
echo -e "${RED}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║           ⚠️  WARNING: DESTRUCTIVE ACTION  ⚠️       ║${NC}"
echo -e "${RED}║                                                    ║${NC}"
echo -e "${RED}║  This will DROP and RECREATE the database!       ║${NC}"
echo -e "${RED}║  All current data will be LOST!                   ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Database: $DB_NAME${NC}"
echo -e "${YELLOW}Backup:   $BACKUP_FILE${NC}"
echo ""
read -p "Are you absolutely sure you want to continue? Type 'YES' to confirm: " CONFIRM

if [ "$CONFIRM" != "YES" ]; then
    echo -e "${YELLOW}Restore cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}Starting restore process...${NC}"

# Stop web and celery services to close database connections
echo -e "${YELLOW}Stopping web and celery services...${NC}"
if [ -f "$COMPOSE_FILE" ]; then
    docker-compose -f "$COMPOSE_FILE" stop web celery_worker
    echo -e "${GREEN}✓ Services stopped${NC}"
else
    echo -e "${RED}WARNING: docker-compose file not found, skipping service stop${NC}"
fi

# Wait a moment for connections to close
sleep 2

# Check if database container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}ERROR: Database container $CONTAINER_NAME is not running${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Database container is running${NC}"

# Drop and recreate database
echo -e "${YELLOW}Dropping and recreating database...${NC}"
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>&1
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;" 2>&1
echo -e "${GREEN}✓ Database recreated${NC}"

# Restore from backup
echo -e "${YELLOW}Restoring from backup (this may take a few minutes)...${NC}"
if gunzip -c "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"; then
    echo -e "${GREEN}✓ Database restored successfully${NC}"
else
    echo -e "${RED}ERROR: Restore failed${NC}"
    echo -e "${YELLOW}You may need to manually restore the database${NC}"
    exit 1
fi

# Restart services
echo -e "${YELLOW}Starting services...${NC}"
if [ -f "$COMPOSE_FILE" ]; then
    docker-compose -f "$COMPOSE_FILE" up -d web celery_worker
    echo -e "${GREEN}✓ Services started${NC}"
fi

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 5

# Verify the restoration
echo -e "${YELLOW}Verifying database...${NC}"
TABLE_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "0")
echo -e "${GREEN}✓ Tables found: $(echo $TABLE_COUNT | tr -d ' ')${NC}"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         ✓ Database restore completed!             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Verify the application is working: curl http://localhost:8000/health/"
echo "2. Check web logs: docker-compose -f $COMPOSE_FILE logs -f web"
echo "3. Test a few key features manually"
echo ""
exit 0
