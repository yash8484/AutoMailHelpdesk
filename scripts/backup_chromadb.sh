#!/bin/bash

# AutoMailHelpdesk ChromaDB Backup Script
# This script creates backups of ChromaDB data and uploads them to cloud storage

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-/tmp/chromadb_backups}"
CHROMADB_DATA_DIR="${CHROMADB_DATA_DIR:-/app/chroma/data}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="chromadb_backup_${TIMESTAMP}"

# Cloud storage configuration (set via environment variables)
S3_BUCKET="${S3_BUCKET:-}"
GCS_BUCKET="${GCS_BUCKET:-}"
AZURE_CONTAINER="${AZURE_CONTAINER:-}"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
}

error() {
    log "ERROR: $1"
    exit 1
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    if ! command -v tar &> /dev/null; then
        error "tar is required but not installed"
    fi
    
    if ! command -v gzip &> /dev/null; then
        error "gzip is required but not installed"
    fi
    
    # Check cloud storage tools
    if [[ -n "$S3_BUCKET" ]] && ! command -v aws &> /dev/null; then
        error "aws CLI is required for S3 uploads but not installed"
    fi
    
    if [[ -n "$GCS_BUCKET" ]] && ! command -v gsutil &> /dev/null; then
        error "gsutil is required for GCS uploads but not installed"
    fi
    
    if [[ -n "$AZURE_CONTAINER" ]] && ! command -v az &> /dev/null; then
        error "Azure CLI is required for Azure uploads but not installed"
    fi
}

# Create backup directory
create_backup_dir() {
    log "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
}

# Backup ChromaDB data
backup_chromadb() {
    log "Starting ChromaDB backup..."
    
    if [[ ! -d "$CHROMADB_DATA_DIR" ]]; then
        error "ChromaDB data directory not found: $CHROMADB_DATA_DIR"
    fi
    
    local backup_path="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    
    log "Creating compressed archive: $backup_path"
    tar -czf "$backup_path" -C "$(dirname "$CHROMADB_DATA_DIR")" "$(basename "$CHROMADB_DATA_DIR")"
    
    if [[ ! -f "$backup_path" ]]; then
        error "Backup file was not created: $backup_path"
    fi
    
    local backup_size=$(du -h "$backup_path" | cut -f1)
    log "Backup created successfully: $backup_path (Size: $backup_size)"
    
    echo "$backup_path"
}

# Upload to S3
upload_to_s3() {
    local backup_path="$1"
    
    if [[ -z "$S3_BUCKET" ]]; then
        log "S3_BUCKET not configured, skipping S3 upload"
        return
    fi
    
    log "Uploading backup to S3: s3://$S3_BUCKET/"
    
    aws s3 cp "$backup_path" "s3://$S3_BUCKET/chromadb_backups/" \
        --storage-class STANDARD_IA \
        --metadata "backup_date=$(date -u +%Y-%m-%dT%H:%M:%SZ),retention_days=$RETENTION_DAYS"
    
    log "S3 upload completed"
}

# Upload to Google Cloud Storage
upload_to_gcs() {
    local backup_path="$1"
    
    if [[ -z "$GCS_BUCKET" ]]; then
        log "GCS_BUCKET not configured, skipping GCS upload"
        return
    fi
    
    log "Uploading backup to GCS: gs://$GCS_BUCKET/"
    
    gsutil -m cp "$backup_path" "gs://$GCS_BUCKET/chromadb_backups/"
    
    log "GCS upload completed"
}

# Upload to Azure Blob Storage
upload_to_azure() {
    local backup_path="$1"
    
    if [[ -z "$AZURE_CONTAINER" ]]; then
        log "AZURE_CONTAINER not configured, skipping Azure upload"
        return
    fi
    
    log "Uploading backup to Azure: $AZURE_CONTAINER"
    
    az storage blob upload \
        --file "$backup_path" \
        --container-name "$AZURE_CONTAINER" \
        --name "chromadb_backups/$(basename "$backup_path")" \
        --tier Cool
    
    log "Azure upload completed"
}

