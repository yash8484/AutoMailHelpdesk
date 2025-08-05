#!/bin/bash

# AutoMailHelpdesk Database Migration Script
# This script applies Alembic migrations to the database.

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Logging
log() {
    echo "[$(date "+%Y-%m-%d %H:%M:%S")] $1" >&2
}

error() {
    log "ERROR: $1"
    exit 1
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."
    if ! command -v alembic &> /dev/null; then
        error "Alembic is required but not installed. Please install it via pip (pip install alembic)"
    fi
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed."
    fi
}

# Apply migrations
apply_migrations() {
    log "Applying database migrations..."
    
    # Ensure we are in the project root to run alembic
    pushd "$PROJECT_DIR" > /dev/null
    
    # Run alembic upgrade head
    # TODO: Ensure DATABASE_URL is correctly set in the environment for alembic
    alembic upgrade head
    
    popd > /dev/null
    log "Database migrations applied successfully."
}

# Main execution
main() {
    log "Starting database migration process..."
    
    check_dependencies
    apply_migrations
    
    log "Database migration process completed."
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--help]"
        echo ""
        echo "This script applies Alembic database migrations."
        echo "Ensure DATABASE_URL environment variable is set."
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac


