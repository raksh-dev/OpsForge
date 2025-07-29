#!/bin/bash

# Backup script for AI Operations Agent

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="ai_ops_backup_$TIMESTAMP"

echo "🔄 Starting backup..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
echo "📦 Backing up database..."
docker-compose exec -T postgres pg_dump -U $DB_USER $DB_NAME > "$BACKUP_DIR/${BACKUP_NAME}_db.sql"

# Backup environment file
cp .env "$BACKUP_DIR/${BACKUP_NAME}.env"

# Create tarball
tar -czf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" -C "$BACKUP_DIR" "${BACKUP_NAME}_db.sql" "${BACKUP_NAME}.env"

# Clean up individual files
rm "$BACKUP_DIR/${BACKUP_NAME}_db.sql" "$BACKUP_DIR/${BACKUP_NAME}.env"

echo "✅ Backup completed: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"