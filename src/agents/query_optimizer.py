"""
Advanced Query Optimization Module

Implements sophisticated query optimization capabilities including:
- Semantic query analysis
- Query rewriting and expansion
- Multi-query strategies
- Dynamic retrieval optimization
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import json
from ..utils.logging import get_logger

logger = get_logger(__name__)

class QueryType(Enum):
    """Types of queries for optimization"""
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    COMPARATIVE = "comparative"
    PROCEDURAL = "procedural"
    EXPLORATORY = "exploratory"
    TROUBLESHOOTING = "troubleshooting"

class OptimizationStrategy(Enum):
    """Query optimization strategies"""
    EXPANSION = "expansion"
    REWRITING = "rewriting"
    DECOMPOSITION = "decomposition"
    SYNONYM_REPLACEMENT = "synonym_replacement"
    CONTEXT_ENHANCEMENT = "context_enhancement"
    MULTI_QUERY = "multi_query"

@dataclass
class QueryOptimizationResult:
    """Result of query optimization"""
    original_query: str
    optimized_queries: List[str]
    strategy_used: OptimizationStrategy
    confidence_score: float
    reasoning: str
    metadata: Dict[str, Any]

class AdvancedQueryOptimizer:
    """
    Advanced query optimizer that implements sophisticated optimization strategies
    
    Features:
    - Semantic query analysis
    - Query rewriting and expansion
    - Multi-query decomposition
    - Dynamic strategy selection
    - Context-aware optimization
    """
    
    def __init__(self, llm, config: Optional[Dict[str, Any]] = None):
        self.llm = llm
        self.config = config or self._get_default_config()
        
        # Initialize optimization components
        self.semantic_analyzer = SemanticQueryAnalyzer(llm, self.config)
        self.query_rewriter = QueryRewriter(llm, self.config)
        self.query_decomposer = QueryDecomposer(llm, self.config)
        self.strategy_selector = OptimizationStrategySelector(self.config)
        
        # Load optimization resources
        self.synonyms = self._load_synonyms()
        self.query_patterns = self._load_query_patterns()
        self.context_keywords = self._load_context_keywords()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for query optimization"""
        return {
            "enable_semantic_analysis": True,
            "enable_query_expansion": True,
            "enable_query_decomposition": True,
            "enable_synonym_replacement": True,
            "max_expansion_queries": 3,
            "max_decomposition_queries": 5,
            "confidence_threshold": 0.7,
            "enable_context_enhancement": True,
            "enable_multi_query_strategies": True,
            "optimization_timeout": 10.0
        }
    
    def optimize_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> QueryOptimizationResult:
        """
        Optimize a query using advanced optimization strategies
        
        Args:
            query: Original query to optimize
            context: Optional context information for optimization
            
        Returns:
            QueryOptimizationResult with optimization details
        """
        logger.info(f"Starting advanced query optimization for: {query[:100]}...")
        
        try:
            # Step 1: Semantic analysis
            semantic_analysis = self.semantic_analyzer.analyze_query(query)
            logger.info(f"Semantic analysis: type={semantic_analysis.query_type}, complexity={semantic_analysis.complexity}")
            
            # Step 2: Select optimization strategy
            strategy = self.strategy_selector.select_strategy(semantic_analysis, context)
            logger.info(f"Selected optimization strategy: {strategy}")
            
            # Step 3: Apply optimization strategy
            if strategy == OptimizationStrategy.EXPANSION:
                optimized_queries = self._apply_expansion_strategy(query, semantic_analysis)
            elif strategy == OptimizationStrategy.REWRITING:
                optimized_queries = self._apply_rewriting_strategy(query, semantic_analysis)
            elif strategy == OptimizationStrategy.DECOMPOSITION:
                optimized_queries = self._apply_decomposition_strategy(query, semantic_analysis)
            elif strategy == OptimizationStrategy.MULTI_QUERY:
                optimized_queries = self._apply_multi_query_strategy(query, semantic_analysis)
            else:
                optimized_queries = [query]  # No optimization
            
            # Step 4: Calculate confidence score
            confidence_score = self._calculate_confidence_score(query, optimized_queries, strategy)
            
            # Step 5: Generate reasoning
            reasoning = self._generate_optimization_reasoning(strategy, semantic_analysis, optimized_queries)
            
            # Step 6: Create result
            result = QueryOptimizationResult(
                original_query=query,
                optimized_queries=optimized_queries,
                strategy_used=strategy,
                confidence_score=confidence_score,
                reasoning=reasoning,
                metadata={
                    "semantic_analysis": semantic_analysis.__dict__,
                    "context": context,
                    "optimization_time": 0.0  # Would measure actual time
                }
            )
            
            logger.info(f"Query optimization completed: {len(optimized_queries)} optimized queries, confidence: {confidence_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Query optimization failed: {str(e)}")
            # Return fallback result
            return QueryOptimizationResult(
                original_query=query,
                optimized_queries=[query],
                strategy_used=OptimizationStrategy.REWRITING,
                confidence_score=0.5,
                reasoning=f"Optimization failed, using original query: {str(e)}",
                metadata={"error": str(e)}
            )
    
    def _apply_expansion_strategy(self, query: str, semantic_analysis) -> List[str]:
        """Apply query expansion strategy"""
        expanded_queries = [query]
        
        # Add synonym-based expansions
        if self.config.get("enable_synonym_replacement", True):
            synonym_expansions = self.query_rewriter.expand_with_synonyms(query)
            expanded_queries.extend(synonym_expansions)
        
        # Add context-based expansions
        if self.config.get("enable_context_enhancement", True):
            context_expansions = self.query_rewriter.expand_with_context(query, semantic_analysis)
            expanded_queries.extend(context_expansions)
        
        # Limit number of expansions
        max_expansions = self.config.get("max_expansion_queries", 3)
        return expanded_queries[:max_expansions]
    
    def _apply_rewriting_strategy(self, query: str, semantic_analysis) -> List[str]:
        """Apply query rewriting strategy"""
        rewritten_queries = [query]
        
        # Apply semantic rewriting
        semantic_rewrites = self.query_rewriter.rewrite_semantically(query, semantic_analysis)
        rewritten_queries.extend(semantic_rewrites)
        
        # Apply pattern-based rewriting
        pattern_rewrites = self.query_rewriter.rewrite_by_patterns(query, semantic_analysis)
        rewritten_queries.extend(pattern_rewrites)
        
        return list(set(rewritten_queries))  # Remove duplicates
    
    def _apply_decomposition_strategy(self, query: str, semantic_analysis) -> List[str]:
        """Apply query decomposition strategy"""
        decomposed_queries = self.query_decomposer.decompose_query(query, semantic_analysis)
        
        # Limit number of decomposed queries
        max_decompositions = self.config.get("max_decomposition_queries", 5)
        return decomposed_queries[:max_decompositions]
    
    def _apply_multi_query_strategy(self, query: str, semantic_analysis) -> List[str]:
        """Apply multi-query strategy combining multiple approaches"""
        queries = [query]
        
        # Combine expansion and rewriting
        if self.config.get("enable_query_expansion", True):
            expansion_queries = self._apply_expansion_strategy(query, semantic_analysis)
            queries.extend(expansion_queries)
        
        if self.config.get("enable_query_decomposition", True):
            decomposition_queries = self._apply_decomposition_strategy(query, semantic_analysis)
            queries.extend(decomposition_queries)
        
        # Remove duplicates and limit
        unique_queries = list(dict.fromkeys(queries))  # Preserve order
        max_queries = max(self.config.get("max_expansion_queries", 3), 
                         self.config.get("max_decomposition_queries", 5))
        
        return unique_queries[:max_queries]
    
    def _calculate_confidence_score(self, original_query: str, optimized_queries: List[str], 
                                   strategy: OptimizationStrategy) -> float:
        """Calculate confidence score for optimization result"""
        base_score = 0.5
        
        # Strategy-specific scoring
        if strategy == OptimizationStrategy.EXPANSION:
            base_score += 0.2
        elif strategy == OptimizationStrategy.REWRITING:
            base_score += 0.3
        elif strategy == OptimizationStrategy.DECOMPOSITION:
            base_score += 0.4
        elif strategy == OptimizationStrategy.MULTI_QUERY:
            base_score += 0.3
        
        # Query count scoring
        if len(optimized_queries) > 1:
            base_score += 0.1
        
        # Original query preservation
        if original_query in optimized_queries:
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _generate_optimization_reasoning(self, strategy: OptimizationStrategy, 
                                       semantic_analysis, optimized_queries: List[str]) -> str:
        """Generate reasoning for optimization decisions"""
        reasoning_parts = [
            f"Applied {strategy.value} strategy based on query analysis.",
            f"Query type: {semantic_analysis.query_type.value}",
            f"Complexity: {semantic_analysis.complexity}",
            f"Generated {len(optimized_queries)} optimized queries."
        ]
        
        if len(optimized_queries) > 1:
            reasoning_parts.append("Multiple queries will be used for comprehensive retrieval.")
        
        return " ".join(reasoning_parts)
    
    def _load_synonyms(self) -> Dict[str, List[str]]:
        """Load synonym dictionary for query expansion"""
        # Basic synonym dictionary - in practice, this would be loaded from a file or database
        return {
            "error": ["bug", "issue", "problem", "fault", "defect"],
            "function": ["method", "procedure", "routine", "subroutine"],
            "class": ["type", "object", "entity", "model"],
            "file": ["document", "resource", "asset"],
            "code": ["source", "implementation", "logic"],
            "test": ["verify", "validate", "check", "assert"],
            "config": ["configuration", "settings", "parameters", "options"],
            "api": ["interface", "endpoint", "service", "method"],
            "database": ["db", "storage", "repository", "store"],
            "user": ["client", "customer", "end-user", "consumer"]
        }
    
    def _load_query_patterns(self) -> Dict[str, List[str]]:
        """Load query patterns for optimization"""
        return {
            "how_to": [
                "how do i", "how to", "what's the way to", "steps to",
                "procedure for", "method to", "approach for"
            ],
            "what_is": [
                "what is", "what are", "define", "explain", "describe",
                "tell me about", "give me information about"
            ],
            "compare": [
                "compare", "difference between", "vs", "versus",
                "which is better", "pros and cons"
            ],
            "troubleshoot": [
                "fix", "solve", "resolve", "debug", "error",
                "problem", "issue", "not working"
            ]
        }
    
    def _load_context_keywords(self) -> Dict[str, List[str]]:
        """Load context keywords for enhancement"""
        return {
            "code_analysis": ["code", "function", "class", "method", "implementation"],
            "configuration": ["config", "settings", "parameters", "options", "environment"],
            "architecture": ["design", "structure", "pattern", "architecture", "system"],
            "performance": ["speed", "efficiency", "optimization", "performance", "scalability"],
            "security": ["security", "authentication", "authorization", "encryption", "vulnerability"]
        }

