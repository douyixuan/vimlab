#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions for logging
log() {
    echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S')${NC} - $1"
}

log_section() {
    echo -e "\n${YELLOW}========== $1 ==========${NC}"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to execute a command with proper logging
run_command() {
    local command=$1
    
    echo "+ $command"
    eval $command
}

# Error handling
set -e
trap 'log_error "An error occurred. Exiting..."; exit 1' ERR

# Main build process
WORKDIR=$(pwd)
log "Working directory: $WORKDIR"

# Read commands from file
COMMANDS_FILE="make"

# Check if commands file exists, create with default commands if not
if [ ! -f "$COMMANDS_FILE" ]; then
    cat > "$COMMANDS_FILE" << 'EOF'
#!/bin/bash

# STAGE: Prepare Build Environment
mkdir -p build && cd build

# STAGE: Configure
cmake -DCMAKE_INSTALL_PREFIX=${WORKDIR}/../out ${WORKDIR}

# STAGE: Build
make -j8

# STAGE: Install
make install
EOF
    chmod +x "$COMMANDS_FILE"
    log "Created default commands file at $COMMANDS_FILE"
fi

# Process commands by stage
current_stage=""
commands=()

while read -r line || [ -n "$line" ]; do
    # Skip empty lines
    [[ -z "$line" ]] && continue
    
    # Check if this is a stage header
    if [[ "$line" =~ ^#\ STAGE:\ (.*)$ ]]; then
        # If we have commands in the current stage, run them
        if [ -n "$current_stage" ] && [ ${#commands[@]} -gt 0 ]; then
            log_section "$current_stage"
            for cmd in "${commands[@]}"; do
                run_command "$cmd"
            done
            log_success "$current_stage completed"
        fi
        
        # Start a new stage
        current_stage="${BASH_REMATCH[1]}"
        commands=()
    # Skip other comments
    elif [[ "$line" =~ ^# ]]; then
        continue
    else
        # Add command to current stage
        commands+=("$line")
    fi
done < "$COMMANDS_FILE"

# Process the last stage if there are commands
if [ -n "$current_stage" ] && [ ${#commands[@]} -gt 0 ]; then
    log_section "$current_stage"
    for cmd in "${commands[@]}"; do
        run_command "$cmd"
    done
    log_success "$current_stage completed"
fi

log_section "Build Process Completed Successfully"
