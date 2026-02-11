#!/bin/bash
set -e

# Database Backup Script for Kupi Slona Production
# This script creates a backup of the PostgreSQL database

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="${PROJECT_DIR:-/root/kupi_slona}"
ENV_FILE="${ENV_FILE:-$PROJECT_DIR/.env.slon.prvms.ru}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Kupi Slona Database Backup ===${NC}"
echo "Started at: $(date)"

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}Creating backup directory: $BACKUP_DIR${NC}"
    mkdir -p "$BACKUP_DIR"
fi

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    echo -e "${GREEN}✓ Environment file loaded${NC}"
else
    echo -e "${RED}ERROR: Environment file not found: $ENV_FILE${NC}"
    exit 1
fi

# Set defaults if not in env
DB_NAME="${DB_NAME:-elephant_shop}"
DB_USER="${DB_USER:-postgres}"
CONTAINER_NAME="${CONTAINER_NAME:-kupi_slona-db-1}"

# Check if database container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}ERROR: Database container $CONTAINER_NAME is not running${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Database container is running${NC}"

# Create backup filename
BACKUP_FILE="$BACKUP_DIR/kupi_slona_$TIMESTAMP.sql.gz"

# Perform backup
echo -e "${YELLOW}Creating backup...${NC}"
if docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"; then
    # Get backup size
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ Backup completed successfully: $BACKUP_FILE ($SIZE)${NC}"

    # Create a 'latest' symlink
    LATEST_LINK="$BACKUP_DIR/kupi_slona_latest.sql.gz"
    ln -sf "$(basename $BACKUP_FILE)" "$LATEST_LINK"
    echo -e "${GREEN}✓ Latest backup link updated${NC}"
else
    echo -e "${RED}ERROR: Backup failed${NC}"
    exit 1
fi

# Clean up old backups
echo -e "${YELLOW}Cleaning up old backups (retention: $RETENTION_DAYS days)...${NC}"
DELETED_COUNT=$(find "$BACKUP_DIR" -name "kupi_slona_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
echo -e "${GREEN}✓ Removed $DELETED_COUNT old backup(s)${NC}"

# List recent backups
echo -e "${YELLOW}Recent backups:${NC}"
ls -lh "$BACKUP_DIR"/kupi_slona_*.sql.gz | tail -5

# Optional: Upload to S3 or remote storage
# Uncomment and configure if you have remote backup storage
# if command -v aws &> /dev/null; then
#     echo -e "${YELLOW}Uploading to S3...${NC}"
#     aws s3 cp "$BACKUP_FILE" "s3://your-backup-bucket/kupi_slona/" --storage-class STANDARD_IA
#     echo -e "${GREEN}✓ Uploaded to S3${NC}"
# fi

echo -e "${GREEN}=== Backup completed ===${NC}"
echo "Finished at: $(date)"
exit 0