class SemanticQueryAnalyzer:
    """Analyzes queries semantically to determine type and characteristics"""
    
    def __init__(self, llm, config: Dict[str, Any]):
        self.llm = llm
        self.config = config
    
    def analyze_query(self, query: str):
        """Analyze query for semantic characteristics"""
        # Simple analysis - in practice, use LLM for sophisticated analysis
        query_lower = query.lower()
        
        # Determine query type
        query_type = self._determine_query_type(query_lower)
        
        # Determine complexity
        complexity = self._determine_complexity(query_lower)
        
        # Create analysis result
        return SemanticAnalysisResult(
            query_type=query_type,
            complexity=complexity,
            keywords=self._extract_keywords(query_lower),
            intent=self._determine_intent(query_lower),
            domain=self._determine_domain(query_lower)
        )
    
    def _determine_query_type(self, query: str) -> QueryType:
        """Determine the type of query"""
        if any(phrase in query for phrase in ["how to", "how do", "steps", "procedure"]):
            return QueryType.PROCEDURAL
        elif any(phrase in query for phrase in ["compare", "difference", "vs", "versus"]):
            return QueryType.COMPARATIVE
        elif any(phrase in query for phrase in ["analyze", "investigate", "examine"]):
            return QueryType.ANALYTICAL
        elif any(phrase in query for phrase in ["explore", "discover", "find"]):
            return QueryType.EXPLORATORY
        elif any(phrase in query for phrase in ["fix", "error", "problem", "issue"]):
            return QueryType.TROUBLESHOOTING
        else:
            return QueryType.FACTUAL
    
    def _determine_complexity(self, query: str) -> str:
        """Determine query complexity"""
        word_count = len(query.split())
        
        if word_count <= 5:
            return "low"
        elif word_count <= 12:  # Increased threshold for medium complexity
            return "medium"
        else:
            return "high"
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract key terms from query"""
        # Simple keyword extraction - in practice, use NLP techniques
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "how", "what", "set", "up"}
        words = query.split()
        keywords = [word for word in words if word.lower() not in stop_words and len(word) > 2]
        return keywords[:10]  # Limit to top 10 keywords
    
    def _determine_intent(self, query: str) -> str:
        """Determine query intent"""
        query_lower = query.lower()
        
        if any(phrase in query_lower for phrase in ["how", "steps", "procedure"]):
            return "instruction"
        elif any(phrase in query_lower for phrase in ["what", "define", "explain"]):
            return "information"
        elif any(phrase in query_lower for phrase in ["compare", "difference", "vs", "versus"]):
            return "comparison"
        elif any(phrase in query_lower for phrase in ["fix", "error", "problem", "issue"]):
            return "solution"
        else:
            return "general"
    
    def _determine_domain(self, query: str) -> str:
        """Determine query domain"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["code", "function", "class", "method", "algorithm", "implementation"]):
            return "code_analysis"
        elif any(word in query_lower for word in ["config", "settings", "parameters", "options", "environment"]):
            return "configuration"
        elif any(word in query_lower for word in ["design", "architecture", "pattern", "system", "structure"]):
            return "architecture"
        elif any(word in query_lower for word in ["performance", "speed", "optimization", "efficiency"]):
            return "performance"
        elif any(word in query_lower for word in ["security", "authentication", "authorization", "encryption", "vulnerability"]):
            return "security"
        else:
            return "general"

