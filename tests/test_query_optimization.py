"""
Tests for Advanced Query Optimization Module

Tests the sophisticated query optimization capabilities including:
- Semantic query analysis
- Query rewriting and expansion
- Multi-query strategies
- Dynamic retrieval optimization
"""

import pytest
from unittest.mock import Mock, patch
from src.agents.query_optimizer import (
    AdvancedQueryOptimizer,
    SemanticQueryAnalyzer,
    QueryRewriter,
    QueryDecomposer,
    OptimizationStrategySelector,
    QueryType,
    OptimizationStrategy,
    QueryOptimizationResult,
    SemanticAnalysisResult
)

class TestSemanticAnalysisResult:
    """Test SemanticAnalysisResult dataclass"""
    
    def test_semantic_analysis_result_creation(self):
        """Test creating semantic analysis result"""
        result = SemanticAnalysisResult(
            query_type=QueryType.FACTUAL,
            complexity="medium",
            keywords=["test", "query"],
            intent="information",
            domain="general"
        )
        
        assert result.query_type == QueryType.FACTUAL
        assert result.complexity == "medium"
        assert result.keywords == ["test", "query"]
        assert result.intent == "information"
        assert result.domain == "general"

class TestSemanticQueryAnalyzer:
    """Test SemanticQueryAnalyzer class"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_llm = Mock()
        self.config = {"enable_semantic_analysis": True}
        self.analyzer = SemanticQueryAnalyzer(self.mock_llm, self.config)
    
    def test_determine_query_type_factual(self):
        """Test factual query type detection"""
        query = "What is Python?"
        query_type = self.analyzer._determine_query_type(query.lower())
        assert query_type == QueryType.FACTUAL
    
    def test_determine_query_type_procedural(self):
        """Test procedural query type detection"""
        query = "How to install Python?"
        query_type = self.analyzer._determine_query_type(query.lower())
        assert query_type == QueryType.PROCEDURAL
    
    def test_determine_query_type_comparative(self):
        """Test comparative query type detection"""
        query = "Python vs JavaScript"
        query_type = self.analyzer._determine_query_type(query.lower())
        assert query_type == QueryType.COMPARATIVE
    
    def test_determine_query_type_analytical(self):
        """Test analytical query type detection"""
        query = "Analyze the performance of this code"
        query_type = self.analyzer._determine_query_type(query.lower())
        assert query_type == QueryType.ANALYTICAL
    
    def test_determine_query_type_exploratory(self):
        """Test exploratory query type detection"""
        query = "Explore the codebase structure"
        query_type = self.analyzer._determine_query_type(query.lower())
        assert query_type == QueryType.EXPLORATORY
    
    def test_determine_query_type_troubleshooting(self):
        """Test troubleshooting query type detection"""
        query = "Fix the error in this function"
        query_type = self.analyzer._determine_query_type(query.lower())
        assert query_type == QueryType.TROUBLESHOOTING
    
    def test_determine_complexity_low(self):
        """Test low complexity detection"""
        query = "What is Python?"
        complexity = self.analyzer._determine_complexity(query)
        assert complexity == "low"
    
    def test_determine_complexity_medium(self):
        """Test medium complexity detection"""
        query = "How do I install Python and set up the environment?"
        complexity = self.analyzer._determine_complexity(query)
        assert complexity == "medium"
    
    def test_determine_complexity_high(self):
        """Test high complexity detection"""
        query = "How do I implement a complex machine learning algorithm using Python with proper error handling and performance optimization?"
        complexity = self.analyzer._determine_complexity(query)
        assert complexity == "high"
    
    def test_extract_keywords(self):
        """Test keyword extraction"""
        query = "How to install Python and set up virtual environment"
        keywords = self.analyzer._extract_keywords(query)
        
        # Should extract meaningful words, excluding stop words
        assert "install" in keywords
        assert "Python" in keywords
        assert "virtual" in keywords
        assert "environment" in keywords
        assert "How" not in keywords  # Stop word
        assert "to" not in keywords   # Stop word
        assert "and" not in keywords  # Stop word
        assert "set" not in keywords  # Stop word
        assert "up" not in keywords   # Stop word
    
    def test_determine_intent_instruction(self):
        """Test instruction intent detection"""
        query = "How to install Python"
        intent = self.analyzer._determine_intent(query)
        assert intent == "instruction"
    
    def test_determine_intent_information(self):
        """Test information intent detection"""
        query = "What is Python"
        intent = self.analyzer._determine_intent(query)
        assert intent == "information"
    
    def test_determine_intent_comparison(self):
        """Test comparison intent detection"""
        query = "Compare Python and JavaScript"
        intent = self.analyzer._determine_intent(query)
        assert intent == "comparison"
    
    def test_determine_intent_solution(self):
        """Test solution intent detection"""
        query = "Fix the error in Python code"
        intent = self.analyzer._determine_intent(query)
        assert intent == "solution"
    
    def test_determine_domain_code_analysis(self):
        """Test code analysis domain detection"""
        query = "How to write a function in Python"
        domain = self.analyzer._determine_domain(query)
        assert domain == "code_analysis"
    
    def test_determine_domain_configuration(self):
        """Test configuration domain detection"""
        query = "How to configure Python settings"
        domain = self.analyzer._determine_domain(query)
        assert domain == "configuration"
    
    def test_determine_domain_architecture(self):
        """Test architecture domain detection"""
        query = "What is the design pattern for this system"
        domain = self.analyzer._determine_domain(query)
        assert domain == "architecture"
    
    def test_analyze_query_complete(self):
        """Test complete query analysis"""
        query = "How to implement a machine learning algorithm in Python with proper error handling"
        result = self.analyzer.analyze_query(query)
        
        assert isinstance(result, SemanticAnalysisResult)
        assert result.query_type == QueryType.PROCEDURAL
        assert result.complexity == "high"
        assert result.intent == "instruction"
        assert result.domain == "code_analysis"
        assert len(result.keywords) > 0

class TestQueryRewriter:
    """Test QueryRewriter class"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_llm = Mock()
        self.config = {"enable_synonym_replacement": True}
        self.rewriter = QueryRewriter(self.mock_llm, self.config)
    
    def test_expand_with_synonyms(self):
        """Test synonym-based query expansion"""
        query = "How to fix the error in the function"
        expansions = self.rewriter.expand_with_synonyms(query)
        
        # Should include original query and synonym expansions
        assert query in expansions
        assert "how to fix the bug in the function" in expansions
        assert "how to fix the issue in the function" in expansions
        assert "how to fix the problem in the function" in expansions
    
    def test_expand_with_context_code_analysis(self):
        """Test context-based expansion for code analysis domain"""
        mock_analysis = Mock()
        mock_analysis.domain = "code_analysis"
        
        query = "How to implement authentication"
        expansions = self.rewriter.expand_with_context(query, mock_analysis)
        
        assert f"{query} code implementation" in expansions
        assert f"{query} function method" in expansions
    
    def test_expand_with_context_configuration(self):
        """Test context-based expansion for configuration domain"""
        mock_analysis = Mock()
        mock_analysis.domain = "configuration"
        
        query = "How to set up database"
        expansions = self.rewriter.expand_with_context(query, mock_analysis)
        
        assert f"{query} settings parameters" in expansions
        assert f"{query} config options" in expansions
    
    def test_rewrite_semantically_instruction(self):
        """Test semantic rewriting for instruction intent"""
        mock_analysis = Mock()
        mock_analysis.intent = "instruction"
        
        query = "Install Python"
        rewrites = self.rewriter.rewrite_semantically(query, mock_analysis)
        
        assert f"steps to {query}" in rewrites
        assert f"how to {query}" in rewrites
    
    def test_rewrite_semantically_information(self):
        """Test semantic rewriting for information intent"""
        mock_analysis = Mock()
        mock_analysis.intent = "information"
        
        query = "Python programming"
        rewrites = self.rewriter.rewrite_semantically(query, mock_analysis)
        
        assert f"what is {query}" in rewrites
        assert f"explain {query}" in rewrites
    
    def test_rewrite_by_patterns_how_to(self):
        """Test pattern-based rewriting for how-to queries"""
        mock_analysis = Mock()
        query = "How to install Python"
        rewrites = self.rewriter.rewrite_by_patterns(query, mock_analysis)
        
        assert "Steps for install Python" in rewrites
        assert "Procedure to install Python" in rewrites
    
    def test_rewrite_by_patterns_what_is(self):
        """Test pattern-based rewriting for what-is queries"""
        mock_analysis = Mock()
        query = "What is Python"
        rewrites = self.rewriter.rewrite_by_patterns(query, mock_analysis)
        
        assert "Explain Python" in rewrites
        assert "Define Python" in rewrites

