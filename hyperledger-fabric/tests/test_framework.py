#!/usr/bin/env python3
"""
Comprehensive Testing Framework for LGCSE Certificate Verification System

This module provides a complete testing suite including unit tests, integration tests,
performance tests, and security tests for the Hyperledger Fabric blockchain system.
"""

import os
import sys
import json
import time
import logging
import unittest
import asyncio
import subprocess
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.fabric_sdk import fabric_sdk
from utils.channel_manager import channel_manager
from utils.access_control import access_control_manager
from utils.msp_manager import msp_manager

logger = logging.getLogger(__name__)

class TestResult:
    """Test result container"""
    def __init__(self, name: str, passed: bool, duration: float, message: str = "", details: Dict[str, Any] = None):
        self.name = name
        self.passed = passed
        self.duration = duration
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()

class TestSuite:
    """Base test suite class"""
    def __init__(self, name: str):
        self.name = name
        self.results: List[TestResult] = []
        self.setup_complete = False
        self.teardown_complete = False
    
    def setup(self):
        """Setup test environment"""
        pass
    
    def teardown(self):
        """Cleanup test environment"""
        pass
    
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> TestResult:
        """Run a single test"""
        start_time = time.time()
        try:
            result = test_func(*args, **kwargs)
            if isinstance(result, bool):
                passed = result
                message = "Test passed" if passed else "Test failed"
                details = {}
            elif isinstance(result, tuple) and len(result) == 2:
                passed, details = result
                message = "Test passed" if passed else "Test failed"
            else:
                passed = True
                message = "Test passed"
                details = {"result": result}
            
            duration = time.time() - start_time
            test_result = TestResult(test_name, passed, duration, message, details)
            self.results.append(test_result)
            return test_result
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = TestResult(test_name, False, duration, str(e), {"error": str(e)})
            self.results.append(test_result)
            return test_result
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test suite summary"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        total_duration = sum(r.duration for r in self.results)
        
        return {
            "suite_name": self.name,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": total_duration,
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "duration": r.duration,
                    "message": r.message,
                    "details": r.details,
                    "timestamp": r.timestamp
                }
                for r in self.results
            ]
        }