@dataclass
class SemanticAnalysisResult:
    """Result of semantic query analysis"""
    query_type: QueryType
    complexity: str
    keywords: List[str]
    intent: str
    domain: str

class QueryRewriter:
    """Rewrites queries using various strategies"""
    
    def __init__(self, llm, config: Dict[str, Any]):
        self.llm = llm
        self.config = config
    
    def expand_with_synonyms(self, query: str) -> List[str]:
        """Expand query using synonyms"""
        # Simple synonym expansion - in practice, use LLM for sophisticated expansion
        expanded_queries = [query]  # Always include original query
        
        # Basic synonym replacement
        synonyms = {
            "error": ["bug", "issue", "problem"],
            "function": ["method", "procedure"],
            "class": ["type", "object"],
            "file": ["document", "resource"]
        }
        
        for original, synonym_list in synonyms.items():
            if original in query.lower():
                for synonym in synonym_list:
                    expanded_query = query.lower().replace(original, synonym)
                    expanded_queries.append(expanded_query)
        
        return expanded_queries
    
    def expand_with_context(self, query: str, semantic_analysis) -> List[str]:
        """Expand query using context information"""
        expanded_queries = []
        
        # Add domain-specific terms
        if semantic_analysis.domain == "code_analysis":
            expanded_queries.append(f"{query} code implementation")
            expanded_queries.append(f"{query} function method")
        
        elif semantic_analysis.domain == "configuration":
            expanded_queries.append(f"{query} settings parameters")
            expanded_queries.append(f"{query} config options")
        
        elif semantic_analysis.domain == "architecture":
            expanded_queries.append(f"{query} design pattern")
            expanded_queries.append(f"{query} system structure")
        
        return expanded_queries
    
    def rewrite_semantically(self, query: str, semantic_analysis) -> List[str]:
        """Rewrite query semantically"""
        rewritten_queries = []
        
        # Intent-based rewriting
        if semantic_analysis.intent == "instruction":
            rewritten_queries.append(f"steps to {query}")
            rewritten_queries.append(f"how to {query}")
        
        elif semantic_analysis.intent == "information":
            rewritten_queries.append(f"what is {query}")
            rewritten_queries.append(f"explain {query}")
        
        elif semantic_analysis.intent == "solution":
            rewritten_queries.append(f"fix {query}")
            rewritten_queries.append(f"resolve {query}")
        
        return rewritten_queries
    
    def rewrite_by_patterns(self, query: str, semantic_analysis) -> List[str]:
        """Rewrite query using pattern matching"""
        rewritten_queries = []
        
        # Pattern-based rewriting
        if "how to" in query.lower():
            # Preserve original case structure
            if "How to" in query:
                rewritten_queries.append(query.replace("How to", "Steps for"))
                rewritten_queries.append(query.replace("How to", "Procedure to"))
            else:
                rewritten_queries.append(query.lower().replace("how to", "steps for"))
                rewritten_queries.append(query.lower().replace("how to", "procedure to"))
        
        if "what is" in query.lower():
            # Preserve original case structure
            if "What is" in query:
                rewritten_queries.append(query.replace("What is", "Explain"))
                rewritten_queries.append(query.replace("What is", "Define"))
            else:
                rewritten_queries.append(query.lower().replace("what is", "explain"))
                rewritten_queries.append(query.lower().replace("what is", "define"))
        
        return rewritten_queries

