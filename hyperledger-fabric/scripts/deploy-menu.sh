#!/bin/bash

#
# Interactive Deployment Menu for LGCSE Hyperledger Fabric
#
# This script provides an interactive menu to choose deployment configurations
# based on available system resources and user preferences.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    echo -e "${1}${2}${NC}"
}

# Function to print header
print_header() {
    clear
    print_color $BLUE "=================================================="
    print_color $BLUE "🚀 LGCSE Hyperledger Fabric Deployment Menu"
    print_color $BLUE "=================================================="
    echo ""
    print_color $WHITE "Welcome to the LGCSE Certificate Verification System!"
    print_color $WHITE "This menu will help you choose the optimal deployment configuration"
    print_color $WHITE "based on your laptop resources and requirements."
    echo ""
}

# Function to print section header
print_section() {
    echo ""
    print_color $CYAN "📊 $1"
    print_color $CYAN "$(printf '=%.0s' {80} '' | tr ' ' '=')"
}

# Function to check system resources
check_system_resources() {
    print_section "System Resource Analysis"
    
    # Get system information using Python script
    python3 scripts/resource-calculator.py > /tmp/resource_analysis.json 2>/dev/null
    
    if [ ! -f /tmp/resource_analysis.json ]; then
        print_color $RED "❌ Failed to analyze system resources"
        return 1
    fi
    
    # Parse resource analysis
    CPU_CORES=$(python3 -c "
import psutil
print(psutil.cpu_count(logical=False))
" 2>/dev/null)
    
    TOTAL_MEMORY=$(python3 -c "
import psutil
memory = psutil.virtual_memory()
print(f'{memory.total / (1024**3):.1f}')
" 2>/dev/null)
    
    AVAILABLE_MEMORY=$(python3 -c "
import psutil
memory = psutil.virtual_memory()
print(f'{memory.available / (1024**3):.1f}')
" 2>/dev/null)
    
    TOTAL_DISK=$(python3 -c "
import psutil
disk = psutil.disk_usage('/')
print(f'{disk.total / (1024**3):.1f}')
" 2>/dev/null)
    
    AVAILABLE_DISK=$(python3 -c "
import psutil
disk = psutil.disk_usage('/')
print(f'{disk.free / (1024**3):.1f}')
" 2>/dev/null)
    
    CPU_USAGE=$(python3 -c "
import psutil
print(f'{psutil.cpu_percent(interval=1):.1f}')
" 2>/dev/null)
    
    MEMORY_USAGE=$(python3 -c "
import psutil
memory = psutil.virtual_memory()
print(f'{memory.percent:.1f}')
" 2>/dev/null)
    
    # Display system resources
    print_color $WHITE "🖥️  System Information:"
    echo "   CPU Cores: $CPU_CORES (Usage: ${CPU_USAGE}%)"
    echo "   Memory: ${TOTAL_MEMORY}GB total, ${AVAILABLE_MEMORY}GB available (Usage: ${MEMORY_USAGE}%)"
    echo "   Disk: ${TOTAL_DISK}GB total, ${AVAILABLE_DISK}GB available"
    echo ""
    
    # Determine resource level
    if [ "$CPU_CORES" -lt 4 ] || [ "$(echo "$AVAILABLE_MEMORY < 6" | bc)" -eq 1 ]; then
        RESOURCE_LEVEL="low"
        print_color $YELLOW "⚠️  Resource Level: LOW (Limited resources detected)"
    elif [ "$CPU_CORES" -lt 8 ] || [ "$(echo "$AVAILABLE_MEMORY < 12" | bc)" -eq 1 ]; then
        RESOURCE_LEVEL="medium"
        print_color $GREEN "✅ Resource Level: MEDIUM (Good for development)"
    else
        RESOURCE_LEVEL="high"
        print_color $GREEN "✅ Resource Level: HIGH (Excellent for production)"
    fi
    
    echo ""
    return 0
}

# Function to display deployment options
display_deployment_options() {
    print_section "Available Deployment Options"
    
    echo "Based on your system resources, you can choose from these deployment options:"
    echo ""
    
    if [ "$RESOURCE_LEVEL" = "low" ]; then
        print_color $YELLOW "1. 📱 Minimal Deployment (Recommended for your system)"
        echo "   • 1 organization (Ecol University)"
        echo "   • 1 peer node"
        echo "   • 1 orderer"
        echo "   • 2 certificate authorities"
        echo "   • No monitoring stack"
        echo "   • Memory usage: ~2.5GB"
        echo "   • CPU usage: ~2 cores"
        echo ""
        
        print_color $YELLOW "2. 🔧 Custom Deployment"
        echo "   • Choose your own configuration"
        echo "   • Adjust based on your preferences"
        echo "   • Resource requirements will be calculated"
        echo ""
        
    elif [ "$RESOURCE_LEVEL" = "medium" ]; then
        print_color $GREEN "1. 📱 Minimal Deployment (Lightweight)"
        echo "   • 1 organization (Ecol University)"
        echo "   • 1 peer node"
        echo "   • 1 orderer"
        echo "   • 2 certificate authorities"
        echo "   • No monitoring stack"
        echo "   • Memory usage: ~2.5GB"
        echo "   • CPU usage: ~2 cores"
        echo ""
        
        print_color $GREEN "2. 🚀 Standard Deployment (Recommended for your system)"
        echo "   • 2 organizations (Ecol, Limkokwing)"
        echo "   • 2 peer nodes"
        echo "   • 1 orderer"
        echo "   • 3 certificate authorities"
        echo "   • Basic monitoring"
        echo "   • Memory usage: ~5.0GB"
        echo "   • CPU usage: ~3 cores"
        echo ""
        
        print_color $YELLOW "3. 🔧 Custom Deployment"
        echo "   • Choose your own configuration"
        echo "   • Adjust based on your preferences"
        echo "   • Resource requirements will be calculated"
        echo ""
        
    else
        print_color $GREEN "1. 📱 Minimal Deployment (Lightweight)"
        echo "   • 1 organization (Ecol University)"
        echo "   • 1 peer node"
        echo "   • 1 orderer"
        echo "   • 2 certificate authorities"
        echo "   • No monitoring stack"
        echo "   • Memory usage: ~2.5GB"
        echo "   • CPU usage: ~2 cores"
        echo ""
        
        print_color $GREEN "2. 🚀 Standard Deployment (Good for development)"
        echo "   • 2 organizations (Ecol, Limkokwing)"
        echo "   • 2 peer nodes"
        echo "   • 1 orderer"
        echo "   • 3 certificate authorities"
        echo "   • Basic monitoring"
        echo "   • Memory usage: ~5.0GB"
        echo "   • CPU usage: ~3 cores"
        echo ""
        
        print_color $PURPLE "3. 🏢 Full Enterprise Deployment (Recommended for your system)"
        echo "   • 4 organizations (Ecol, Limkokwing, Botho, NUL)"
        echo "   • 4 peer nodes"
        echo "   • 3 orderers (Raft consensus)"
        echo "   • 5 certificate authorities"
        echo "   • Full monitoring stack"
        echo "   • Memory usage: ~12.0GB"
        echo "   • CPU usage: ~6 cores"
        echo ""
        
        print_color $CYAN "4. ⚡ High-Performance Deployment"
        echo "   • 4 organizations (Ecol, Limkokwing, Botho, NUL)"
        echo "   • 8 peer nodes (2 per org)"
        echo "   • 3 orderers (Raft consensus)"
        echo "   • 5 certificate authorities"
        echo "   • Full monitoring stack"
        echo "   • Memory usage: ~20.0GB"
        echo "   • CPU usage: ~10 cores"
        echo ""
        
        print_color $YELLOW "5. 🔧 Custom Deployment"
        echo "   • Choose your own configuration"
        echo "   • Adjust based on your preferences"
        echo "   • Resource requirements will be calculated"
        echo ""
    fi
}

# Function to get user choice
get_user_choice() {
    local max_choice
    if [ "$RESOURCE_LEVEL" = "low" ]; then
        max_choice=2
    elif [ "$RESOURCE_LEVEL" = "medium" ]; then
        max_choice=3
    else
        max_choice=5
    fi
    
    while true; do
        echo ""
        print_color $WHITE "Enter your choice (1-$max_choice):"
        read -r user_choice
        
        if [[ "$user_choice" =~ ^[1-$max_choice]$ ]]; then
            echo "$user_choice"
            return
        else
            print_color $RED "❌ Invalid choice. Please enter a number between 1 and $max_choice."
        fi
    done
}

# Function to configure minimal deployment
configure_minimal_deployment() {
    print_section "Configuring Minimal Deployment"
    
    print_color $WHITE "📋 Minimal Deployment Configuration:"
    echo "   • Organizations: Ecol University"
    echo "   • Peers: 1 (peer0.ecol.example.com)"
    echo "   • Orderer: 1 (orderer.example.com)"
    echo "   • CAs: 2 (orderer + ecol)"
    echo "   • Monitoring: Disabled"
    echo ""
    
    # Create minimal configuration
    cat > deployment-config.json << EOF
{
    "deployment_type": "minimal",
    "organizations": ["EcolOrgMSP"],
    "orderers": 1,
    "peers_per_org": 1,
    "monitoring": false,
    "resource_usage": {
        "memory_gb": 2.5,
        "cpu_cores": 2,
        "disk_gb": 5
    },
    "services": {
        "cas": ["ca.orderer.example.com", "ca.ecol.example.com"],
        "orderers": ["orderer.example.com"],
        "peers": ["peer0.ecol.example.com"],
        "couchdbs": ["couchdb0"],
        "monitoring": []
    },
    "ports": {
        "cas": [7054, 8054],
        "orderers": [7050],
        "peers": [7051],
        "couchdbs": [5984],
        "monitoring": []
    }
}
EOF
    
    print_color $GREEN "✅ Minimal deployment configuration created"
}

# Function to configure standard deployment
configure_standard_deployment() {
    print_section "Configuring Standard Deployment"
    
    print_color $WHITE "📋 Standard Deployment Configuration:"
    echo "   • Organizations: Ecol University, Limkokwing University"
    echo "   • Peers: 2 (1 per organization)"
    echo "   • Orderer: 1 (orderer.example.com)"
    echo "   • CAs: 3 (orderer + 2 orgs)"
    echo "   • Monitoring: Basic (Prometheus, Grafana)"
    echo ""
    
    # Create standard configuration
    cat > deployment-config.json << EOF
{
    "deployment_type": "standard",
    "organizations": ["EcolOrgMSP", "LimkokwingOrgMSP"],
    "orderers": 1,
    "peers_per_org": 1,
    "monitoring": true,
    "resource_usage": {
        "memory_gb": 5.0,
        "cpu_cores": 3,
        "disk_gb": 15
    },
    "services": {
        "cas": ["ca.orderer.example.com", "ca.ecol.example.com", "ca.limkokwing.example.com"],
        "orderers": ["orderer.example.com"],
        "peers": ["peer0.ecol.example.com", "peer0.limkokwing.example.com"],
        "couchdbs": ["couchdb0", "couchdb1"],
        "monitoring": ["prometheus", "grafana", "postgres"]
    },
    "ports": {
        "cas": [7054, 8054, 9054],
        "orderers": [7050],
        "peers": [7051, 9051],
        "couchdbs": [5984, 6984],
        "monitoring": [9090, 3000, 5432]
    }
}
EOF
    
    print_color $GREEN "✅ Standard deployment configuration created"
}

# Function to configure full deployment
configure_full_deployment() {
    print_section "Configuring Full Enterprise Deployment"
    
    print_color $WHITE "📋 Full Enterprise Deployment Configuration:"
    echo "   • Organizations: Ecol, Limkokwing, Botho, NUL"
    echo "   • Peers: 4 (1 per organization)"
    echo "   • Orderers: 3 (Raft consensus)"
    echo "   • CAs: 5 (orderer + 4 orgs)"
    echo "   • Monitoring: Full stack"
    echo ""
    
    # Create full configuration
    cat > deployment-config.json << EOF
{
    "deployment_type": "full",
    "organizations": ["EcolOrgMSP", "LimkokwingOrgMSP", "BothoOrgMSP", "NulOrgMSP"],
    "orderers": 3,
    "peers_per_org": 1,
    "monitoring": true,
    "resource_usage": {
        "memory_gb": 12.0,
        "cpu_cores": 6,
        "disk_gb": 40
    },
    "services": {
        "cas": ["ca.orderer.example.com", "ca.ecol.example.com", "ca.limkokwing.example.com", "ca.botho.example.com", "ca.nul.example.com"],
        "orderers": ["orderer.example.com", "orderer1.example.com", "orderer2.example.com"],
        "peers": ["peer0.ecol.example.com", "peer0.limkokwing.example.com", "peer0.botho.example.com", "peer0.nul.example.com"],
        "couchdbs": ["couchdb0", "couchdb1", "couchdb2", "couchdb3"],
        "monitoring": ["prometheus", "grafana", "postgres", "explorer"]
    },
    "ports": {
        "cas": [7054, 8054, 9054, 10054, 11054],
        "orderers": [7050, 7051, 7052],
        "peers": [7051, 9051, 11051, 12051],
        "couchdbs": [5984, 6984, 7984, 8984],
        "monitoring": [9090, 3000, 5432, 8080]
    }
}
EOF
    
    print_color $GREEN "✅ Full enterprise deployment configuration created"
}

# Function to configure high-performance deployment
configure_high_performance_deployment() {
    print_section "Configuring High-Performance Deployment"
    
    print_color $WHITE "📋 High-Performance Deployment Configuration:"
    echo "   • Organizations: Ecol, Limkokwing, Botho, NUL"
    echo "   • Peers: 8 (2 per organization)"
    echo "   • Orderers: 3 (Raft consensus)"
    echo "   • CAs: 5 (orderer + 4 orgs)"
    echo "   • Monitoring: Full stack with advanced analytics"
    echo ""
    
    # Create high-performance configuration
    cat > deployment-config.json << EOF
{
    "deployment_type": "high-performance",
    "organizations": ["EcolOrgMSP", "LimkokwingOrgMSP", "BothoOrgMSP", "NulOrgMSP"],
    "orderers": 3,
    "peers_per_org": 2,
    "monitoring": true,
    "resource_usage": {
        "memory_gb": 20.0,
        "cpu_cores": 10,
        "disk_gb": 60
    },
    "services": {
        "cas": ["ca.orderer.example.com", "ca.ecol.example.com", "ca.limkokwing.example.com", "ca.botho.example.com", "ca.nul.example.com"],
        "orderers": ["orderer.example.com", "orderer1.example.com", "orderer2.example.com"],
        "peers": ["peer0.ecol.example.com", "peer1.ecol.example.com", "peer0.limkokwing.example.com", "peer1.limkokwing.example.com", "peer0.botho.example.com", "peer1.botho.example.com", "peer0.nul.example.com", "peer1.nul.example.com"],
        "couchdbs": ["couchdb0", "couchdb1", "couchdb2", "couchdb3", "couchdb4", "couchdb5", "couchdb6", "couchdb7"],
        "monitoring": ["prometheus", "grafana", "postgres", "explorer", "jaeger"]
    },
    "ports": {
        "cas": [7054, 8054, 9054, 10054, 11054],
        "orderers": [7050, 7051, 7052],
        "peers": [7051, 8051, 9051, 10051, 11051, 12051, 13051, 14051],
        "couchdbs": [5984, 6984, 7984, 8984, 9984, 10984, 11984, 12984],
        "monitoring": [9090, 3000, 5432, 8080, 16686]
    }
}
EOF
    
    print_color $GREEN "✅ High-performance deployment configuration created"
}

# Function to configure custom deployment
configure_custom_deployment() {
    print_section "Configuring Custom Deployment"
    
    # Get custom configuration from user
    print_color $WHITE "📋 Custom Deployment Configuration:"
    echo ""
    
    # Select organizations
    echo "Available organizations:"
    echo "1. Ecol University (ECOL)"
    echo "2. Limkokwing University (LIMKOWING)"
    echo "3. Botho University (BOTHO)"
    echo "4. National University of Lesotho (NUL)"
    echo ""
    
    local selected_orgs=()
    local org_options=("EcolOrgMSP" "LimkokwingOrgMSP" "BothoOrgMSP" "NulOrgMSP")
    local org_names=("ECOL" "LIMKOWING" "BOTHO" "NUL")
    
    for i in {1..4}; do
        echo "Select organization $i (1-4) or press Enter to finish:"
        read -r org_choice
        
        if [ -z "$org_choice" ]; then
            break
        fi
        
        if [[ "$org_choice" =~ ^[1-4]$ ]]; then
            selected_orgs+=("${org_options[$((org_choice-1))]}")
            echo "   ✓ Added ${org_names[$((org_choice-1))]}"
        else
            echo "   ❌ Invalid choice"
        fi
    done
    
    if [ ${#selected_orgs[@]} -eq 0 ]; then
        echo "No organizations selected. Using default: Ecol"
        selected_orgs=("EcolOrgMSP")
    fi
    
    echo ""
    echo "Selected organizations: ${selected_orgs[@]}"
    
    # Get peers per organization
    echo ""
    echo "Number of peers per organization (1-3) [default: 1]:"
    read -r peers_per_org
    peers_per_org=${peers_per_org:-1}
    
    if [[ ! "$peers_per_org" =~ ^[1-3]$ ]]; then
        peers_per_org=1
        echo "Invalid input. Using default: 1"
    fi
    
    # Get orderer count
    echo ""
    echo "Number of orderers (1-3) [default: 1]:"
    read -r orderer_count
    orderer_count=${orderer_count:-1}
    
    if [[ ! "$orderer_count" =~ ^[1-3]$ ]]; then
        orderer_count=1
        echo "Invalid input. Using default: 1"
    fi
    
    # Get monitoring preference
    echo ""
    echo "Enable monitoring stack? (y/n) [default: y]:"
    read -r enable_monitoring
    enable_monitoring=${enable_monitoring:-y}
    
    if [[ "$enable_monitoring" =~ ^[Yy]$ ]]; then
        monitoring=true
    else
        monitoring=false
    fi
    
    # Calculate resource requirements
    num_orgs=${#selected_orgs[@]}
    total_peers=$((num_orgs * peers_per_org))
    total_cas=$((1 + num_orgs))
    total_couchdb=$total_peers
    
    # Memory calculations
    peer_memory=$(echo "0.8 * $total_peers" | bc)
    orderer_memory=$(echo "0.5 * $orderer_count" | bc)
    ca_memory=$(echo "0.3 * $total_cas" | bc)
    couchdb_memory=$(echo "0.4 * $total_couchdb" | bc)
    monitoring_memory=1.5
    if [ "$monitoring" = false ]; then
        monitoring_memory=0
    fi
    
    total_memory=$(echo "$peer_memory + $orderer_memory + $ca_memory + $couchdb_memory + $monitoring_memory" | bc)
    
    # CPU calculations
    peer_cpu=$(echo "0.5 * $total_peers" | bc)
    orderer_cpu=$(echo "0.3 * $orderer_count" | bc)
    ca_cpu=$(echo "0.2 * $total_cas" | bc)
    couchdb_cpu=$(echo "0.3 * $total_couchdb" | bc)
    monitoring_cpu=1.0
    if [ "$monitoring" = false ]; then
        monitoring_cpu=0
    fi
    
    total_cpu=$(echo "$peer_cpu + $orderer_cpu + $ca_cpu + $couchdb_cpu + $monitoring_cpu" | bc)
    
    # Create custom configuration
    cat > deployment-config.json << EOF
{
    "deployment_type": "custom",
    "organizations": [$(printf '"%s",' "${selected_orgs[@]}" | sed 's/,$//')],
    "orderers": $orderer_count,
    "peers_per_org": $peers_per_org,
    "monitoring": $monitoring,
    "resource_usage": {
        "memory_gb": $total_memory,
        "cpu_cores": $total_cpu,
        "disk_gb": $((total_peers * 3))
    },
    "services": {
        "cas": ["ca.orderer.example.com"$(for org in "${selected_orgs[@]}"; do echo ", \"ca.${org,,}.example.com\""; done)],
        "orderers": $(for i in $(seq 1 $orderer_count); do echo "\"orderer.example.com\""; done | sed 's/ /, /g'),
        "peers": [$(for org in "${selected_orgs[@]}"; do for i in $(seq 1 $peers_per_org); do echo "\"peer$((i-1)).${org,,}.example.com\""; done; done | sed 's/ /, /g')],
        "couchdbs": [$(for i in $(seq 1 $total_couchdb); do echo "\"couchdb$((i-1))\""; done | sed 's/ /, /g')],
        "monitoring": []
    }
}
EOF
    
    if [ "$monitoring" = true ]; then
        sed -i 's/"monitoring": \[\]/"monitoring": ["prometheus", "grafana", "postgres", "explorer"]/g' deployment-config.json
    fi
    
    echo ""
    print_color $WHITE "📋 Custom Deployment Summary:"
    echo "   • Organizations: ${#selected_orgs[@]} (${selected_orgs[@]})"
    echo "   • Peers: $total_peers ($peers_per_org per org)"
    echo "   • Orderers: $orderer_count"
    echo "   • CAs: $total_cas"
    echo "   • Monitoring: $([ "$monitoring" = true ] && echo "Enabled" || echo "Disabled")"
    echo "   • Estimated Memory: ${total_memory}GB"
    echo "   • Estimated CPU: ${total_cpu} cores"
    echo ""
    
    print_color $GREEN "✅ Custom deployment configuration created"
}

# Function to show deployment summary
show_deployment_summary() {
    print_section "Deployment Summary"
    
    if [ ! -f deployment-config.json ]; then
        print_color $RED "❌ No deployment configuration found"
        return 1
    fi
    
    # Parse configuration
    DEPLOYMENT_TYPE=$(python3 -c "
import json
with open('deployment-config.json') as f:
    config = json.load(f)
print(config.get('deployment_type', 'unknown'))
" 2>/dev/null)
    
    ORG_COUNT=$(python3 -c "
import json
with open('deployment-config.json') as f:
    config = json.load(f)
print(len(config.get('organizations', [])))
" 2>/dev/null)
    
    PEERS_PER_ORG=$(python3 -c "
import json
with open('deployment-config.json') as f:
    config = json.load(f)
print(config.get('peers_per_org', 1))
" 2>/dev/null)
    
    ORDERERS=$(python3 -c "
import json
with open('deployment-config.json') as f:
    config = json.load(f)
print(config.get('orderers', 1))
" 2>/dev/null)
    
    MONITORING=$(python3 -c "
import json
with open('deployment-config.json') as f:
    config = json.load(f)
print(config.get('monitoring', False))
" 2>/dev/null)
    
    MEMORY_USAGE=$(python3 -c "
import json
with open('deployment-config.json') as f:
    config = json.load(f)
print(config.get('resource_usage', {}).get('memory_gb', 0))
" 2>/dev/null)
    
    CPU_USAGE=$(python3 -c "
import json
with open('deployment-config.json') as f:
    config = json.load(f)
print(config.get('resource_usage', {}).get('cpu_cores', 0))
" 2>/dev/null)
    
    TOTAL_PEERS=$((ORG_COUNT * PEERS_PER_ORG))
    
    print_color $WHITE "📋 Deployment Configuration:"
    echo "   • Type: $DEPLOYMENT_TYPE"
    echo "   • Organizations: $ORG_COUNT"
    echo "   • Total Peers: $TOTAL_PEERS"
    echo "   • Peers per Org: $PEERS_PER_ORG"
    echo "   • Orderers: $ORDERERS"
    echo "   • Monitoring: $([ "$MONITORING" = "True" ] && echo "Enabled" || echo "Disabled")"
    echo "   • Estimated Memory: ${MEMORY_USAGE}GB"
    echo "   • Estimated CPU: ${CPU_USAGE} cores"
    echo ""
    
    # Resource utilization
    CPU_UTILIZATION=$(echo "scale=1; $CPU_USAGE * 100 / $CPU_CORES" | bc)
    MEMORY_UTILIZATION=$(echo "scale=1; $MEMORY_USAGE * 100 / $AVAILABLE_MEMORY" | bc)
    
    print_color $WHITE "📊 Resource Utilization:"
    echo "   • CPU: ${CPU_UTILIZATION}% (${CPU_USAGE}/${CPU_CORES} cores)"
    echo "   • Memory: ${MEMORY_UTILIZATION}% (${MEMORY_USAGE}/${AVAILABLE_MEMORY}GB)"
    echo ""
    
    # Warnings
    if (( $(echo "$CPU_UTILIZATION > 80" | bc -l) )); then
        print_color $YELLOW "⚠️  Warning: High CPU utilization detected"
    fi
    
    if (( $(echo "$MEMORY_UTILIZATION > 80" | bc -l) )); then
        print_color $YELLOW "⚠️  Warning: High memory utilization detected"
    fi
    
    if (( $(echo "$AVAILABLE_DISK < 10" | bc -l) )); then
        print_color $YELLOW "⚠️  Warning: Low disk space available"
    fi
    
    echo ""
}

# Function to deploy with configuration
deploy_with_config() {
    print_section "Deploying with Configuration"
    
    if [ ! -f deployment-config.json ]; then
        print_color $RED "❌ No deployment configuration found"
        return 1
    fi
    
    print_color $WHITE "🚀 Starting deployment with your configuration..."
    echo ""
    
    # Check if user wants to proceed
    echo "This will:"
    echo "  • Stop any existing services"
    echo "  • Deploy the selected configuration"
    echo "  • This may take several minutes"
    echo ""
    print_color $YELLOW "Do you want to proceed? (y/n)"
    read -r proceed
    
    if [[ ! "$proceed" =~ ^[Yy]$ ]]; then
        print_color $BLUE "Deployment cancelled by user"
        return 0
    fi
    
    # Stop existing services
    print_step "Stopping existing services"
    docker-compose -f docker-compose.yaml down 2>/dev/null || true
    
    # Generate dynamic docker-compose file
    print_step "Generating dynamic docker-compose configuration"
    python3 scripts/generate-docker-compose.py deployment-config.json
    
    # Run deployment
    print_step "Running deployment"
    ./scripts/deploy-complete-system.sh deploy
    
    print_color $GREEN "✅ Deployment completed!"
}

# Function to show help
show_help() {
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  (no args)  - Show interactive deployment menu"
    echo "  --check    - Check system resources only"
    echo "  --minimal  - Deploy minimal configuration"
    echo "  --standard - Deploy standard configuration"
    echo "  --full     - Deploy full enterprise configuration"
    echo "  --help     - Show this help message"
    echo ""
}

# Function to print step
print_step() {
    echo ""
    print_color $CYAN "🔧 $1"
}

# Main execution
main() {
    case "${1:-}" in
        "--check")
            check_system_resources
            ;;
        "--minimal")
            check_system_resources
            configure_minimal_deployment
            show_deployment_summary
            deploy_with_config
            ;;
        "--standard")
            check_system_resources
            configure_standard_deployment
            show_deployment_summary
            deploy_with_config
            ;;
        "--full")
            check_system_resources
            configure_full_deployment
            show_deployment_summary
            deploy_with_config
            ;;
        "--help")
            show_help
            ;;
        "")
            # Interactive menu
            print_header
            check_system_resources || exit 1
            display_deployment_options
            user_choice=$(get_user_choice)
            
            case $user_choice in
                1)
                    if [ "$RESOURCE_LEVEL" = "low" ] || [ "$RESOURCE_LEVEL" = "medium" ]; then
                        configure_minimal_deployment
                    else
                        configure_minimal_deployment
                    fi
                    ;;
                2)
                    if [ "$RESOURCE_LEVEL" = "medium" ]; then
                        configure_standard_deployment
                    elif [ "$RESOURCE_LEVEL" = "high" ]; then
                        configure_standard_deployment
                    else
                        configure_standard_deployment
                    fi
                    ;;
                3)
                    if [ "$RESOURCE_LEVEL" = "high" ]; then
                        configure_full_deployment
                    else
                        configure_custom_deployment
                    fi
                    ;;
                4)
                    if [ "$RESOURCE_LEVEL" = "high" ]; then
                        configure_high_performance_deployment
                    else
                        configure_custom_deployment
                    fi
                    ;;
                5)
                    configure_custom_deployment
                    ;;
            esac
            
            show_deployment_summary
            deploy_with_config
            ;;
        *)
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