class ChaincodeTestSuite(TestSuite):
    """Chaincode testing suite"""
    
    def __init__(self):
        super().__init__("Chaincode Tests")
        self.test_certificates = []
        self.test_verifications = []
    
    def setup(self):
        """Setup chaincode test environment"""
        logger.info("Setting up chaincode test environment")
        
        # Create test certificates
        self.test_certificates = [
            {
                "certificateHash": f"TEST_CERT_{i}_{int(time.time())}",
                "studentId": f"STU_{i:03d}",
                "studentName": f"TestStudent{i}",
                "studentSurname": f"TestSurname{i}",
                "examinationYear": 2023,
                "subjects": [
                    {"name": "Mathematics", "grade": "A", "symbol": "*"},
                    {"name": "English", "grade": "B", "symbol": "+"}
                ],
                "credits": 5,
                "issueDate": "2023-12-01",
                "issuer": "Test University",
                "institutionCode": "ECOL",
                "privateData": f"encrypted_data_{i}"
            }
            for i in range(1, 6)
        ]
        
        self.setup_complete = True
        logger.info("Chaincode test environment setup complete")
    
    def teardown(self):
        """Cleanup chaincode test environment"""
        logger.info("Cleaning up chaincode test environment")
        
        # Clean up test data if needed
        self.test_certificates = []
        self.test_verifications = []
        
        self.teardown_complete = True
        logger.info("Chaincode test environment cleanup complete")
    
    def test_certificate_issuance(self) -> Tuple[bool, Dict[str, Any]]:
        """Test certificate issuance"""
        logger.info("Testing certificate issuance")
        
        results = []
        for cert in self.test_certificates:
            try:
                result = fabric_sdk.issue_certificate(cert)
                if result.get("success"):
                    results.append({"hash": cert["certificateHash"], "status": "issued"})
                    self.test_verifications.append({
                        "certificateHash": cert["certificateHash"],
                        "transactionId": result.get("transaction_id")
                    })
                else:
                    results.append({"hash": cert["certificateHash"], "status": "failed", "error": result.get("error")})
            except Exception as e:
                results.append({"hash": cert["certificateHash"], "status": "error", "error": str(e)})
        
        success_count = sum(1 for r in results if r["status"] == "issued")
        passed = success_count == len(self.test_certificates)
        
        return passed, {
            "total_certificates": len(self.test_certificates),
            "issued_certificates": success_count,
            "results": results
        }
    
    def test_certificate_verification(self) -> Tuple[bool, Dict[str, Any]]:
        """Test certificate verification"""
        logger.info("Testing certificate verification")
        
        if not self.test_verifications:
            return False, {"error": "No certificates to verify"}
        
        results = []
        for verification in self.test_verifications:
            try:
                verification_data = {
                    "certificateHash": verification["certificateHash"],
                    "verifierId": f"VER_{int(time.time())}",
                    "verifierName": "TestVerifier",
                    "institutionCode": "LIMKOWING",
                    "verificationMethod": "hash",
                    "ipAddress": "192.168.1.100",
                    "userAgent": "Test Agent",
                    "verificationData": ""
                }
                
                result = fabric_sdk.verify_certificate(verification_data)
                if result.get("success"):
                    results.append({"hash": verification["certificateHash"], "status": "verified"})
                else:
                    results.append({"hash": verification["certificateHash"], "status": "failed", "error": result.get("error")})
            except Exception as e:
                results.append({"hash": verification["certificateHash"], "status": "error", "error": str(e)})
        
        success_count = sum(1 for r in results if r["status"] == "verified")
        passed = success_count == len(self.test_verifications)
        
        return passed, {
            "total_verifications": len(self.test_verifications),
            "verified_certificates": success_count,
            "results": results
        }
    
    def test_certificate_query(self) -> Tuple[bool, Dict[str, Any]]:
        """Test certificate querying"""
        logger.info("Testing certificate querying")
        
        if not self.test_verifications:
            return False, {"error": "No certificates to query"}
        
        results = []
        for verification in self.test_verifications[:3]:  # Test first 3
            try:
                result = fabric_sdk.get_certificate(verification["certificateHash"])
                if result.get("success"):
                    cert_data = result.get("certificate")
                    results.append({
                        "hash": verification["certificateHash"],
                        "status": "found",
                        "studentName": cert_data.get("studentName"),
                        "institutionCode": cert_data.get("institutionCode")
                    })
                else:
                    results.append({"hash": verification["certificateHash"], "status": "not_found"})
            except Exception as e:
                results.append({"hash": verification["certificateHash"], "status": "error", "error": str(e)})
        
        success_count = sum(1 for r in results if r["status"] == "found")
        passed = success_count == len(results)
        
        return passed, {
            "total_queries": len(results),
            "found_certificates": success_count,
            "results": results
        }
    
    def test_certificate_revocation(self) -> Tuple[bool, Dict[str, Any]]:
        """Test certificate revocation"""
        logger.info("Testing certificate revocation")
        
        if not self.test_verifications:
            return False, {"error": "No certificates to revoke"}
        
        # Revoke first certificate
        cert_to_revoke = self.test_verifications[0]
        
        try:
            revocation_data = {
                "certificateHash": cert_to_revoke["certificateHash"],
                "reason": "Test revocation",
                "revokedBy": "TestAdmin",
                "institutionCode": "ECOL"
            }
            
            result = fabric_sdk.revoke_certificate(revocation_data)
            passed = result.get("success", False)
            
            return passed, {
                "revoked_certificate": cert_to_revoke["certificateHash"],
                "result": result
            }
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_network_statistics(self) -> Tuple[bool, Dict[str, Any]]:
        """Test network statistics retrieval"""
        logger.info("Testing network statistics")
        
        try:
            result = fabric_sdk.get_network_statistics()
            passed = result.get("success", False)
            
            if passed:
                stats = result.get("statistics", {})
                return True, {
                    "statistics": stats,
                    "has_certificates": stats.get("totalCertificates", 0) > 0,
                    "has_institutions": stats.get("totalInstitutions", 0) > 0
                }
            else:
                return False, {"error": result.get("error")}
                
        except Exception as e:
            return False, {"error": str(e)}

