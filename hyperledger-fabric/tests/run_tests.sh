#!/bin/bash

#
# Test Runner Script for LGCSE Certificate Verification System
#
# This script runs comprehensive tests for the Hyperledger Fabric blockchain system,
# including unit tests, integration tests, performance tests, and security tests.
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
    print_color $BLUE "🧪 LGCSE Certificate Verification Test Suite"
    print_color $BLUE "=================================================="
    echo ""
    print_color $WHITE "Running comprehensive tests for the blockchain system:"
    print_color $WHITE "• Chaincode functionality tests"
    print_color $WHITE "• Integration tests"
    print_color $WHITE "• Performance tests"
    print_color $WHITE "• Security tests"
    echo ""
}

# Function to check prerequisites
check_prerequisites() {
    print_color $CYAN "🔍 Checking test prerequisites..."
    
    # Check if Python is available
    if ! command -v python3 >/dev/null 2>&1; then
        print_color $RED "❌ Python 3 is not installed. Please install Python 3 and try again."
        exit 1
    fi
    print_color $GREEN "✅ Python 3 is available"
    
    # Check required Python packages
    python3 -c "
import sys
required_packages = ['psutil', 'pyyaml']
missing_packages = []
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    print(f'Missing packages: {missing_packages}')
    sys.exit(1)
else:
    print('All required packages are available')
" 2>/dev/null || {
        print_color $YELLOW "⚠️ Installing required Python packages..."
        pip3 install psutil pyyaml
    }
    
    print_color $GREEN "✅ Python packages are available"
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_color $RED "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_color $GREEN "✅ Docker is running"
    
    # Check if network is deployed
    if ! docker ps | grep -q "peer0.ecol.example.com\|orderer.example.com"; then
        print_color $YELLOW "⚠️ Fabric network is not running. Starting minimal network for testing..."
        ./scripts/deploy-menu.sh --minimal
        sleep 30
    fi
    
    print_color $GREEN "✅ Prerequisites checked"
}

# Function to run unit tests
run_unit_tests() {
    print_color $CYAN "🧪 Running Unit Tests"
    print_color $CYAN "$(printf '=%.0s' {80} '' | tr ' ' '=')"
    
    # Create test directory
    mkdir -p tests/unit
    
    # Run chaincode unit tests
    print_color $WHITE "Testing chaincode functions..."
    
    python3 -c "
import sys
sys.path.append('tests')
from test_framework import ChaincodeTestSuite

suite = ChaincodeTestSuite()
suite.setup()

# Test individual functions
print('Testing certificate issuance...')
result = suite.test_certificate_issuance()
print(f'Result: {result[0]} - {result[1]}')

print('Testing certificate verification...')
result = suite.test_certificate_verification()
print(f'Result: {result[0]} - {result[1]}')

print('Testing certificate query...')
result = suite.test_certificate_query()
print(f'Result: {result[0]} - {result[1]}')

print('Testing network statistics...')
result = suite.test_network_statistics()
print(f'Result: {result[0]} - {result[1]}')

suite.teardown()
" 2>/dev/null || {
        print_color $RED "❌ Unit tests failed"
        return 1
    }
    
    print_color $GREEN "✅ Unit tests completed"
    return 0
}

# Function to run integration tests
run_integration_tests() {
    print_color $CYAN "🔗 Running Integration Tests"
    print_color $CYAN "$(printf '=%.0s' {80} '' | tr ' ' '=')"
    
    python3 -c "
import sys
sys.path.append('tests')
from test_framework import IntegrationTestSuite

suite = IntegrationTestSuite()
suite.setup()

# Test integration functions
print('Testing channel creation...')
result = suite.test_channel_creation()
print(f'Result: {result[0]} - {result[1]}')

print('Testing access control...')
result = suite.test_access_control_permissions()
print(f'Result: {result[0]} - {result[1]}')

print('Testing data encryption...')
result = suite.test_data_encryption()
print(f'Result: {result[0]} - {result[1]}')

suite.teardown()
" 2>/dev/null || {
        print_color $RED "❌ Integration tests failed"
        return 1
    }
    
    print_color $GREEN "✅ Integration tests completed"
    return 0
}

# Function to run performance tests
run_performance_tests() {
    print_color $CYAN "⚡ Running Performance Tests"
    print_color $CYAN "$(printf '=%.0s' {80} '' | tr ' ' '=')"
    
    python3 -c "
import sys
sys.path.append('tests')
from test_framework import PerformanceTestSuite

suite = PerformanceTestSuite()
suite.setup()

# Test performance
print('Testing certificate issuance performance...')
result = suite.test_certificate_issuance_performance()
print(f'Result: {result[0]} - {result[1]}')

print('Testing verification performance...')
result = suite.test_verification_performance()
print(f'Result: {result[0]} - {result[1]}')

print('Testing query performance...')
result = suite.test_query_performance()
print(f'Result: {result[0]} - {result[1]}')

suite.teardown()
" 2>/dev/null || {
        print_color $RED "❌ Performance tests failed"
        return 1
    }
    
    print_color $GREEN "✅ Performance tests completed"
    return 0
}

