"""
Test Enhanced RAG Agent

Tests for the enhanced RAG agent with Chain-of-Thought reasoning,
context refinement, and response quality enhancement.
"""

import pytest
from unittest.mock import Mock, MagicMock
from langchain.docstore.document import Document

from src.agents.rag_agent import RAGAgent, QueryAnalysis, QueryAnalyzer, ContextRefiner, ResponseEnhancer
from src.config.rag_enhancement_config import RAGEnhancementConfig, get_enhancement_config

class TestQueryAnalysis:
    """Test QueryAnalysis class"""
    
    def test_query_analysis_creation(self):
        """Test creating QueryAnalysis object"""
        analysis = QueryAnalysis(
            original="What is the main function?",
            optimized="What is the main function code implementation?",
            intent="code_analysis",
            complexity="medium",
            retrieval_strategy="code_focused",
            reasoning_steps=["Analyzed query intent: code_analysis"]
        )
        
        assert analysis.original == "What is the main function?"
        assert analysis.optimized == "What is the main function code implementation?"
        assert analysis.intent == "code_analysis"
        assert analysis.complexity == "medium"
        assert analysis.retrieval_strategy == "code_focused"
        assert len(analysis.reasoning_steps) == 1

class TestQueryAnalyzer:
    """Test QueryAnalyzer class"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_llm = Mock()
        self.analyzer = QueryAnalyzer(self.mock_llm)
    
    def test_intent_classification(self):
        """Test query intent classification"""
        # Test code analysis intent
        intent = self.analyzer._classify_intent("How does the main function work?")
        assert intent == "code_analysis"
        
        # Test configuration intent
        intent = self.analyzer._classify_intent("What are the config settings?")
        assert intent == "configuration"
        
        # Test general intent
        intent = self.analyzer._classify_intent("What is this project about?")
        assert intent == "general"
    
    def test_complexity_assessment(self):
        """Test query complexity assessment"""
        # Test low complexity
        complexity = self.analyzer._assess_complexity("What is Python?")
        assert complexity == "low"
        
        # Test medium complexity
        complexity = self.analyzer._assess_complexity("How does the authentication system work?")
        assert complexity == "medium"
        
        # Test high complexity
        complexity = self.analyzer._assess_complexity("Analyze the architecture and optimize the performance")
        assert complexity == "high"
    
    def test_query_optimization(self):
        """Test query optimization"""
        # Test code analysis optimization
        optimized = self.analyzer._optimize_query("How does this work?", "code_analysis")
        assert "code implementation" in optimized
        
        # Test configuration optimization - use question without config terms
        question = "What are the options?"
        optimized = self.analyzer._optimize_query(question, "configuration")
        assert "configuration settings" in optimized
        
        # Test no optimization for general
        optimized = self.analyzer._optimize_query("What is this?", "general")
        assert optimized == "What is this?"
    
    def test_retrieval_strategy_selection(self):
        """Test retrieval strategy selection"""
        # Test high complexity -> multi_pass
        strategy = self.analyzer._select_retrieval_strategy("code_analysis", "high")
        assert strategy == "multi_pass"
        
        # Test code analysis -> code_focused
        strategy = self.analyzer._select_retrieval_strategy("code_analysis", "medium")
        assert strategy == "code_focused"
        
        # Test configuration -> config_focused
        strategy = self.analyzer._select_retrieval_strategy("configuration", "medium")
        assert strategy == "config_focused"
        
        # Test general -> standard
        strategy = self.analyzer._select_retrieval_strategy("general", "low")
        assert strategy == "standard"
    
    def test_full_analysis(self):
        """Test complete query analysis"""
        analysis = self.analyzer.analyze_query("How does the authentication work?")
        
        assert analysis.intent == "code_analysis"
        assert analysis.complexity == "medium"
        assert analysis.retrieval_strategy == "code_focused"
        assert len(analysis.reasoning_steps) > 0
        assert "code implementation" in analysis.optimized

class TestContextRefiner:
    """Test ContextRefiner class"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_llm = Mock()
        self.config = RAGEnhancementConfig(
            max_refinement_iterations=3,
            quality_threshold=0.8
        )
        self.refiner = ContextRefiner(self.mock_llm, self.config)
    
    def test_context_quality_assessment(self):
        """Test context quality assessment"""
        # Create test documents
        docs = [
            Document(page_content="This is about Python functions and code", metadata={}),
            Document(page_content="Python programming language features", metadata={}),
            Document(page_content="How to write Python code", metadata={})
        ]
        
        question = "How does Python work?"
        quality = self.refiner._assess_context_quality(docs, question)
        
        assert 0.0 <= quality <= 1.0
        assert quality > 0.0  # Should have some relevance
    
    def test_context_optimization(self):
        """Test context optimization"""
        # Create test documents with varying relevance
        docs = [
            Document(page_content="Python functions and code implementation", metadata={}),
            Document(page_content="Unrelated content about databases", metadata={}),
            Document(page_content="Python programming examples", metadata={})
        ]
        
        question = "How does Python work?"
        quality = self.refiner._assess_context_quality(docs, question)
        
        if quality < 0.6:
            optimized = self.refiner._optimize_context(docs, question, quality)
            # Should re-rank documents by relevance
            assert len(optimized) == len(docs)
    
    def test_context_refinement(self):
        """Test context refinement process"""
        docs = [
            Document(page_content="Python functions and code", metadata={}),
            Document(page_content="Python programming", metadata={})
        ]
        
        question = "How does Python work?"
        refined = self.refiner.refine_context(docs, question)
        
        assert len(refined) == len(docs)
        assert self.refiner.last_iterations >= 0
        assert 0.0 <= self.refiner.last_quality_score <= 1.0

