#!/bin/bash
# LLM Server Maintenance Script
# Performs routine maintenance tasks and cleanup

set -euo pipefail

# Configuration
LOG_DIR="logs"
BACKUP_DIR="backups"
MAX_LOG_AGE=30  # days
MAINTENANCE_LOG="${LOG_DIR}/maintenance.log"

# Ensure directories exist
mkdir -p "$LOG_DIR" "$BACKUP_DIR"

# Logging function
log() {
    local message=$1
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "${timestamp} ${message}" | tee -a "$MAINTENANCE_LOG"
}

# Backup configuration
backup_config() {
    log "Starting configuration backup..."
    local backup_file="${BACKUP_DIR}/config-$(date +%Y%m%d).tar.gz"
    
    tar -czf "$backup_file" .continue/mcpServers/*.yaml
    
    if [ $? -eq 0 ]; then
        log "✓ Configuration backup created: $backup_file"
    else
        log "❌ Configuration backup failed"
        return 1
    fi
}

# Clean old log files
cleanup_logs() {
    log "Starting log cleanup..."
    local count=0
    
    # Find and remove old log files
    while IFS= read -r file; do
        rm "$file"
        count=$((count + 1))
    done < <(find "$LOG_DIR" -name "*.log.*" -type f -mtime +${MAX_LOG_AGE})
    
    log "✓ Removed ${count} old log files"
}

# Rotate current logs
rotate_logs() {
    log "Starting log rotation..."
    
    # Force Python logger rotation
    if [ -f "scripts/llm_logger.py" ]; then
        python3 -c "
from llm_logger import LLMLogger
logger = LLMLogger()
logger.rotate_logs()
"
    fi
    
    log "✓ Logs rotated"
}

# Check and clean temporary files
cleanup_temp() {
    log "Cleaning temporary files..."
    local temp_dir="/tmp"
    local pattern="llm-*"
    
    # Remove temp files older than 24 hours
    find "$temp_dir" -name "$pattern" -type f -mtime +1 -delete
    
    log "✓ Temporary files cleaned"
}

# Generate maintenance report
generate_report() {
    local report_file="${LOG_DIR}/maintenance-report-$(date +%Y%m%d).txt"
    
    {
        echo "=== LLM Server Maintenance Report ==="
        echo "Date: $(date)"
        echo
        echo "1. Disk Usage"
        df -h .
        echo
        echo "2. Log Directory Size"
        du -sh "$LOG_DIR"
        echo
        echo "3. Recent Errors"
        tail -n 50 "${LOG_DIR}/error.log" 2>/dev/null || echo "No recent errors"
        echo
        echo "4. System Status"
        uptime
        echo
        echo "=== End Report ==="
    } > "$report_file"
    
    log "✓ Maintenance report generated: $report_file"
}

# Main maintenance routine
main() {
    log "=== Starting maintenance $(date) ==="
    
    # Run maintenance tasks
    backup_config
    cleanup_logs
    rotate_logs
    cleanup_temp
    generate_report
    
    log "=== Maintenance complete ==="
}

main "$@"#!/bin/bash
# LLM Server Maintenance Script
# Performs routine maintenance tasks and cleanup

set -euo pipefail

# Configuration
LOG_DIR="logs"
BACKUP_DIR="backups"
MAX_LOG_AGE=30  # days
MAINTENANCE_LOG="${LOG_DIR}/maintenance.log"

# Ensure directories exist
mkdir -p "$LOG_DIR" "$BACKUP_DIR"

# Logging function
log() {
    local message=$1
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "${timestamp} ${message}" | tee -a "$MAINTENANCE_LOG"
}

# Backup configuration
backup_config() {
    log "Starting configuration backup..."
    local backup_file="${BACKUP_DIR}/config-$(date +%Y%m%d).tar.gz"
    
    tar -czf "$backup_file" .continue/mcpServers/*.yaml
    
    if [ $? -eq 0 ]; then
        log "✓ Configuration backup created: $backup_file"
    else
        log "❌ Configuration backup failed"
        return 1
    fi
}

# Clean old log files
cleanup_logs() {
    log "Starting log cleanup..."
    local count=0
    
    # Find and remove old log files
    while IFS= read -r file; do
        rm "$file"
        count=$((count + 1))
    done < <(find "$LOG_DIR" -name "*.log.*" -type f -mtime +${MAX_LOG_AGE})
    
    log "✓ Removed ${count} old log files"
}

# Rotate current logs
rotate_logs() {
    log "Starting log rotation..."
    
    # Force Python logger rotation
    if [ -f "scripts/llm_logger.py" ]; then
        python3 -c "
from llm_logger import LLMLogger
logger = LLMLogger()
logger.rotate_logs()
"
    fi
    
    log "✓ Logs rotated"
}

# Check and clean temporary files
cleanup_temp() {
    log "Cleaning temporary files..."
    local temp_dir="/tmp"
    local pattern="llm-*"
    
    # Remove temp files older than 24 hours
    find "$temp_dir" -name "$pattern" -type f -mtime +1 -delete
    
    log "✓ Temporary files cleaned"
}

# Generate maintenance report
generate_report() {
    local report_file="${LOG_DIR}/maintenance-report-$(date +%Y%m%d).txt"
    
    {
        echo "=== LLM Server Maintenance Report ==="
        echo "Date: $(date)"
        echo
        echo "1. Disk Usage"
        df -h .
        echo
        echo "2. Log Directory Size"
        du -sh "$LOG_DIR"
        echo
        echo "3. Recent Errors"
        tail -n 50 "${LOG_DIR}/error.log" 2>/dev/null || echo "No recent errors"
        echo
        echo "4. System Status"
        uptime
        echo
        echo "=== End Report ==="
    } > "$report_file"
    
    log "✓ Maintenance report generated: $report_file"
}

# Main maintenance routine
main() {
    log "=== Starting maintenance $(date) ==="
    
    # Run maintenance tasks
    backup_config
    cleanup_logs
    rotate_logs
    cleanup_temp
    generate_report
    
    log "=== Maintenance complete ==="
}

main "$@"