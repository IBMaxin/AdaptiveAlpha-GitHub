 pretty formamted
 #!/bin/bash
# LLM Server Health Check Script
# Verifies configuration and performs basic health checks

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Performing LLM Server Health Check..."

# Check if required environment variables are set
check_env() {
    local var_name=$1
    local default_value=$2
    
    if [[ -z "${!var_name:-}" ]]; then
        echo -e "${YELLOW}⚠️  $var_name not set, using default: $default_value${NC}"
    else
        echo -e "${GREEN}✓ $var_name is set${NC}"
    fi
}

# Check API endpoint
check_endpoint() {
    local endpoint=${OPENAI_API_BASE:-http://localhost:11434/v1}
    echo "📡 Testing endpoint: $endpoint"
    
    if curl -s -m 5 "$endpoint/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Endpoint is responding${NC}"
    else
        echo -e "${RED}❌ Endpoint is not accessible${NC}"
        return 1
    fi
}

# Check model availability
check_model() {
    local model=${MODEL_NAME:-codellama:13b}
    echo "🤖 Checking model: $model"
    
    # Simple test prompt
    local test_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"test\"}]}" \
        "${OPENAI_API_BASE:-http://localhost:11434/v1}/chat/completions")
    
    if [[ $test_response == *"error"* ]]; then
        echo -e "${RED}❌ Model test failed${NC}"
        return 1
    else
        echo -e "${GREEN}✓ Model is responding${NC}"
    fi
}

# Check system resources
check_resources() {
    echo "💻 Checking system resources..."
    
    # Memory check
    local available_mem=$(free -m | awk '/Mem:/ {print $7}')
    local required_mem=${MEMORY_LIMIT:-8192}
    
    if [[ $available_mem -lt $required_mem ]]; then
        echo -e "${RED}❌ Insufficient memory: ${available_mem}MB available, ${required_mem}MB required${NC}"
    else
        echo -e "${GREEN}✓ Memory OK: ${available_mem}MB available${NC}"
    fi
    
    # CPU load check
    local cpu_load=$(uptime | awk -F'load average:' '{ print $2 }' | cut -d, -f1)
    if (( $(echo "$cpu_load > 0.8" | bc -l) )); then
        echo -e "${YELLOW}⚠️  High CPU load: $cpu_load${NC}"
    else
        echo -e "${GREEN}✓ CPU load OK: $cpu_load${NC}"
    fi
}

# Main health check
main() {
    echo "==== LLM Server Health Check $(date) ===="
    
    # Check environment variables
    check_env "OPENAI_API_BASE" "http://localhost:11434/v1"
    check_env "MODEL_NAME" "codellama:13b"
    check_env "MAX_TOKENS" "4096"
    check_env "TEMPERATURE" "0.2"
    
    # Perform checks
    check_endpoint || echo -e "${YELLOW}⚠️  Endpoint check failed${NC}"
    check_model || echo -e "${YELLOW}⚠️  Model check failed${NC}"
    check_resources
    
    echo "==== Health Check Complete ===="
}

main "$@"