class TestResponseEnhancer:
    """Test ResponseEnhancer class"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_llm = Mock()
        self.config = RAGEnhancementConfig(
            max_enhancement_iterations=2,
            quality_validation=True,
            response_improvement=True
        )
        self.enhancer = ResponseEnhancer(self.mock_llm, self.config)
    
    def test_response_validation(self):
        """Test response validation"""
        # Test short answer
        response = {"answer": "Short", "source_documents": []}
        docs = [Document(page_content="Python code", metadata={})]
        validation = self.enhancer._validate_response(response, docs, "What is Python?")
        
        assert not validation["is_satisfactory"]
        assert "Answer too short" in validation["issues"]
        assert "Provide more detailed explanation" in validation["suggestions"]
    
    def test_response_improvement(self):
        """Test response improvement"""
        response = {"answer": "Python is a language", "source_documents": []}
        docs = [Document(page_content="Python code", metadata={})]
        validation = self.enhancer._validate_response(response, docs, "Show me the code")
        
        improved = self.enhancer._improve_response(response, docs, "Show me the code", validation)
        
        assert "Consider reviewing the source code" in improved["answer"]
    
    def test_response_enhancement(self):
        """Test complete response enhancement"""
        response = {"answer": "Short", "source_documents": []}
        docs = [Document(page_content="Python code", metadata={})]
        
        enhanced = self.enhancer.enhance_response(response, docs, "What is Python?")
        
        assert enhanced["answer"] != response["answer"]  # Should be enhanced

class TestEnhancedRAGAgent:
    """Test Enhanced RAG Agent"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_llm = Mock()
        self.mock_vectorstore = Mock()
        self.mock_vectorstore.as_retriever.return_value = Mock()
        self.mock_vectorstore.similarity_search.return_value = []
        
        # Mock QA chain with proper structure
        self.mock_qa_chain = Mock()
        self.mock_qa_chain.__call__ = Mock(return_value={
            "result": "Python is a programming language",
            "source_documents": []
        })
        self.mock_qa_chain.invoke = Mock(return_value={
            "answer": "Python is a programming language",
            "context": []
        })
        
        # Create agent with proper enhancement config
        enhancement_config = get_enhancement_config()
        
        self.agent = RAGAgent(
            self.mock_llm,
            self.mock_vectorstore,
            enhancement_config=enhancement_config
        )
        self.agent.qa_chain = self.mock_qa_chain
        
        # Mock the enhancement components to avoid complex dependencies
        self.agent.query_analyzer.analyze_query = Mock(return_value=QueryAnalysis(
            original="What is Python?",
            optimized="What is Python?",
            intent="general",
            complexity="low",
            retrieval_strategy="standard",
            reasoning_steps=["Test reasoning step"]
        ))
        
        self.agent.context_refiner.refine_context = Mock(return_value=[])
        self.agent.response_enhancer.enhance_response = Mock(return_value={
            "answer": "Python is a programming language",
            "source_documents": [],
            "query_analysis": {
                "intent": "general",
                "complexity": "low",
                "retrieval_strategy": "standard",
                "reasoning_steps": ["Test reasoning step"]
            },
            "context_metadata": {
                "total_documents": 0,
                "refinement_iterations": 0,
                "context_quality_score": 0.8
            }
        })
    
    def test_enhanced_query_processing(self):
        """Test enhanced query processing"""
        question = "What is Python?"
        result = self.agent.query(question)
        
        # Should return enhanced response with metadata
        assert "answer" in result
        assert "reasoning_steps" in result
        assert "query_analysis" in result
        assert "context_quality_score" in result
        assert "enhancement_iterations" in result
        assert result["status"] == "success"
    
    def test_fallback_processing(self):
        """Test fallback to basic processing"""
        # Mock enhancement failure
        self.agent.query_analyzer.analyze_query = Mock(side_effect=Exception("Test error"))
        
        question = "What is Python?"
        result = self.agent.query(question)
        
        # Should fallback to basic processing
        assert "answer" in result
        assert "reasoning_steps" in result
        assert "fallback" in result.get("query_analysis", {}).get("intent", "")
        assert result["status"] == "success"
    
    def test_adaptive_retrieval(self):
        """Test adaptive retrieval based on query analysis"""
        # Mock query analysis for high complexity
        mock_analysis = QueryAnalysis(
            original="Analyze the complex architecture",
            optimized="Analyze the complex architecture",
            intent="architecture",
            complexity="high",
            retrieval_strategy="multi_pass",
            reasoning_steps=[]
        )
        
        self.agent.query_analyzer.analyze_query = Mock(return_value=mock_analysis)
        
        # Test adaptive retrieval kwargs
        kwargs = self.agent._get_adaptive_retrieval_kwargs(mock_analysis)
        
        # Should increase k for high complexity
        assert kwargs["k"] > self.agent.retriever_kwargs.get("k", 5)
    
    def test_document_relevance_assessment(self):
        """Test document relevance assessment"""
        doc = Document(page_content="Python programming language", metadata={})
        question = "What is Python?"
        analysis = QueryAnalysis(
            original=question,
            optimized=question,
            intent="general",
            complexity="low",
            retrieval_strategy="standard",
            reasoning_steps=[]
        )
        
        relevance = self.agent._assess_document_relevance(doc, question, analysis)
        
        assert "relevance" in relevance.lower()
        assert "match" in relevance.lower()

if __name__ == "__main__":
    pytest.main([__file__])