class IntegrationTestSuite(TestSuite):
    """Integration testing suite"""
    
    def __init__(self):
        super().__init__("Integration Tests")
        self.test_channels = []
        self.test_institutions = []
    
    def setup(self):
        """Setup integration test environment"""
        logger.info("Setting up integration test environment")
        
        # Create test institutions
        self.test_institutions = [
            {
                "nodeId": f"TEST_NODE_{i}_{int(time.time())}",
                "institutionCode": f"TEST{i}",
                "institutionName": f"Test Institution {i}",
                "nodeType": "issuer" if i == 1 else "verifier",
                "mspId": f"TestOrg{i}MSP",
                "peerId": f"peer0.test{i}.example.com",
                "channelName": "lgcse-channel",
                "status": "active",
                "publicKey": f"test_public_key_{i}",
                "nodeConfig": {"region": "test", "type": "university"}
            }
            for i in range(1, 4)
        ]
        
        self.setup_complete = True
        logger.info("Integration test environment setup complete")
    
    def teardown(self):
        """Cleanup integration test environment"""
        logger.info("Cleaning up integration test environment")
        
        # Clean up test data
        self.test_channels = []
        self.test_institutions = []
        
        self.teardown_complete = True
        logger.info("Integration test environment cleanup complete")
    
    def test_channel_creation(self) -> Tuple[bool, Dict[str, Any]]:
        """Test channel creation"""
        logger.info("Testing channel creation")
        
        try:
            from utils.channel_manager import ChannelType
            
            # Create test channel
            result = channel_manager.create_channel(
                "test-channel",
                ChannelType.CERTIFICATE_VERIFICATION,
                ["TestOrg1MSP", "TestOrg2MSP"],
                "Test channel for integration testing",
                "TestOrg1MSP"
            )
            
            passed = result.get("success", False)
            if passed:
                self.test_channels.append(result.get("channel_name"))
            
            return passed, result
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_channel_join(self) -> Tuple[bool, Dict[str, Any]]:
        """Test channel joining"""
        logger.info("Testing channel joining")
        
        if not self.test_channels:
            return False, {"error": "No test channels available"}
        
        try:
            channel_name = self.test_channels[0]
            result = channel_manager.join_channel(channel_name, "TestOrg3MSP")
            
            return result.get("success", False), result
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_cross_channel_communication(self) -> Tuple[bool, Dict[str, Any]]:
        """Test cross-channel communication"""
        logger.info("Testing cross-channel communication")
        
        try:
            result = channel_manager.enable_cross_channel_communication(
                "lgcse-certificate-channel",
                "lgcse-audit-channel",
                ["certificate_issued", "certificate_verified"],
                {"access_control": "role_based", "audit_required": True}
            )
            
            return result.get("success", False), result
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_access_control_permissions(self) -> Tuple[bool, Dict[str, Any]]:
        """Test access control permissions"""
        logger.info("Testing access control permissions")
        
        try:
            # Test admin access
            admin_result = access_control_manager.check_access_permission(
                "admin_user", "admin", "ECOL", "certificatePrivateData", "read"
            )
            
            # Test unauthorized access
            unauthorized_result = access_control_manager.check_access_permission(
                "unauthorized_user", "student", "ECOL", "certificatePrivateData", "read"
            )
            
            admin_granted = admin_result.get("access_granted", False)
            unauthorized_denied = not unauthorized_result.get("access_granted", True)
            
            passed = admin_granted and unauthorized_denied
            
            return passed, {
                "admin_access": admin_result,
                "unauthorized_access": unauthorized_result,
                "admin_granted": admin_granted,
                "unauthorized_denied": unauthorized_denied
            }
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_data_encryption(self) -> Tuple[bool, Dict[str, Any]]:
        """Test data encryption and decryption"""
        logger.info("Testing data encryption")
        
        try:
            test_data = "This is sensitive test data"
            data_type = "certificate"
            
            # Encrypt data
            encrypt_result = access_control_manager.encrypt_private_data(test_data, data_type)
            if not encrypt_result.get("success"):
                return False, {"error": "Encryption failed"}
            
            encrypted_data = encrypt_result.get("encrypted_data")
            checksum = encrypt_result.get("checksum")
            
            # Decrypt data
            decrypt_result = access_control_manager.decrypt_private_data(
                encrypted_data, data_type, checksum
            )
            
            if not decrypt_result.get("success"):
                return False, {"error": "Decryption failed"}
            
            decrypted_data = decrypt_result.get("decrypted_data")
            passed = decrypted_data == test_data
            
            return passed, {
                "original_data": test_data,
                "encrypted_data": encrypted_data[:50] + "...",  # Show partial for brevity
                "decrypted_data": decrypted_data,
                "data_match": passed
            }
            
        except Exception as e:
            return False, {"error": str(e)}

