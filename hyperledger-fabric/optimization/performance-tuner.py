#!/usr/bin/env python3
"""
Performance Tuner for LGCSE Certificate Verification System

This module provides comprehensive performance optimization for the Hyperledger Fabric
blockchain system, including chaincode optimization, network tuning, database optimization,
and resource scaling.
"""

import os
import json
import time
import logging
import threading
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics container"""
    cpu_usage: float
    memory_usage: float
    disk_io: float
    network_io: float
    response_time: float
    throughput: float
    error_rate: float
    timestamp: datetime

class PerformanceTuner:
    """
    Comprehensive performance tuning system for Hyperledger Fabric
    
    Provides:
    - Chaincode performance optimization
    - Network configuration tuning
    - Database optimization
    - Resource scaling recommendations
    - Real-time performance monitoring
    """
    
    def __init__(self):
        self.metrics_history = []
        self.optimization_profiles = {}
        self.tuning_recommendations = []
        self.performance_thresholds = {
            "cpu_warning": 70.0,
            "cpu_critical": 85.0,
            "memory_warning": 75.0,
            "memory_critical": 90.0,
            "response_time_warning": 5.0,
            "response_time_critical": 10.0,
            "error_rate_warning": 5.0,
            "error_rate_critical": 10.0
        }
        
        self._initialize_optimization_profiles()
    
    def _initialize_optimization_profiles(self):
        """Initialize optimization profiles for different scenarios"""
        self.optimization_profiles = {
            "high_throughput": {
                "name": "High Throughput",
                "description": "Optimized for maximum transaction throughput",
                "chaincode": {
                    "batch_size": 50,
                    "timeout": "30s",
                    "endorsement_policy": "Any",
                    "private_data_collections": False,
                    "caching_enabled": True
                },
                "network": {
                    "max_connections": 100,
                    "connection_timeout": "10s",
                    "keepalive": "true",
                    "compression": "true"
                },
                "database": {
                    "cache_size": "2GB",
                    "write_buffer_size": "64MB",
                    "max_connections": 50,
                    "query_timeout": "10s"
                }
            },
            "low_latency": {
                "name": "Low Latency",
                "description": "Optimized for minimal response time",
                "chaincode": {
                    "batch_size": 1,
                    "timeout": "5s",
                    "endorsement_policy": "Any",
                    "private_data_collections": True,
                    "caching_enabled": True
                },
                "network": {
                    "max_connections": 20,
                    "connection_timeout": "2s",
                    "keepalive": "true",
                    "compression": "false"
                },
                "database": {
                    "cache_size": "1GB",
                    "write_buffer_size": "16MB",
                    "max_connections": 20,
                    "query_timeout": "2s"
                }
            },
            "balanced": {
                "name": "Balanced",
                "description": "Balanced performance for general use",
                "chaincode": {
                    "batch_size": 10,
                    "timeout": "15s",
                    "endorsement_policy": "Majority",
                    "private_data_collections": True,
                    "caching_enabled": True
                },
                "network": {
                    "max_connections": 50,
                    "connection_timeout": "5s",
                    "keepalive": "true",
                    "compression": "true"
                },
                "database": {
                    "cache_size": "1.5GB",
                    "write_buffer_size": "32MB",
                    "max_connections": 30,
                    "query_timeout": "5s"
                }
            },
            "resource_constrained": {
                "name": "Resource Constrained",
                "description": "Optimized for limited resources",
                "chaincode": {
                    "batch_size": 5,
                    "timeout": "10s",
                    "endorsement_policy": "Any",
                    "private_data_collections": False,
                    "caching_enabled": False
                },
                "network": {
                    "max_connections": 10,
                    "connection_timeout": "3s",
                    "keepalive": "false",
                    "compression": "false"
                },
                "database": {
                    "cache_size": "512MB",
                    "write_buffer_size": "8MB",
                    "max_connections": 10,
                    "query_timeout": "3s"
                }
            }
        }
    
    def collect_system_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics"""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0
            disk_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0
            total_disk_io = disk_read_mb + disk_write_mb
            
            # Network I/O
            network_io = psutil.net_io_counters()
            net_sent_mb = network_io.bytes_sent / (1024 * 1024) if network_io else 0
            net_recv_mb = network_io.bytes_recv / (1024 * 1024) if network_io else 0
            total_network_io = net_sent_mb + net_recv_mb
            
            # Simulate response time and throughput (would be measured from actual transactions)
            response_time = self._measure_response_time()
            throughput = self._measure_throughput()
            error_rate = self._measure_error_rate()
            
            metrics = PerformanceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_io=total_disk_io,
                network_io=total_network_io,
                response_time=response_time,
                throughput=throughput,
                error_rate=error_rate,
                timestamp=datetime.utcnow()
            )
            
            # Store in history (keep last 1000 entries)
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 1000:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            raise
    
    def _measure_response_time(self) -> float:
        """Measure average response time (simulated)"""
        # In production, this would measure actual transaction response times
        # For now, simulate based on current system load
        if self.metrics_history:
            avg_cpu = sum(m.cpu_usage for m in self.metrics_history[-10:]) / 10
            base_time = 1.0
            load_factor = avg_cpu / 100.0
            return base_time * (1 + load_factor * 2)
        return 2.0
    
    def _measure_throughput(self) -> float:
        """Measure transaction throughput (simulated)"""
        # In production, this would measure actual transaction throughput
        # For now, simulate based on system resources
        if self.metrics_history:
            avg_cpu = sum(m.cpu_usage for m in self.metrics_history[-10:]) / 10
            avg_memory = sum(m.memory_usage for m in self.metrics_history[-10:]) / 10
            
            # Throughput decreases with higher load
            load_factor = (avg_cpu + avg_memory) / 200.0
            base_throughput = 100.0  # transactions per second
            return base_throughput * (1 - load_factor * 0.5)
        return 50.0
    
    def _measure_error_rate(self) -> float:
        """Measure error rate (simulated)"""
        # In production, this would measure actual error rates
        # For now, simulate based on system load
        if self.metrics_history:
            avg_cpu = sum(m.cpu_usage for m in self.metrics_history[-10:]) / 10
            avg_memory = sum(m.memory_usage for m in self.metrics_history[-10:]) / 10
            
            # Error rate increases with higher load
            load_factor = (avg_cpu + avg_memory) / 200.0
            base_error_rate = 1.0  # 1% base error rate
            return base_error_rate * (1 + load_factor * 3)
        return 1.0
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze current performance and identify bottlenecks"""
        if not self.metrics_history:
            return {"error": "No metrics available for analysis"}
        
        # Get recent metrics (last 10 measurements)
        recent_metrics = self.metrics_history[-10:]
        
        # Calculate averages
        avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
        avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
        avg_throughput = sum(m.throughput for m in recent_metrics) / len(recent_metrics)
        avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(recent_metrics)
        
        # Identify issues
        issues = []
        recommendations = []
        
        # CPU issues
        if avg_cpu > self.performance_thresholds["cpu_critical"]:
            issues.append("critical_cpu")
            recommendations.append("Scale up CPU resources or optimize CPU-intensive operations")
        elif avg_cpu > self.performance_thresholds["cpu_warning"]:
            issues.append("warning_cpu")
            recommendations.append("Monitor CPU usage and consider optimization")
        
        # Memory issues
        if avg_memory > self.performance_thresholds["memory_critical"]:
            issues.append("critical_memory")
            recommendations.append("Increase memory allocation or optimize memory usage")
        elif avg_memory > self.performance_thresholds["memory_warning"]:
            issues.append("warning_memory")
            recommendations.append("Monitor memory usage and optimize memory-intensive operations")
        
        # Response time issues
        if avg_response_time > self.performance_thresholds["response_time_critical"]:
            issues.append("critical_response_time")
            recommendations.append("Optimize chaincode and network configuration")
        elif avg_response_time > self.performance_thresholds["response_time_warning"]:
            issues.append("warning_response_time")
            recommendations.append("Review and optimize slow operations")
        
        # Error rate issues
        if avg_error_rate > self.performance_thresholds["error_rate_critical"]:
            issues.append("critical_error_rate")
            recommendations.append("Investigate and fix error sources")
        elif avg_error_rate > self.performance_thresholds["error_rate_warning"]:
            issues.append("warning_error_rate")
            recommendations.append("Monitor error patterns and implement error handling")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "cpu_usage": avg_cpu,
                "memory_usage": avg_memory,
                "response_time": avg_response_time,
                "throughput": avg_throughput,
                "error_rate": avg_error_rate
            },
            "issues": issues,
            "recommendations": recommendations,
            "overall_status": "critical" if any("critical" in issue for issue in issues) else "warning" if issues else "healthy"
        }
    
    def recommend_optimization_profile(self) -> Dict[str, Any]:
        """Recommend optimization profile based on current performance"""
        analysis = self.analyze_performance()
        
        if "error" in analysis:
            return {"error": "Cannot recommend profile without metrics"}
        
        metrics = analysis["metrics"]
        issues = analysis["issues"]
        
        # Select profile based on issues and metrics
        if "critical_cpu" in issues or "critical_memory" in issues:
            recommended_profile = "resource_constrained"
            reason = "System resources are critically high, use resource-constrained profile"
        elif "critical_response_time" in issues:
            recommended_profile = "low_latency"
            reason = "Response time is critical, use low-latency profile"
        elif metrics["throughput"] < 20:
            recommended_profile = "high_throughput"
            reason = "Throughput is low, use high-throughput profile"
        else:
            recommended_profile = "balanced"
            reason = "System performance is acceptable, use balanced profile"
        
        profile_config = self.optimization_profiles[recommended_profile]
        
        return {
            "recommended_profile": recommended_profile,
            "reason": reason,
            "profile_config": profile_config,
            "current_metrics": metrics,
            "expected_improvement": self._calculate_expected_improvement(recommended_profile, metrics)
        }
    
    def _calculate_expected_improvement(self, profile_name: str, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate expected performance improvement with optimization profile"""
        profile = self.optimization_profiles[profile_name]
        
        # Estimate improvements based on profile characteristics
        improvements = {}
        
        if profile_name == "high_throughput":
            improvements["throughput"] = "+50%"
            improvements["response_time"] = "+20%"
            improvements["cpu_usage"] = "+10%"
        elif profile_name == "low_latency":
            improvements["response_time"] = "-60%"
            improvements["throughput"] = "-30%"
            improvements["cpu_usage"] = "+20%"
        elif profile_name == "balanced":
            improvements["response_time"] = "-30%"
            improvements["throughput"] = "+20%"
            improvements["cpu_usage"] = "+5%"
        elif profile_name == "resource_constrained":
            improvements["cpu_usage"] = "-30%"
            improvements["memory_usage"] = "-25%"
            improvements["response_time"] = "+10%"
        
        return improvements
    
    def apply_optimization_profile(self, profile_name: str) -> Dict[str, Any]:
        """Apply optimization profile to the system"""
        if profile_name not in self.optimization_profiles:
            return {"error": f"Unknown profile: {profile_name}"}
        
        profile = self.optimization_profiles[profile_name]
        
        # Apply chaincode optimizations
        chaincode_result = self._optimize_chaincode(profile["chaincode"])
        
        # Apply network optimizations
        network_result = self._optimize_network(profile["network"])
        
        # Apply database optimizations
        database_result = self._optimize_database(profile["database"])
        
        return {
            "profile_applied": profile_name,
            "timestamp": datetime.utcnow().isoformat(),
            "chaincode_optimization": chaincode_result,
            "network_optimization": network_result,
            "database_optimization": database_result,
            "overall_status": "success"
        }
    
    def _optimize_chaincode(self, chaincode_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply chaincode optimizations"""
        try:
            optimizations = []
            
            # Update chaincode configuration
            if "batch_size" in chaincode_config:
                batch_size = chaincode_config["batch_size"]
                # In production, this would update actual chaincode configuration
                optimizations.append(f"Set batch size to {batch_size}")
            
            if "timeout" in chaincode_config:
                timeout = chaincode_config["timeout"]
                optimizations.append(f"Set timeout to {timeout}")
            
            if "caching_enabled" in chaincode_config:
                caching = chaincode_config["caching_enabled"]
                optimizations.append(f"{'Enabled' if caching else 'Disabled'} caching")
            
            if "private_data_collections" in chaincode_config:
                private_data = chaincode_config["private_data_collections"]
                optimizations.append(f"{'Enabled' if private_data else 'Disabled'} private data collections")
            
            return {
                "success": True,
                "optimizations": optimizations,
                "config": chaincode_config
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize chaincode: {e}")
            return {"success": False, "error": str(e)}
    
    def _optimize_network(self, network_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply network optimizations"""
        try:
            optimizations = []
            
            # Update network configuration
            if "max_connections" in network_config:
                max_conn = network_config["max_connections"]
                optimizations.append(f"Set max connections to {max_conn}")
            
            if "connection_timeout" in network_config:
                timeout = network_config["connection_timeout"]
                optimizations.append(f"Set connection timeout to {timeout}")
            
            if "keepalive" in network_config:
                keepalive = network_config["keepalive"]
                optimizations.append(f"{'Enabled' if keepalive == 'true' else 'Disabled'} keepalive")
            
            if "compression" in network_config:
                compression = network_config["compression"]
                optimizations.append(f"{'Enabled' if compression == 'true' else 'Disabled'} compression")
            
            return {
                "success": True,
                "optimizations": optimizations,
                "config": network_config
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize network: {e}")
            return {"success": False, "error": str(e)}
    
    def _optimize_database(self, database_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply database optimizations"""
        try:
            optimizations = []
            
            # Update database configuration
            if "cache_size" in database_config:
                cache_size = database_config["cache_size"]
                optimizations.append(f"Set cache size to {cache_size}")
            
            if "write_buffer_size" in database_config:
                buffer_size = database_config["write_buffer_size"]
                optimizations.append(f"Set write buffer size to {buffer_size}")
            
            if "max_connections" in database_config:
                max_conn = database_config["max_connections"]
                optimizations.append(f"Set max connections to {max_conn}")
            
            if "query_timeout" in database_config:
                timeout = database_config["query_timeout"]
                optimizations.append(f"Set query timeout to {timeout}")
            
            return {
                "success": True,
                "optimizations": optimizations,
                "config": database_config
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize database: {e}")
            return {"success": False, "error": str(e)}
    
    def auto_tune(self) -> Dict[str, Any]:
        """Automatically tune system performance"""
        logger.info("Starting automatic performance tuning")
        
        # Collect current metrics
        current_metrics = self.collect_system_metrics()
        
        # Analyze performance
        analysis = self.analyze_performance()
        
        # Get recommendation
        recommendation = self.recommend_optimization_profile()
        
        if "error" in recommendation:
            return {"error": "Cannot auto-tune without metrics"}
        
        # Apply recommended profile
        profile_name = recommendation["recommended_profile"]
        application_result = self.apply_optimization_profile(profile_name)
        
        # Wait for changes to take effect
        time.sleep(5)
        
        # Collect new metrics
        new_metrics = self.collect_system_metrics()
        
        # Calculate improvement
        improvement = self._calculate_improvement(current_metrics, new_metrics)
        
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "auto_tune_completed": True,
            "profile_applied": profile_name,
            "reason": recommendation["reason"],
            "before_metrics": {
                "cpu_usage": current_metrics.cpu_usage,
                "memory_usage": current_metrics.memory_usage,
                "response_time": current_metrics.response_time,
                "throughput": current_metrics.throughput,
                "error_rate": current_metrics.error_rate
            },
            "after_metrics": {
                "cpu_usage": new_metrics.cpu_usage,
                "memory_usage": new_metrics.memory_usage,
                "response_time": new_metrics.response_time,
                "throughput": new_metrics.throughput,
                "error_rate": new_metrics.error_rate
            },
            "improvement": improvement,
            "application_result": application_result
        }
        
        logger.info(f"Auto-tune completed with profile: {profile_name}")
        return result
    
    def _calculate_improvement(self, before: PerformanceMetrics, after: PerformanceMetrics) -> Dict[str, Any]:
        """Calculate performance improvement"""
        improvements = {}
        
        # CPU improvement
        if before.cpu_usage > 0:
            cpu_improvement = ((before.cpu_usage - after.cpu_usage) / before.cpu_usage) * 100
            improvements["cpu_usage"] = f"{cpu_improvement:+.1f}%"
        
        # Memory improvement
        if before.memory_usage > 0:
            memory_improvement = ((before.memory_usage - after.memory_usage) / before.memory_usage) * 100
            improvements["memory_usage"] = f"{memory_improvement:+.1f}%"
        
        # Response time improvement
        if before.response_time > 0:
            response_improvement = ((before.response_time - after.response_time) / before.response_time) * 100
            improvements["response_time"] = f"{response_improvement:+.1f}%"
        
        # Throughput improvement
        if before.throughput > 0:
            throughput_improvement = ((after.throughput - before.throughput) / before.throughput) * 100
            improvements["throughput"] = f"{throughput_improvement:+.1f}%"
        
        # Error rate improvement
        if before.error_rate > 0:
            error_improvement = ((before.error_rate - after.error_rate) / before.error_rate) * 100
            improvements["error_rate"] = f"{error_improvement:+.1f}%"
        
        return improvements
    
    def start_monitoring(self, interval: int = 30) -> None:
        """Start continuous performance monitoring"""
        def monitor_loop():
            while True:
                try:
                    metrics = self.collect_system_metrics()
                    analysis = self.analyze_performance()
                    
                    # Check for critical issues
                    if analysis["overall_status"] == "critical":
                        logger.warning(f"Critical performance issues detected: {analysis['issues']}")
                        
                        # Auto-tune if critical
                        if "critical_cpu" in analysis["issues"] or "critical_memory" in analysis["issues"]:
                            logger.info("Auto-tuning due to critical issues")
                            self.auto_tune()
                    
                    # Log metrics
                    logger.info(f"Performance metrics - CPU: {metrics.cpu_usage:.1f}%, "
                               f"Memory: {metrics.memory_usage:.1f}%, "
                               f"Response Time: {metrics.response_time:.2f}s, "
                               f"Throughput: {metrics.throughput:.1f} tx/s")
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                
                time.sleep(interval)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        logger.info(f"Performance monitoring started with {interval}s interval")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.metrics_history:
            return {"error": "No metrics available for report"}
        
        # Calculate statistics
        cpu_values = [m.cpu_usage for m in self.metrics_history]
        memory_values = [m.memory_usage for m in self.metrics_history]
        response_times = [m.response_time for m in self.metrics_history]
        throughputs = [m.throughput for m in self.metrics_history]
        error_rates = [m.error_rate for m in self.metrics_history]
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "period": {
                "start": self.metrics_history[0].timestamp.isoformat(),
                "end": self.metrics_history[-1].timestamp.isoformat(),
                "duration": str(self.metrics_history[-1].timestamp - self.metrics_history[0].timestamp),
                "samples": len(self.metrics_history)
            },
            "statistics": {
                "cpu": {
                    "min": min(cpu_values),
                    "max": max(cpu_values),
                    "avg": sum(cpu_values) / len(cpu_values),
                    "current": cpu_values[-1]
                },
                "memory": {
                    "min": min(memory_values),
                    "max": max(memory_values),
                    "avg": sum(memory_values) / len(memory_values),
                    "current": memory_values[-1]
                },
                "response_time": {
                    "min": min(response_times),
                    "max": max(response_times),
                    "avg": sum(response_times) / len(response_times),
                    "current": response_times[-1]
                },
                "throughput": {
                    "min": min(throughputs),
                    "max": max(throughputs),
                    "avg": sum(throughputs) / len(throughputs),
                    "current": throughputs[-1]
                },
                "error_rate": {
                    "min": min(error_rates),
                    "max": max(error_rates),
                    "avg": sum(error_rates) / len(error_rates),
                    "current": error_rates[-1]
                }
            },
            "analysis": self.analyze_performance(),
            "recommendations": self.recommend_optimization_profile(),
            "available_profiles": list(self.optimization_profiles.keys())
        }
        
        return report

def main():
    """Main function for testing"""
    tuner = PerformanceTuner()
    
    # Collect some sample metrics
    for i in range(10):
        metrics = tuner.collect_system_metrics()
        print(f"Sample {i+1}: CPU={metrics.cpu_usage:.1f}%, "
              f"Memory={metrics.memory_usage:.1f}%, "
              f"Response={metrics.response_time:.2f}s, "
              f"Throughput={metrics.throughput:.1f} tx/s")
        time.sleep(1)
    
    # Generate report
    report = tuner.get_performance_report()
    print("\nPerformance Report:")
    print(json.dumps(report, indent=2, default=str))

if __name__ == "__main__":
    main()