class QueryDecomposer:
    """Decomposes complex queries into simpler sub-queries"""
    
    def __init__(self, llm, config: Dict[str, Any]):
        self.llm = llm
        self.config = config
    
    def decompose_query(self, query: str, semantic_analysis) -> List[str]:
        """Decompose complex query into simpler queries"""
        decomposed_queries = [query]
        
        # Decomposition based on complexity and connectors
        if semantic_analysis.complexity in ["high", "medium"]:
            # Break down queries with connectors
            if " and " in query.lower():
                parts = query.lower().split(" and ")
                decomposed_queries.extend([part.strip() for part in parts if part.strip()])
            
            if " or " in query.lower():
                parts = query.lower().split(" or ")
                decomposed_queries.extend([part.strip() for part in parts if part.strip()])
        
        # Intent-based decomposition
        if semantic_analysis.intent == "comparison":
            # Extract comparison elements
            if " vs " in query.lower() or "versus" in query.lower():
                if " vs " in query.lower():
                    parts = query.lower().split(" vs ")
                else:
                    parts = query.lower().split("versus")
                
                if len(parts) > 1:
                    # Handle the case where we have "A vs B for C"
                    first_part = parts[0].strip()
                    second_part = parts[1].strip()
                    
                    # Check if second part contains "for" to separate context
                    if " for " in second_part:
                        context_parts = second_part.split(" for ", 1)
                        second_item = context_parts[0].strip()
                        context = context_parts[1].strip()
                        
                        decomposed_queries.extend([
                            f"what is {first_part}",
                            f"what is {second_item} for {context}"
                        ])
                    else:
                        decomposed_queries.extend([
                            f"what is {first_part}",
                            f"what is {second_part}"
                        ])
        
        return list(set(decomposed_queries))  # Remove duplicates

class OptimizationStrategySelector:
    """Selects the best optimization strategy for a query"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def select_strategy(self, semantic_analysis, context: Optional[Dict[str, Any]] = None) -> OptimizationStrategy:
        """Select the best optimization strategy"""
        
        # Strategy selection logic
        if semantic_analysis.complexity == "high":
            if semantic_analysis.query_type == QueryType.COMPARATIVE:
                return OptimizationStrategy.DECOMPOSITION
            elif semantic_analysis.query_type == QueryType.ANALYTICAL:
                return OptimizationStrategy.MULTI_QUERY
            else:
                return OptimizationStrategy.EXPANSION
        
        elif semantic_analysis.complexity == "medium":
            if semantic_analysis.intent == "instruction":
                return OptimizationStrategy.REWRITING
            else:
                return OptimizationStrategy.EXPANSION
        
        else:  # Low complexity
            return OptimizationStrategy.REWRITING