class TestQueryDecomposer:
    """Test QueryDecomposer class"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_llm = Mock()
        self.config = {"enable_decomposition": True}
        self.decomposer = QueryDecomposer(self.mock_llm, self.config)
    
    def test_decompose_query_simple(self):
        """Test decomposition of simple query"""
        mock_analysis = Mock()
        mock_analysis.complexity = "low"
        mock_analysis.intent = "information"
        
        query = "What is Python"
        decomposed = self.decomposer.decompose_query(query, mock_analysis)
        
        # Simple query should not be decomposed
        assert decomposed == [query]
    
    def test_decompose_query_complex_and(self):
        """Test decomposition of complex query with 'and'"""
        mock_analysis = Mock()
        mock_analysis.complexity = "high"
        mock_analysis.intent = "information"
        
        query = "What is Python and how to install it"
        decomposed = self.decomposer.decompose_query(query, mock_analysis)
        
        # Should decompose into parts
        assert len(decomposed) >= 2
        assert "what is python" in [q.lower() for q in decomposed]
        assert "how to install it" in [q.lower() for q in decomposed]
    
    def test_decompose_query_complex_or(self):
        """Test decomposition of complex query with 'or'"""
        mock_analysis = Mock()
        mock_analysis.complexity = "high"
        mock_analysis.intent = "information"
        
        query = "Should I use Python or JavaScript for web development"
        decomposed = self.decomposer.decompose_query(query, mock_analysis)
        
        # Should decompose into parts
        assert len(decomposed) >= 2
        assert "should i use python" in [q.lower() for q in decomposed]
        assert "javascript for web development" in [q.lower() for q in decomposed]
    
    def test_decompose_query_comparison(self):
        """Test decomposition of comparison query"""
        mock_analysis = Mock()
        mock_analysis.complexity = "medium"
        mock_analysis.intent = "comparison"
        
        query = "Python vs JavaScript for data science"
        decomposed = self.decomposer.decompose_query(query, mock_analysis)
        
        # Should decompose comparison elements
        assert len(decomposed) >= 2
        assert "what is python" in [q.lower() for q in decomposed]
        assert "what is javascript for data science" in [q.lower() for q in decomposed]

class TestOptimizationStrategySelector:
    """Test OptimizationStrategySelector class"""
    
    def setup_method(self):
        """Setup test method"""
        self.config = {"enable_adaptive_strategy_selection": True}
        self.selector = OptimizationStrategySelector(self.config)
    
    def test_select_strategy_high_complexity_comparative(self):
        """Test strategy selection for high complexity comparative query"""
        mock_analysis = Mock()
        mock_analysis.complexity = "high"
        mock_analysis.query_type = QueryType.COMPARATIVE
        
        strategy = self.selector.select_strategy(mock_analysis)
        assert strategy == OptimizationStrategy.DECOMPOSITION
    
    def test_select_strategy_high_complexity_analytical(self):
        """Test strategy selection for high complexity analytical query"""
        mock_analysis = Mock()
        mock_analysis.complexity = "high"
        mock_analysis.query_type = QueryType.ANALYTICAL
        
        strategy = self.selector.select_strategy(mock_analysis)
        assert strategy == OptimizationStrategy.MULTI_QUERY
    
    def test_select_strategy_high_complexity_other(self):
        """Test strategy selection for high complexity other query types"""
        mock_analysis = Mock()
        mock_analysis.complexity = "high"
        mock_analysis.query_type = QueryType.FACTUAL
        
        strategy = self.selector.select_strategy(mock_analysis)
        assert strategy == OptimizationStrategy.EXPANSION
    
    def test_select_strategy_medium_complexity_instruction(self):
        """Test strategy selection for medium complexity instruction query"""
        mock_analysis = Mock()
        mock_analysis.complexity = "medium"
        mock_analysis.intent = "instruction"
        
        strategy = self.selector.select_strategy(mock_analysis)
        assert strategy == OptimizationStrategy.REWRITING
    
    def test_select_strategy_medium_complexity_other(self):
        """Test strategy selection for medium complexity other intents"""
        mock_analysis = Mock()
        mock_analysis.complexity = "medium"
        mock_analysis.intent = "information"
        
        strategy = self.selector.select_strategy(mock_analysis)
        assert strategy == OptimizationStrategy.EXPANSION
    
    def test_select_strategy_low_complexity(self):
        """Test strategy selection for low complexity query"""
        mock_analysis = Mock()
        mock_analysis.complexity = "low"
        
        strategy = self.selector.select_strategy(mock_analysis)
        assert strategy == OptimizationStrategy.REWRITING

class TestAdvancedQueryOptimizer:
    """Test AdvancedQueryOptimizer class"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_llm = Mock()
        self.config = {
            "enable_semantic_analysis": True,
            "enable_query_expansion": True,
            "enable_query_decomposition": True,
            "max_expansion_queries": 3,
            "max_decomposition_queries": 5
        }
        self.optimizer = AdvancedQueryOptimizer(self.mock_llm, self.config)
    
    def test_optimize_query_expansion_strategy(self):
        """Test query optimization with expansion strategy"""
        query = "How to fix the error in the function"
        
        with patch.object(self.optimizer.strategy_selector, 'select_strategy') as mock_select:
            mock_select.return_value = OptimizationStrategy.EXPANSION
            
            result = self.optimizer.optimize_query(query)
            
            assert isinstance(result, QueryOptimizationResult)
            assert result.original_query == query
            assert result.strategy_used == OptimizationStrategy.EXPANSION
            assert len(result.optimized_queries) > 1
            assert result.confidence_score > 0.5
    
    def test_optimize_query_rewriting_strategy(self):
        """Test query optimization with rewriting strategy"""
        query = "What is Python"
        
        with patch.object(self.optimizer.strategy_selector, 'select_strategy') as mock_select:
            mock_select.return_value = OptimizationStrategy.REWRITING
            
            result = self.optimizer.optimize_query(query)
            
            assert isinstance(result, QueryOptimizationResult)
            assert result.original_query == query
            assert result.strategy_used == OptimizationStrategy.REWRITING
            assert len(result.optimized_queries) > 1
            assert result.confidence_score > 0.5
    
    def test_optimize_query_decomposition_strategy(self):
        """Test query optimization with decomposition strategy"""
        query = "What is Python and how to install it"
        
        with patch.object(self.optimizer.strategy_selector, 'select_strategy') as mock_select:
            mock_select.return_value = OptimizationStrategy.DECOMPOSITION
            
            result = self.optimizer.optimize_query(query)
            
            assert isinstance(result, QueryOptimizationResult)
            assert result.original_query == query
            assert result.strategy_used == OptimizationStrategy.DECOMPOSITION
            assert len(result.optimized_queries) > 1
            assert result.confidence_score > 0.5
    
    def test_optimize_query_multi_query_strategy(self):
        """Test query optimization with multi-query strategy"""
        query = "Analyze the performance and security of this code"
        
        with patch.object(self.optimizer.strategy_selector, 'select_strategy') as mock_select:
            mock_select.return_value = OptimizationStrategy.MULTI_QUERY
            
            result = self.optimizer.optimize_query(query)
            
            assert isinstance(result, QueryOptimizationResult)
            assert result.original_query == query
            assert result.strategy_used == OptimizationStrategy.MULTI_QUERY
            assert len(result.optimized_queries) > 1
            assert result.confidence_score > 0.5
    
    def test_optimize_query_fallback_on_error(self):
        """Test query optimization fallback on error"""
        query = "Test query"
        
        # Mock an error in semantic analysis
        with patch.object(self.optimizer.semantic_analyzer, 'analyze_query') as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis failed")
            
            result = self.optimizer.optimize_query(query)
            
            assert isinstance(result, QueryOptimizationResult)
            assert result.original_query == query
            assert result.optimized_queries == [query]
            assert result.confidence_score == 0.5
            assert "Optimization failed" in result.reasoning
    
    def test_calculate_confidence_score(self):
        """Test confidence score calculation"""
        query = "Test query"
        optimized_queries = ["Test query", "Test query expanded"]
        strategy = OptimizationStrategy.EXPANSION
        
        score = self.optimizer._calculate_confidence_score(query, optimized_queries, strategy)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be higher than base score
    
    def test_generate_optimization_reasoning(self):
        """Test optimization reasoning generation"""
        strategy = OptimizationStrategy.EXPANSION
        mock_analysis = Mock()
        mock_analysis.query_type = QueryType.FACTUAL
        mock_analysis.complexity = "medium"
        optimized_queries = ["query1", "query2"]
        
        reasoning = self.optimizer._generate_optimization_reasoning(strategy, mock_analysis, optimized_queries)
        
        assert "expansion" in reasoning.lower()
        assert "factual" in reasoning.lower()
        assert "medium" in reasoning.lower()
        assert "2" in reasoning
        assert "multiple queries" in reasoning.lower()

if __name__ == "__main__":
    pytest.main([__file__])