class PerformanceTestSuite(TestSuite):
    """Performance testing suite"""
    
    def __init__(self):
        super().__init__("Performance Tests")
        self.performance_metrics = {}
    
    def setup(self):
        """Setup performance test environment"""
        logger.info("Setting up performance test environment")
        self.setup_complete = True
        logger.info("Performance test environment setup complete")
    
    def teardown(self):
        """Cleanup performance test environment"""
        logger.info("Cleaning up performance test environment")
        self.performance_metrics = {}
        self.teardown_complete = True
        logger.info("Performance test environment cleanup complete")
    
    def test_certificate_issuance_performance(self) -> Tuple[bool, Dict[str, Any]]:
        """Test certificate issuance performance"""
        logger.info("Testing certificate issuance performance")
        
        try:
            num_certificates = 10
            start_time = time.time()
            
            successful_issuances = 0
            issuance_times = []
            
            for i in range(num_certificates):
                cert_start = time.time()
                
                cert_data = {
                    "certificateHash": f"PERF_CERT_{i}_{int(time.time())}",
                    "studentId": f"PERF_STU_{i:03d}",
                    "studentName": f"PerfStudent{i}",
                    "studentSurname": f"PerfSurname{i}",
                    "examinationYear": 2023,
                    "subjects": [{"name": "Mathematics", "grade": "A", "symbol": "*"}],
                    "credits": 5,
                    "issueDate": "2023-12-01",
                    "issuer": "Perf University",
                    "institutionCode": "ECOL",
                    "privateData": ""
                }
                
                result = fabric_sdk.issue_certificate(cert_data)
                cert_end = time.time()
                
                if result.get("success"):
                    successful_issuances += 1
                    issuance_times.append(cert_end - cert_start)
            
            total_time = time.time() - start_time
            
            if issuance_times:
                avg_time = sum(issuance_times) / len(issuance_times)
                min_time = min(issuance_times)
                max_time = max(issuance_times)
            else:
                avg_time = min_time = max_time = 0
            
            passed = successful_issuances == num_certificates and avg_time < 5.0  # 5 seconds max average
            
            self.performance_metrics["certificate_issuance"] = {
                "total_certificates": num_certificates,
                "successful_issuances": successful_issuances,
                "total_time": total_time,
                "avg_time": avg_time,
                "min_time": min_time,
                "max_time": max_time,
                "throughput": successful_issuances / total_time if total_time > 0 else 0
            }
            
            return passed, self.performance_metrics["certificate_issuance"]
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_verification_performance(self) -> Tuple[bool, Dict[str, Any]]:
        """Test verification performance"""
        logger.info("Testing verification performance")
        
        try:
            # First issue a certificate to verify
            cert_data = {
                "certificateHash": f"PERF_VERIFY_CERT_{int(time.time())}",
                "studentId": "PERF_VERIFY_STU",
                "studentName": "PerfVerifyStudent",
                "studentSurname": "PerfVerifySurname",
                "examinationYear": 2023,
                "subjects": [{"name": "Mathematics", "grade": "A", "symbol": "*"}],
                "credits": 5,
                "issueDate": "2023-12-01",
                "issuer": "Perf University",
                "institutionCode": "ECOL",
                "privateData": ""
            }
            
            issue_result = fabric_sdk.issue_certificate(cert_data)
            if not issue_result.get("success"):
                return False, {"error": "Failed to issue certificate for verification test"}
            
            # Test multiple verifications
            num_verifications = 20
            start_time = time.time()
            
            successful_verifications = 0
            verification_times = []
            
            for i in range(num_verifications):
                verify_start = time.time()
                
                verification_data = {
                    "certificateHash": cert_data["certificateHash"],
                    "verifierId": f"PERF_VER_{i:03d}",
                    "verifierName": f"PerfVerifier{i}",
                    "institutionCode": "LIMKOWING",
                    "verificationMethod": "hash",
                    "ipAddress": "192.168.1.100",
                    "userAgent": "Perf Agent",
                    "verificationData": ""
                }
                
                result = fabric_sdk.verify_certificate(verification_data)
                verify_end = time.time()
                
                if result.get("success"):
                    successful_verifications += 1
                    verification_times.append(verify_end - verify_start)
            
            total_time = time.time() - start_time
            
            if verification_times:
                avg_time = sum(verification_times) / len(verification_times)
                min_time = min(verification_times)
                max_time = max(verification_times)
            else:
                avg_time = min_time = max_time = 0
            
            passed = successful_verifications == num_verifications and avg_time < 3.0  # 3 seconds max average
            
            self.performance_metrics["verification"] = {
                "total_verifications": num_verifications,
                "successful_verifications": successful_verifications,
                "total_time": total_time,
                "avg_time": avg_time,
                "min_time": min_time,
                "max_time": max_time,
                "throughput": successful_verifications / total_time if total_time > 0 else 0
            }
            
            return passed, self.performance_metrics["verification"]
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_query_performance(self) -> Tuple[bool, Dict[str, Any]]:
        """Test query performance"""
        logger.info("Testing query performance")
        
        try:
            num_queries = 50
            start_time = time.time()
            
            successful_queries = 0
            query_times = []
            
            for i in range(num_queries):
                query_start = time.time()
                
                result = fabric_sdk.get_network_statistics()
                query_end = time.time()
                
                if result.get("success"):
                    successful_queries += 1
                    query_times.append(query_end - query_start)
            
            total_time = time.time() - start_time
            
            if query_times:
                avg_time = sum(query_times) / len(query_times)
                min_time = min(query_times)
                max_time = max(query_times)
            else:
                avg_time = min_time = max_time = 0
            
            passed = successful_queries == num_queries and avg_time < 1.0  # 1 second max average
            
            self.performance_metrics["query"] = {
                "total_queries": num_queries,
                "successful_queries": successful_queries,
                "total_time": total_time,
                "avg_time": avg_time,
                "min_time": min_time,
                "max_time": max_time,
                "throughput": successful_queries / total_time if total_time > 0 else 0
            }
            
            return passed, self.performance_metrics["query"]
            
        except Exception as e:
            return False, {"error": str(e)}

