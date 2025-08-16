"""
Migration Utilities

This module provides utilities for managing the migration from LangChain to LangGraph,
including feature flags, performance comparison, and rollback capabilities.
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import json
import time
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from ..config.graph_config import GraphConfig, MigrationConfig, SystemSelector
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for system comparison"""
    system_name: str
    execution_time: float
    memory_usage: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class ComparisonResult:
    """Result of performance comparison between systems"""
    langchain_metrics: PerformanceMetrics
    langgraph_metrics: PerformanceMetrics
    performance_improvement: float  # Factor improvement (>1.0 means LangGraph is faster)
    recommendation: str
    confidence_score: float  # 0.0 to 1.0
    
    @property
    def langraph_is_better(self) -> bool:
        """Check if LangGraph performed better"""
        return (self.performance_improvement > 1.0 and 
                self.langgraph_metrics.success and 
                self.confidence_score > 0.7)


class MigrationManager:
    """Manages migration between LangChain and LangGraph systems"""
    
    def __init__(self, 
                 migration_config: Optional[MigrationConfig] = None,
                 metrics_storage_path: Optional[str] = None):
        self.config = migration_config or MigrationConfig()
        self.metrics_storage_path = metrics_storage_path
        
        # Performance tracking
        self.performance_history: List[PerformanceMetrics] = []
        self.comparison_results: List[ComparisonResult] = []
        
        # Migration state
        self.current_rollout_percentage = 0.0
        self.migration_active = False
        self.last_evaluation_time = datetime.utcnow()
        
        logger.info(f"MigrationManager initialized with rollout: {self.current_rollout_percentage:.1%}")
    
    @contextmanager
    def performance_tracker(self, system_name: str):
        """Context manager for tracking performance metrics"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        error = None
        
        try:
            yield
        except Exception as e:
            error = str(e)
            raise
        finally:
            execution_time = time.time() - start_time
            end_memory = self._get_memory_usage()
            memory_usage = end_memory - start_memory if start_memory and end_memory else None
            
            metrics = PerformanceMetrics(
                system_name=system_name,
                execution_time=execution_time,
                memory_usage=memory_usage,
                success=error is None,
                error=error
            )
            
            self.record_performance_metrics(metrics)
    
    def record_performance_metrics(self, metrics: PerformanceMetrics):
        """Record performance metrics"""
        self.performance_history.append(metrics)
        
        # Keep only recent metrics (last 1000 entries)
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
        
        # Save to storage if configured
        if self.metrics_storage_path:
            self._save_metrics_to_storage()
        
        logger.debug(f"Recorded metrics for {metrics.system_name}: "
                    f"{metrics.execution_time:.3f}s, success: {metrics.success}")
    
    def compare_systems(self, 
                       langchain_function: Callable,
                       langgraph_function: Callable,
                       test_input: Any,
                       test_name: str = "comparison") -> ComparisonResult:
        """
        Compare performance between LangChain and LangGraph systems.
        
        Args:
            langchain_function: Function using LangChain system
            langgraph_function: Function using LangGraph system
            test_input: Input to test both functions with
            test_name: Name for this test
            
        Returns:
            Comparison result
        """
        logger.info(f"Starting system comparison: {test_name}")
        
        # Test LangChain system
        with self.performance_tracker("langchain"):
            try:
                langchain_result = langchain_function(test_input)
                langchain_success = True
                langchain_error = None
            except Exception as e:
                langchain_result = None
                langchain_success = False
                langchain_error = str(e)
        
        # Test LangGraph system
        with self.performance_tracker("langgraph"):
            try:
                langgraph_result = langgraph_function(test_input)
                langgraph_success = True
                langgraph_error = None
            except Exception as e:
                langgraph_result = None
                langgraph_success = False
                langgraph_error = str(e)
        
        # Get latest metrics
        recent_metrics = self.performance_history[-2:]
        langchain_metrics = next(m for m in recent_metrics if m.system_name == "langchain")
        langgraph_metrics = next(m for m in recent_metrics if m.system_name == "langgraph")
        
        # Calculate performance improvement
        if langchain_metrics.execution_time > 0:
            performance_improvement = langchain_metrics.execution_time / langgraph_metrics.execution_time
        else:
            performance_improvement = 1.0
        
        # Determine recommendation and confidence
        recommendation, confidence = self._generate_recommendation(
            langchain_metrics, langgraph_metrics, performance_improvement
        )
        
        comparison_result = ComparisonResult(
            langchain_metrics=langchain_metrics,
            langgraph_metrics=langgraph_metrics,
            performance_improvement=performance_improvement,
            recommendation=recommendation,
            confidence_score=confidence
        )
        
        self.comparison_results.append(comparison_result)
        
        logger.info(f"Comparison complete: {performance_improvement:.2f}x improvement, "
                   f"recommendation: {recommendation}")
        
        return comparison_result
    
    def should_migrate(self) -> Dict[str, Any]:
        """
        Determine if migration should proceed based on performance data.
        
        Returns:
            Migration decision with reasoning
        """
        if not self.comparison_results:
            return {
                "should_migrate": False,
                "reason": "No performance data available",
                "confidence": 0.0,
                "recommended_rollout": 0.0
            }
        
        # Analyze recent comparison results
        recent_results = self.comparison_results[-10:]  # Last 10 comparisons
        
        successful_comparisons = [r for r in recent_results if r.langgraph_metrics.success]
        if not successful_comparisons:
            return {
                "should_migrate": False,
                "reason": "LangGraph system showing failures",
                "confidence": 0.0,
                "recommended_rollout": 0.0
            }
        
        # Calculate average performance improvement
        avg_improvement = sum(r.performance_improvement for r in successful_comparisons) / len(successful_comparisons)
        success_rate = len(successful_comparisons) / len(recent_results)
        
        # Check if meets thresholds
        meets_performance_threshold = avg_improvement >= self.config.performance_improvement_threshold
        meets_success_threshold = success_rate >= self.config.min_success_rate_threshold
        
        if meets_performance_threshold and meets_success_threshold:
            confidence = min(1.0, (avg_improvement - 1.0) * success_rate)
            recommended_rollout = min(1.0, self.current_rollout_percentage + 0.1)  # Gradual increase
            
            return {
                "should_migrate": True,
                "reason": f"Performance improvement {avg_improvement:.2f}x, success rate {success_rate:.1%}",
                "confidence": confidence,
                "recommended_rollout": recommended_rollout,
                "avg_improvement": avg_improvement,
                "success_rate": success_rate
            }
        else:
            return {
                "should_migrate": False,
                "reason": f"Thresholds not met - improvement: {avg_improvement:.2f}x (need {self.config.performance_improvement_threshold:.2f}x), success: {success_rate:.1%} (need {self.config.min_success_rate_threshold:.1%})",
                "confidence": 0.0,
                "recommended_rollout": max(0.0, self.current_rollout_percentage - 0.05),  # Slight decrease
                "avg_improvement": avg_improvement,
                "success_rate": success_rate
            }
    
    def should_rollback(self) -> Dict[str, Any]:
        """
        Determine if automatic rollback should occur.
        
        Returns:
            Rollback decision with reasoning
        """
        if not self.config.enable_automatic_rollback:
            return {"should_rollback": False, "reason": "Automatic rollback disabled"}
        
        # Check recent performance
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.config.rollback_evaluation_window_minutes)
        recent_metrics = [m for m in self.performance_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"should_rollback": False, "reason": "No recent metrics available"}
        
        # Calculate error rates
        langgraph_metrics = [m for m in recent_metrics if m.system_name == "langgraph"]
        if not langgraph_metrics:
            return {"should_rollback": False, "reason": "No LangGraph metrics in evaluation window"}
        
        error_rate = sum(1 for m in langgraph_metrics if not m.success) / len(langgraph_metrics)
        
        if error_rate >= self.config.rollback_trigger_threshold:
            return {
                "should_rollback": True,
                "reason": f"Error rate {error_rate:.1%} exceeds threshold {self.config.rollback_trigger_threshold:.1%}",
                "error_rate": error_rate,
                "evaluation_window_minutes": self.config.rollback_evaluation_window_minutes,
                "sample_size": len(langgraph_metrics)
            }
        
        return {
            "should_rollback": False,
            "reason": f"Error rate {error_rate:.1%} within acceptable range",
            "error_rate": error_rate
        }
    
    def update_rollout_percentage(self, new_percentage: float) -> bool:
        """
        Update the rollout percentage for gradual migration.
        
        Args:
            new_percentage: New rollout percentage (0.0 to 1.0)
            
        Returns:
            True if update was successful
        """
        if not 0.0 <= new_percentage <= 1.0:
            logger.error(f"Invalid rollout percentage: {new_percentage}")
            return False
        
        old_percentage = self.current_rollout_percentage
        self.current_rollout_percentage = new_percentage
        
        logger.info(f"Updated rollout percentage from {old_percentage:.1%} to {new_percentage:.1%}")
        return True
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        rollback_decision = self.should_rollback()
        migration_decision = self.should_migrate()
        
        return {
            "migration_active": self.migration_active,
            "current_rollout_percentage": self.current_rollout_percentage,
            "total_comparisons": len(self.comparison_results),
            "total_metrics": len(self.performance_history),
            "last_evaluation": self.last_evaluation_time.isoformat(),
            "rollback_status": rollback_decision,
            "migration_status": migration_decision,
            "config": asdict(self.config)
        }
    
    def _generate_recommendation(self, 
                               langchain_metrics: PerformanceMetrics,
                               langgraph_metrics: PerformanceMetrics,
                               performance_improvement: float) -> tuple[str, float]:
        """Generate recommendation and confidence score"""
        
        if not langgraph_metrics.success:
            return "stick_with_langchain", 0.9
        
        if not langchain_metrics.success:
            return "use_langgraph", 0.8
        
        if performance_improvement >= 2.0:
            return "strongly_recommend_langgraph", 0.9
        elif performance_improvement >= 1.2:
            return "recommend_langgraph", 0.7
        elif performance_improvement >= 0.9:
            return "neutral", 0.5
        else:
            return "recommend_langchain", 0.7
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)  # Convert to MB
        except ImportError:
            return None
        except Exception:
            return None
    
    def _save_metrics_to_storage(self):
        """Save metrics to persistent storage"""
        if not self.metrics_storage_path:
            return
        
        try:
            data = {
                "performance_history": [asdict(m) for m in self.performance_history[-100:]],  # Save last 100
                "comparison_results": [asdict(r) for r in self.comparison_results[-50:]],  # Save last 50
                "migration_status": {
                    "current_rollout_percentage": self.current_rollout_percentage,
                    "migration_active": self.migration_active,
                    "last_evaluation_time": self.last_evaluation_time.isoformat()
                }
            }
            
            with open(self.metrics_storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save metrics to storage: {e}")


class FeatureFlags:
    """Feature flag management for migration"""
    
    def __init__(self, config: GraphConfig):
        self.config = config
        self._flags = {
            "enable_langgraph": config.enable_langgraph,
            "enable_parallel_processing": config.enable_parallel_processing,
            "enable_ab_testing": config.enable_ab_testing,
            "enable_performance_monitoring": config.enable_performance_monitoring,
            "enable_automatic_retry": config.enable_automatic_retry,
            "enable_circuit_breaker": config.enable_circuit_breaker
        }
    
    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        return self._flags.get(flag_name, False)
    
    def enable_flag(self, flag_name: str):
        """Enable a feature flag"""
        if flag_name in self._flags:
            self._flags[flag_name] = True
            logger.info(f"Enabled feature flag: {flag_name}")
    
    def disable_flag(self, flag_name: str):
        """Disable a feature flag"""
        if flag_name in self._flags:
            self._flags[flag_name] = False
            logger.info(f"Disabled feature flag: {flag_name}")
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags"""
        return self._flags.copy()


def create_migration_manager(config_path: Optional[str] = None) -> MigrationManager:
    """Factory function to create a migration manager"""
    migration_config = MigrationConfig()
    
    # Load custom config if provided
    if config_path:
        try:
            import yaml
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                migration_config = MigrationConfig(**config_data)
        except Exception as e:
            logger.warning(f"Failed to load migration config from {config_path}: {e}")
    
    return MigrationManager(migration_config=migration_config)