# Function to run security tests
run_security_tests() {
    print_color $CYAN "🔒 Running Security Tests"
    print_color $CYAN "$(printf '=%.0s' {80} '' | tr ' ' '=')"
    
    python3 -c "
import sys
sys.path.append('tests')
from test_framework import SecurityTestSuite

suite = SecurityTestSuite()
suite.setup()

# Test security
print('Testing TLS encryption...')
result = suite.test_tls_encryption()
print(f'Result: {result[0]} - {result[1]}')

print('Testing access control bypass...')
result = suite.test_access_control_bypass()
print(f'Result: {result[0]} - {result[1]}')

print('Testing data integrity...')
result = suite.test_data_integrity()
print(f'Result: {result[0]} - {result[1]}')

suite.teardown()
" 2>/dev/null || {
        print_color $RED "❌ Security tests failed"
        return 1
    }
    
    print_color $GREEN "✅ Security tests completed"
    return 0
}

# Function to run comprehensive test suite
run_comprehensive_tests() {
    print_color $CYAN "🧪 Running Comprehensive Test Suite"
    print_color $CYAN "$(printf '=%.0s' {80} '' | tr ' ' '=')"
    
    python3 tests/test_framework.py
    test_exit_code=$?
    
    if [ $test_exit_code -eq 0 ]; then
        print_color $GREEN "✅ All comprehensive tests passed"
    else
        print_color $RED "❌ Some comprehensive tests failed"
    fi
    
    return $test_exit_code
}

# Function to generate test report
generate_test_report() {
    print_color $CYAN "📋 Generating Test Report"
    print_color $CYAN "$(printf '=%.0s' {80} '' | tr ' ' '=')"
    
    # Find the latest test results file
    latest_results=$(find . -name "test_results_*.json" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [ -n "$latest_results" ]; then
        print_color $WHITE "Latest test results: $latest_results"
        
        # Extract key metrics
        python3 -c "
import json
import sys

with open('$latest_results', 'r') as f:
    results = json.load(f)

print('Test Summary:')
print(f'  Status: {results[\"status\"]}')
print(f'  Total Tests: {results[\"total_tests\"]}')
print(f'  Passed: {results[\"total_passed\"]}')
print(f'  Failed: {results[\"total_failed\"]}')
print(f'  Success Rate: {results[\"overall_success_rate\"]:.1f}%')
print(f'  Duration: {results[\"total_duration\"]:.2f}s')

print('\nTest Suite Results:')
for suite_name, suite_results in results['test_suites'].items():
    print(f'  {suite_name}:')
    print(f'    Tests: {suite_results[\"total_tests\"]}')
    print(f'    Passed: {suite_results[\"passed_tests\"]}')
    print(f'    Success Rate: {suite_results[\"success_rate\"]:.1f}%')
    if 'error' in suite_results:
        print(f'    Error: {suite_results[\"error\"]}')
"
    else
        print_color $YELLOW "⚠️ No test results found"
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  (no args)  - Run comprehensive test suite"
    echo "  --unit     - Run unit tests only"
    echo "  --integration - Run integration tests only"
    echo "  --performance - Run performance tests only"
    echo "  --security  - Run security tests only"
    echo "  --report    - Generate test report"
    echo "  --help      - Show this help message"
    echo ""
    echo "Test Categories:"
    echo "  • Unit Tests - Individual component testing"
    echo "  • Integration Tests - Cross-component testing"
    echo "  • Performance Tests - Performance and load testing"
    echo "  • Security Tests - Security and vulnerability testing"
    echo ""
}

# Main execution
main() {
    local test_type=${1:-"comprehensive"}
    local exit_code=0
    
    case "$test_type" in
        "--unit")
            print_header
            check_prerequisites || exit 1
            run_unit_tests || exit_code=1
            ;;
        "--integration")
            print_header
            check_prerequisites || exit 1
            run_integration_tests || exit_code=1
            ;;
        "--performance")
            print_header
            check_prerequisites || exit 1
            run_performance_tests || exit_code=1
            ;;
        "--security")
            print_header
            check_prerequisites || exit 1
            run_security_tests || exit_code=1
            ;;
        "--report")
            generate_test_report
            ;;
        "--help")
            show_help
            ;;
        "comprehensive"|"")
            print_header
            check_prerequisites || exit 1
            run_comprehensive_tests || exit_code=1
            generate_test_report
            ;;
        *)
            print_color $RED "❌ Unknown option: $test_type"
            show_help
            exit 1
            ;;
    esac
    
    if [ $exit_code -eq 0 ]; then
        print_color $GREEN "🎉 Test execution completed successfully!"
    else
        print_color $RED "❌ Test execution failed!"
    fi
    
    return $exit_code
}

# Run main function
main "$@"