class SecurityTestSuite(TestSuite):
    """Security testing suite"""
    
    def __init__(self):
        super().__init__("Security Tests")
        self.security_findings = []
    
    def setup(self):
        """Setup security test environment"""
        logger.info("Setting up security test environment")
        self.setup_complete = True
        logger.info("Security test environment setup complete")
    
    def teardown(self):
        """Cleanup security test environment"""
        logger.info("Cleaning up security test environment")
        self.security_findings = []
        self.teardown_complete = True
        logger.info("Security test environment cleanup complete")
    
    def test_tls_encryption(self) -> Tuple[bool, Dict[str, Any]]:
        """Test TLS encryption"""
        logger.info("Testing TLS encryption")
        
        try:
            # Check if TLS is enabled in network configuration
            with open("configtx.yaml", "r") as f:
                config_content = f.read()
            
            tls_enabled = "TLS" in config_content and "tls" in config_content.lower()
            
            # Check docker-compose for TLS configuration
            with open("docker-compose.yaml", "r") as f:
                compose_content = f.read()
            
            compose_tls = "TLS_ENABLED=true" in compose_content and "tls" in compose_content.lower()
            
            passed = tls_enabled and compose_tls
            
            return passed, {
                "configtx_tls": tls_enabled,
                "compose_tls": compose_tls,
                "tls_configured": passed
            }
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_access_control_bypass(self) -> Tuple[bool, Dict[str, Any]]:
        """Test access control bypass attempts"""
        logger.info("Testing access control bypass attempts")
        
        try:
            # Test unauthorized access attempts
            unauthorized_attempts = [
                ("student_user", "student", "ECOL", "auditPrivateData", "read"),
                ("student_user", "student", "ECOL", "certificatePrivateData", "write"),
                ("verifier_user", "verifier", "LIMKOWING", "institutionPrivateData", "write"),
                ("external_user", "external", "ECOL", "certificatePrivateData", "read")
            ]
            
            blocked_attempts = 0
            total_attempts = len(unauthorized_attempts)
            
            for user_id, role, institution, collection, operation in unauthorized_attempts:
                result = access_control_manager.check_access_permission(
                    user_id, role, institution, collection, operation
                )
                
                if not result.get("access_granted", True):
                    blocked_attempts += 1
                    self.security_findings.append({
                        "type": "access_blocked",
                        "user_id": user_id,
                        "role": role,
                        "collection": collection,
                        "operation": operation
                    })
            
            passed = blocked_attempts == total_attempts
            
            return passed, {
                "total_attempts": total_attempts,
                "blocked_attempts": blocked_attempts,
                "access_control_effective": passed,
                "findings": self.security_findings
            }
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_data_integrity(self) -> Tuple[bool, Dict[str, Any]]:
        """Test data integrity"""
        logger.info("Testing data integrity")
        
        try:
            # Test certificate hash integrity
            test_cert_hash = f"INTEGRITY_TEST_{int(time.time())}"
            test_data = "Integrity test data"
            
            # Issue certificate
            cert_data = {
                "certificateHash": test_cert_hash,
                "studentId": "INTEGRITY_STU",
                "studentName": "IntegrityStudent",
                "studentSurname": "IntegritySurname",
                "examinationYear": 2023,
                "subjects": [{"name": "Mathematics", "grade": "A", "symbol": "*"}],
                "credits": 5,
                "issueDate": "2023-12-01",
                "issuer": "Integrity University",
                "institutionCode": "ECOL",
                "privateData": test_data
            }
            
            issue_result = fabric_sdk.issue_certificate(cert_data)
            if not issue_result.get("success"):
                return False, {"error": "Failed to issue certificate for integrity test"}
            
            # Retrieve certificate
            retrieve_result = fabric_sdk.get_certificate(test_cert_hash)
            if not retrieve_result.get("success"):
                return False, {"error": "Failed to retrieve certificate for integrity test"}
            
            certificate = retrieve_result.get("certificate")
            
            # Check data integrity
            integrity_checks = {
                "hash_match": certificate.get("certificateHash") == test_cert_hash,
                "student_id_match": certificate.get("studentId") == "INTEGRITY_STU",
                "private_data_match": certificate.get("privateData") == test_data
            }
            
            passed = all(integrity_checks.values())
            
            return passed, {
                "integrity_checks": integrity_checks,
                "data_integrity_maintained": passed,
                "certificate": {
                    "hash": certificate.get("certificateHash"),
                    "studentId": certificate.get("studentId"),
                    "privateDataPresent": certificate.get("privateData") is not None
                }
            }
            
        except Exception as e:
            return False, {"error": str(e)}

class TestRunner:
    """Main test runner"""
    
    def __init__(self):
        self.suites = [
            ChaincodeTestSuite(),
            IntegrationTestSuite(),
            PerformanceTestSuite(),
            SecurityTestSuite()
        ]
        self.results = {}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        logger.info("Starting comprehensive test suite")
        start_time = time.time()
        
        all_results = {}
        total_tests = 0
        total_passed = 0
        total_duration = 0
        
        for suite in self.suites:
            logger.info(f"Running {suite.name}")
            suite_start = time.time()
            
            try:
                # Setup suite
                suite.setup()
                
                # Run tests based on suite type
                if isinstance(suite, ChaincodeTestSuite):
                    suite.run_test("Certificate Issuance", suite.test_certificate_issuance)
                    suite.run_test("Certificate Verification", suite.test_certificate_verification)
                    suite.run_test("Certificate Query", suite.test_certificate_query)
                    suite.run_test("Certificate Revocation", suite.test_certificate_revocation)
                    suite.run_test("Network Statistics", suite.test_network_statistics)
                
                elif isinstance(suite, IntegrationTestSuite):
                    suite.run_test("Channel Creation", suite.test_channel_creation)
                    suite.run_test("Channel Join", suite.test_channel_join)
                    suite.run_test("Cross-Channel Communication", suite.test_cross_channel_communication)
                    suite.run_test("Access Control Permissions", suite.test_access_control_permissions)
                    suite.run_test("Data Encryption", suite.test_data_encryption)
                
                elif isinstance(suite, PerformanceTestSuite):
                    suite.run_test("Certificate Issuance Performance", suite.test_certificate_issuance_performance)
                    suite.run_test("Verification Performance", suite.test_verification_performance)
                    suite.run_test("Query Performance", suite.test_query_performance)
                
                elif isinstance(suite, SecurityTestSuite):
                    suite.run_test("TLS Encryption", suite.test_tls_encryption)
                    suite.run_test("Access Control Bypass", suite.test_access_control_bypass)
                    suite.run_test("Data Integrity", suite.test_data_integrity)
                
                # Teardown suite
                suite.teardown()
                
                # Get suite summary
                suite_summary = suite.get_summary()
                all_results[suite.name] = suite_summary
                
                total_tests += suite_summary["total_tests"]
                total_passed += suite_summary["passed_tests"]
                total_duration += suite_summary["total_duration"]
                
                logger.info(f"{suite.name} completed: {suite_summary['passed_tests']}/{suite_summary['total_tests']} passed")
                
            except Exception as e:
                logger.error(f"Error running {suite.name}: {e}")
                all_results[suite.name] = {
                    "suite_name": suite.name,
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 0,
                    "success_rate": 0,
                    "total_duration": 0,
                    "error": str(e)
                }
        
        overall_duration = time.time() - start_time
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        final_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_duration": overall_duration,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_tests - total_passed,
            "overall_success_rate": overall_success_rate,
            "test_suites": all_results,
            "status": "PASSED" if overall_success_rate >= 95 else "FAILED"
        }
        
        # Save results to file
        self._save_results(final_results)
        
        logger.info(f"Test suite completed: {total_passed}/{total_tests} passed ({overall_success_rate:.1f}%)")
        return final_results
    
    def _save_results(self, results: Dict[str, Any]):
        """Save test results to file"""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            results_file = f"test_results_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Test results saved to {results_file}")
            
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")

def main():
    """Main function for running tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    runner = TestRunner()
    results = runner.run_all_tests()
    
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    print(f"Status: {results['status']}")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['total_passed']}")
    print(f"Failed: {results['total_failed']}")
    print(f"Success Rate: {results['overall_success_rate']:.1f}%")
    print(f"Duration: {results['total_duration']:.2f}s")
    print("="*80)
    
    for suite_name, suite_results in results['test_suites'].items():
        print(f"\n{suite_name}:")
        print(f"  Tests: {suite_results['total_tests']}")
        print(f"  Passed: {suite_results['passed_tests']}")
        print(f"  Success Rate: {suite_results['success_rate']:.1f}%")
        
        if 'error' in suite_results:
            print(f"  Error: {suite_results['error']}")
    
    return results['status'] == 'PASSED'

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