# Clean up old local backups
cleanup_local_backups() {
    log "Cleaning up local backups older than $RETENTION_DAYS days..."
    
    find "$BACKUP_DIR" -name "chromadb_backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
    
    local remaining_count=$(find "$BACKUP_DIR" -name "chromadb_backup_*.tar.gz" -type f | wc -l)
    log "Local cleanup completed. Remaining backups: $remaining_count"
}

# Clean up old cloud backups
cleanup_cloud_backups() {
    # S3 cleanup
    if [[ -n "$S3_BUCKET" ]]; then
        log "Cleaning up old S3 backups..."
        aws s3 ls "s3://$S3_BUCKET/chromadb_backups/" | \
            awk '{print $4}' | \
            while read -r file; do
                if [[ -n "$file" ]]; then
                    # Extract date from filename and check if older than retention period
                    file_date=$(echo "$file" | grep -oE '[0-9]{8}' | head -1)
                    if [[ -n "$file_date" ]]; then
                        cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%Y%m%d)
                        if [[ "$file_date" -lt "$cutoff_date" ]]; then
                            log "Deleting old S3 backup: $file"
                            aws s3 rm "s3://$S3_BUCKET/chromadb_backups/$file"
                        fi
                    fi
                fi
            done
    fi
    
    # GCS cleanup (using lifecycle policies is recommended instead)
    if [[ -n "$GCS_BUCKET" ]]; then
        log "Note: Consider setting up lifecycle policies for GCS bucket: $GCS_BUCKET"
    fi
    
    # Azure cleanup (using lifecycle policies is recommended instead)
    if [[ -n "$AZURE_CONTAINER" ]]; then
        log "Note: Consider setting up lifecycle policies for Azure container: $AZURE_CONTAINER"
    fi
}

# Verify backup integrity
verify_backup() {
    local backup_path="$1"
    
    log "Verifying backup integrity..."
    
    if tar -tzf "$backup_path" > /dev/null 2>&1; then
        log "Backup integrity verified successfully"
    else
        error "Backup integrity check failed"
    fi
}

# Send notification
send_notification() {
    local status="$1"
    local message="$2"
    
    # Slack notification
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"ChromaDB Backup $status: $message\"}" \
            "$SLACK_WEBHOOK_URL" > /dev/null 2>&1 || true
    fi
    
    # Email notification (requires mailutils or similar)
    if [[ -n "${NOTIFICATION_EMAIL:-}" ]] && command -v mail &> /dev/null; then
        echo "$message" | mail -s "ChromaDB Backup $status" "$NOTIFICATION_EMAIL" || true
    fi
}

# Main execution
main() {
    log "Starting ChromaDB backup process..."
    
    # Trap errors and send notification
    trap 'send_notification "FAILED" "ChromaDB backup failed at $(date)"' ERR
    
    check_dependencies
    create_backup_dir
    
    # Create backup
    backup_path=$(backup_chromadb)
    
    # Verify backup
    verify_backup "$backup_path"
    
    # Upload to cloud storage
    upload_to_s3 "$backup_path"
    upload_to_gcs "$backup_path"
    upload_to_azure "$backup_path"
    
    # Cleanup old backups
    cleanup_local_backups
    cleanup_cloud_backups
    
    log "ChromaDB backup process completed successfully"
    send_notification "SUCCESS" "ChromaDB backup completed successfully at $(date). Backup: $(basename "$backup_path")"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--help]"
        echo ""
        echo "Environment variables:"
        echo "  BACKUP_DIR          - Local backup directory (default: /tmp/chromadb_backups)"
        echo "  CHROMADB_DATA_DIR   - ChromaDB data directory (default: /app/chroma/data)"
        echo "  RETENTION_DAYS      - Backup retention in days (default: 30)"
        echo "  S3_BUCKET           - S3 bucket for backups (optional)"
        echo "  GCS_BUCKET          - GCS bucket for backups (optional)"
        echo "  AZURE_CONTAINER     - Azure container for backups (optional)"
        echo "  SLACK_WEBHOOK_URL   - Slack webhook for notifications (optional)"
        echo "  NOTIFICATION_EMAIL  - Email for notifications (optional)"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac

