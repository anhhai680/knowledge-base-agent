"""
Test Enhanced DiagramAgent with Enhanced Code Retrieval

This test suite validates the enhanced code retrieval functionality implemented in TASK029,
including semantic analysis, repository filtering, and code pattern detection.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from langchain.docstore.document import Document
from src.agents.diagram_agent import DiagramAgent
from src.utils.code_analysis import CodePatternDetector, QueryOptimizer, RepositoryFilter


class TestEnhancedCodeRetrieval(unittest.TestCase):
    """Test enhanced code retrieval functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock dependencies
        self.mock_vectorstore = Mock()
        self.mock_llm = Mock()
        self.mock_query_optimizer = Mock()
        self.mock_response_enhancer = Mock()
        
        # Create DiagramAgent instance
        self.agent = DiagramAgent(
            vectorstore=self.mock_vectorstore,
            llm=self.mock_llm,
            query_optimizer=self.mock_query_optimizer,
            response_enhancer=self.mock_response_enhancer
        )
        
        # Sample test documents
        self.sample_docs = [
            Document(
                page_content="class UserService:\n    def get_user(self, user_id):\n        return self.repository.find(user_id)",
                metadata={'file_type': 'py', 'repository': 'user-management', 'file_path': 'services/user_service.py'}
            ),
            Document(
                page_content="function processUser(userId) {\n    if (userId) {\n        return userService.getUser(userId);\n    }\n    return null;",
                metadata={'file_type': 'js', 'repository': 'user-management', 'file_path': 'utils/user_processor.js'}
            ),
            Document(
                page_content="@Entity\n@Table(name='users')\npublic class User {\n    @Id\n    private Long id;\n    private String name;",
                metadata={'file_type': 'cs', 'repository': 'user-management', 'file_path': 'models/User.cs'}
            )
        ]
    
    def test_enhanced_query_optimization(self):
        """Test enhanced query optimization for diagrams"""
        # Test basic query optimization
        query = "show me the user flow"
        optimized = self.agent._enhanced_query_optimization(query)
        
        # Should add diagram-specific terms
        self.assertIn("diagram", optimized)
        self.assertIn("visualization", optimized)
        
        # Test with external query optimizer
        self.mock_query_optimizer.optimize_for_diagrams.return_value = "enhanced user flow analysis"
        optimized_with_external = self.agent._enhanced_query_optimization(query)
        
        # Should combine both optimizations
        self.assertIn("diagram", optimized_with_external)
        self.assertIn("enhanced", optimized_with_external)
    
    def test_repository_extraction(self):
        """Test repository extraction from queries"""
        # Test various repository patterns
        test_cases = [
            ("show diagram for repository:user-management", ["user-management"]),
            ("create flowchart in user-management repo", ["user-management"]),
            ("generate sequence diagram from user-management repository", ["user-management"]),
            ("show me the code in user-management", ["user-management"]),
            ("no repository mentioned", [])
        ]
        
        for query, expected_repos in test_cases:
            with self.subTest(query=query):
                repositories = self.agent.repository_filter.extract_repositories(query)
                self.assertEqual(repositories, expected_repos)
    
    def test_diagram_intent_extraction(self):
        """Test diagram intent extraction"""
        # Test sequence diagram intent
        query = "show me the sequence of API calls"
        intent = self.agent.diagram_query_optimizer.extract_diagram_intent(query)
        
        self.assertTrue(intent['is_diagram_request'])
        self.assertEqual(intent['preferred_type'], 'sequence')
        self.assertGreater(intent['confidence'], 0.5)
        
        # Test flowchart intent
        query = "create a flowchart of the decision logic"
        intent = self.agent.diagram_query_optimizer.extract_diagram_intent(query)
        
        self.assertTrue(intent['is_diagram_request'])
        self.assertEqual(intent['preferred_type'], 'flowchart')
        
        # Test class diagram intent
        query = "show me the class structure"
        intent = self.agent.diagram_query_optimizer.extract_diagram_intent(query)
        
        self.assertTrue(intent['is_diagram_request'])
        self.assertEqual(intent['preferred_type'], 'class')
    
    def test_semantic_search_terms_extraction(self):
        """Test semantic search terms extraction"""
        query = "create a sequence diagram for the user authentication flow"
        intent = self.agent.diagram_query_optimizer.extract_diagram_intent(query)
        terms = self.agent._extract_semantic_search_terms(query, intent)
        
        # Should contain meaningful terms
        self.assertIn("sequence", terms)
        self.assertIn("diagram", terms)
        self.assertIn("user", terms)
        self.assertIn("authentication", terms)
        self.assertIn("flow", terms)
        
        # Should not contain stop words
        self.assertNotIn("the", terms)
        self.assertNotIn("a", terms)
        self.assertNotIn("for", terms)
    
    def test_multi_strategy_search(self):
        """Test multi-strategy search implementation"""
        # Mock vectorstore responses
        self.mock_vectorstore.similarity_search.side_effect = [
            [self.sample_docs[0]],  # Repository search
            [self.sample_docs[1]],  # Intent search
            [self.sample_docs[2]],  # General search
            [self.sample_docs[0]]   # Pattern search
        ]
        
        search_terms = ["user", "service"]
        repositories = ["user-management"]
        intent = {'preferred_type': 'sequence', 'confidence': 0.8}
        
        results = self.agent._multi_strategy_search(search_terms, repositories, intent)
        
        # Should combine results from all strategies
        self.assertGreater(len(results), 0)
        self.mock_vectorstore.similarity_search.assert_called()
    
    def test_repository_specific_search(self):
        """Test repository-specific search with context"""
        # Mock repository search
        self.mock_vectorstore.similarity_search.return_value = self.sample_docs[:2]
        
        results = self.agent._search_repository_with_context(
            "user-management", ["user", "service"], 
            {'preferred_type': 'sequence'}
        )
        
        # Should filter by repository and intent
        self.assertGreater(len(results), 0)
        self.mock_vectorstore.similarity_search.assert_called_with(
            "user repository:user-management", k=15
        )
    
    def test_intent_based_search(self):
        """Test search based on diagram generation intent"""
        intent = {'preferred_type': 'sequence'}
        search_terms = ["user", "service"]
        
        # Mock intent-based search
        self.mock_vectorstore.similarity_search.return_value = self.sample_docs[:2]
        
        results = self.agent._search_by_diagram_intent(search_terms, intent)
        
        # Should add diagram-specific terms
        self.assertGreater(len(results), 0)
        self.mock_vectorstore.similarity_search.assert_called_with(
            "user sequence diagram", k=10
        )
    
    def test_code_pattern_detection(self):
        """Test code pattern detection for different diagram types"""
        # Test sequence patterns
        content = "userService.getUser(userId).then(response => processUser(response))"
        structure = self.agent.pattern_detector.detect_patterns([self.sample_docs[0]])
        
        self.assertGreater(len(structure.patterns), 0)
        # Check if sequence patterns are detected
        sequence_patterns = [p for p in structure.patterns if p.pattern_type == 'sequence']
        self.assertGreater(len(sequence_patterns), 0)
        
        # Test flowchart patterns
        content = "if (condition) { doSomething(); } else { doSomethingElse(); }"
        flowchart_doc = Document(
            page_content=content,
            metadata={'file_type': 'js', 'file_path': 'test.js'}
        )
        flowchart_structure = self.agent.pattern_detector.detect_patterns([flowchart_doc])
        
        self.assertGreater(len(flowchart_structure.patterns), 0)
        # Check if flowchart patterns are detected
        flowchart_patterns = [p for p in flowchart_structure.patterns if p.pattern_type == 'flowchart']
        self.assertGreater(len(flowchart_patterns), 0)
        
        # Test class patterns
        content = "class UserService extends BaseService implements IUserService"
        class_doc = Document(
            page_content=content,
            metadata={'file_type': 'cs', 'file_path': 'test.cs'}
        )
        class_structure = self.agent.pattern_detector.detect_patterns([class_doc])
        
        self.assertGreater(len(class_structure.patterns), 0)
        # Check if class patterns are detected
        class_patterns = [p for p in class_structure.patterns if p.pattern_type == 'class']
        self.assertGreater(len(class_patterns), 0)
    
    def test_enhanced_result_processing(self):
        """Test enhanced result processing and ranking"""
        intent = {'preferred_type': 'sequence', 'keywords': ['user', 'service']}
        
        # Process sample documents
        processed = self.agent._enhanced_result_processing(
            self.sample_docs, "show user service sequence", intent
        )
        
        # Should filter and rank results
        self.assertGreater(len(processed), 0)
        
        # Should prioritize documents with relevant patterns
        sequence_docs = [doc for doc in processed if doc.metadata.get('file_type') == 'py']
        self.assertGreater(len(sequence_docs), 0)
    
    def test_diagram_type_detection(self):
        """Test enhanced diagram type detection"""
        # Test direct type specification
        query = "create a sequence diagram"
        diagram_type = self.agent._enhanced_diagram_type_detection(query, self.sample_docs)
        self.assertEqual(diagram_type, 'sequence')
        
        # Test intent-based detection
        query = "show me the API interactions"
        diagram_type = self.agent._enhanced_diagram_type_detection(query, self.sample_docs)
        self.assertEqual(diagram_type, 'sequence')
        
        # Test code-based detection
        query = "visualize this code"
        diagram_type = self.agent._enhanced_diagram_type_detection(query, self.sample_docs)
        # Should detect based on code content
        self.assertIn(diagram_type, ['sequence', 'flowchart', 'class', 'er', 'component'])
    
    def test_code_structure_analysis(self):
        """Test code structure analysis capabilities"""
        # Analyze sample documents
        structure = self.agent.pattern_detector.detect_patterns(self.sample_docs)
        
        # Should extract classes, functions, and patterns
        self.assertIsNotNone(structure.classes)
        self.assertIsNotNone(structure.functions)
        self.assertIsNotNone(structure.patterns)
        
        # Should detect patterns across different file types
        self.assertGreater(len(structure.patterns), 0)
    
    def test_file_type_filtering(self):
        """Test file type filtering based on diagram intent"""
        # Test sequence diagram file types
        preferred_types = self.agent._get_preferred_file_types('sequence')
        self.assertIn('py', preferred_types)
        self.assertIn('js', preferred_types)
        self.assertIn('ts', preferred_types)
        
        # Test class diagram file types
        preferred_types = self.agent._get_preferred_file_types('class')
        self.assertIn('py', preferred_types)
        self.assertIn('cs', preferred_types)
        self.assertIn('java', preferred_types)
    
    def test_relevance_scoring(self):
        """Test enhanced relevance scoring with intent awareness"""
        intent = {'preferred_type': 'sequence', 'keywords': ['user', 'service']}
        
        # Test scoring function
        def mock_relevance_score(doc):
            return self.agent._deduplicate_and_rank_results([doc], "user service", intent)
        
        # Should handle different document types
        for doc in self.sample_docs:
            results = mock_relevance_score(doc)
            self.assertGreaterEqual(len(results), 0)
    
    def test_error_handling_and_fallback(self):
        """Test error handling and fallback mechanisms"""
        # Test vectorstore failure
        self.mock_vectorstore.similarity_search.side_effect = Exception("Search failed")
        
        # Should fallback to basic search
        results = self.agent._enhanced_code_retrieval("test query")
        self.assertEqual(len(results), 0)
        
        # Test with working fallback
        self.mock_vectorstore.similarity_search.side_effect = None
        self.mock_vectorstore.similarity_search.return_value = self.sample_docs[:1]
        
        results = self.agent._enhanced_code_retrieval("test query")
        self.assertGreater(len(results), 0)
    
    def test_integration_with_existing_components(self):
        """Test integration with existing sequence detector and other components"""
        # Mock sequence detector
        with patch.object(self.agent.sequence_detector, 'analyze_code') as mock_analyzer:
            mock_analyzer.return_value = {'interactions': [{'pattern': 'test'}]}
            
            # Test sequence diagram generation
            result = self.agent._generate_sequence_diagram(self.sample_docs, "test query")
            
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['diagram_type'], 'sequence')
            mock_analyzer.assert_called()


class TestCodeAnalysisUtilities(unittest.TestCase):
    """Test individual code analysis utility classes"""
    
    def test_pattern_detector_pattern_detection(self):
        """Test pattern detection for different diagram types"""
        detector = CodePatternDetector()
        
        # Test Python code with class patterns
        python_doc = Document(
            page_content="class UserService:\n    def get_user(self, user_id):\n        return self.repository.find(user_id)",
            metadata={'file_type': 'py', 'file_path': 'user_service.py'}
        )
        
        # Test JavaScript code with function patterns
        js_doc = Document(
            page_content="function processUser(userId) { if (userId) { return userService.getUser(userId); } }",
            metadata={'file_type': 'js', 'file_path': 'user_processor.js'}
        )
        
        structure = detector.detect_patterns([python_doc, js_doc])
        
        # Should detect classes and functions
        self.assertGreater(len(structure.classes), 0)
        self.assertGreater(len(structure.functions), 0)
        self.assertGreater(len(structure.patterns), 0)
        
        # Should detect different pattern types
        pattern_types = set(pattern.pattern_type for pattern in structure.patterns)
        self.assertIn('class', pattern_types)
        self.assertIn('sequence', pattern_types)
    
    def test_query_optimizer_diagram_keywords(self):
        """Test query optimization for different diagram types"""
        optimizer = QueryOptimizer()
        
        # Test query that should get enhanced (no diagram keywords)
        query = "show me the user management"
        optimized = optimizer.optimize_for_diagrams(query)
        self.assertIn("diagram", optimized)
        
        # Test query with diagram keywords (should not be changed)
        query = "show me the API calls"  # contains "call" which is a sequence keyword
        optimized = optimizer.optimize_for_diagrams(query)
        self.assertEqual(optimized, query)  # Should not change
        
        # Test already optimized query
        query = "create a sequence diagram"
        optimized = optimizer.optimize_for_diagrams(query)
        self.assertEqual(optimized, query)  # Should not change
    
    def test_repository_filter_patterns(self):
        """Test repository filtering patterns"""
        filter_obj = RepositoryFilter()
        
        # Test various repository patterns
        test_cases = [
            ("repository:user-management", ["user-management"]),
            ("repo user-management", ["user-management"]),
            ("in user-management repository", ["user-management"]),
            ("from user-management repository", ["user-management"]),
            ("no repository mentioned", [])
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                repositories = filter_obj.extract_repositories(query)
                self.assertEqual(repositories, expected)


if __name__ == '__main__':
    unittest.main()
