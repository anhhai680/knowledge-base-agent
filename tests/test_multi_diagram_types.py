"""
Test Multi-Diagram Type Support

This test suite validates the multi-diagram type support functionality implemented in TASK030,
including flowchart, class diagram, ER diagram, and component diagram generation.
"""

import unittest
from unittest.mock import Mock, MagicMock
from langchain.docstore.document import Document
from src.agents.diagram_agent import DiagramAgent
from src.utils.diagram_generators import DiagramPatternExtractor, MermaidGenerator


class TestMultiDiagramTypeSupport(unittest.TestCase):
    """Test multi-diagram type support functionality"""
    
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
        
        # Sample test documents for different diagram types
        self.flowchart_docs = [
            Document(
                page_content="""def process_user_login(username, password):
    if username is None:
        return "Username required"
    
    if password is None:
        return "Password required"
    
    user = authenticate_user(username, password)
    if user:
        for role in user.roles:
            if role.is_active:
                return create_session(user)
        return "No active roles"
    else:
        return "Authentication failed"
""",
                metadata={'file_type': 'py', 'repository': 'auth-service', 'file_path': 'auth/login.py'}
            )
        ]
        
        self.class_docs = [
            Document(
                page_content="""class UserService:
    def __init__(self, repository):
        self.repository = repository
        self.cache = {}
    
    def get_user(self, user_id):
        return self.repository.find(user_id)
    
    def create_user(self, user_data):
        return self.repository.save(user_data)
    
    def update_user(self, user_id, data):
        user = self.get_user(user_id)
        user.update(data)
        return self.repository.save(user)

class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.created_at = datetime.now()
    
    def update(self, data):
        for key, value in data.items():
            setattr(self, key, value)
""",
                metadata={'file_type': 'py', 'repository': 'user-service', 'file_path': 'models/user.py'}
            )
        ]
        
        self.er_docs = [
            Document(
                page_content="""@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String username;
    
    @Column(nullable = false)
    private String email;
    
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL)
    private List<Order> orders;
    
    @ManyToOne
    @JoinColumn(name = "role_id")
    private Role role;
}

@Entity
@Table(name = "orders")
public class Order {
    @Id
    private Long id;
    
    @ManyToOne
    @JoinColumn(name = "user_id")
    private User user;
    
    private BigDecimal amount;
}
""",
                metadata={'file_type': 'cs', 'repository': 'order-service', 'file_path': 'entities/User.cs'}
            )
        ]
        
        self.component_docs = [
            Document(
                page_content="""@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;
    
    @Autowired
    private EmailService emailService;
    
    public User createUser(UserDto userDto) {
        User user = new User();
        user.setUsername(userDto.getUsername());
        user.setEmail(userDto.getEmail());
        
        User savedUser = userRepository.save(user);
        emailService.sendWelcomeEmail(savedUser);
        
        return savedUser;
    }
}

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByUsername(String username);
    List<User> findByEmailContaining(String email);
}

@Component
public class EmailService {
    public void sendWelcomeEmail(User user) {
        // Implementation
    }
}
""",
                metadata={'file_type': 'cs', 'repository': 'user-service', 'file_path': 'services/UserService.cs'}
            )
        ]
    
    def test_flowchart_diagram_generation(self):
        """Test flowchart diagram generation from code with flow control"""
        # Mock vectorstore response
        self.mock_vectorstore.similarity_search.return_value = self.flowchart_docs
        
        # Test flowchart query
        result = self.agent.process_query("Generate a flowchart for the user login process")
        
        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['diagram_type'], 'flowchart')
        self.assertIsNotNone(result['mermaid_code'])
        self.assertTrue(result['mermaid_code'].startswith('flowchart'))
        self.assertGreater(len(result['source_documents']), 0)
    
    def test_class_diagram_generation(self):
        """Test class diagram generation from code with classes"""
        # Mock vectorstore response
        self.mock_vectorstore.similarity_search.return_value = self.class_docs
        
        # Test class diagram query
        result = self.agent.process_query("Create a class diagram showing the user service structure")
        
        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['diagram_type'], 'class')
        self.assertIsNotNone(result['mermaid_code'])
        self.assertTrue(result['mermaid_code'].startswith('classDiagram'))
        self.assertGreater(len(result['source_documents']), 0)
    
    def test_er_diagram_generation(self):
        """Test ER diagram generation from entity definitions"""
        # Mock vectorstore response
        self.mock_vectorstore.similarity_search.return_value = self.er_docs
        
        # Test ER diagram query
        result = self.agent.process_query("Generate an entity relationship diagram for the user and order entities")
        
        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['diagram_type'], 'er')
        self.assertIsNotNone(result['mermaid_code'])
        self.assertTrue(result['mermaid_code'].startswith('erDiagram'))
        self.assertGreater(len(result['source_documents']), 0)
    
    def test_component_diagram_generation(self):
        """Test component diagram generation from service definitions"""
        # Mock vectorstore response
        self.mock_vectorstore.similarity_search.return_value = self.component_docs
        
        # Test component diagram query
        result = self.agent.process_query("Show me a component diagram of the user service architecture")
        
        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['diagram_type'], 'component')
        self.assertIsNotNone(result['mermaid_code'])
        self.assertTrue(result['mermaid_code'].startswith('graph'))
        self.assertGreater(len(result['source_documents']), 0)
    
    def test_diagram_type_detection(self):
        """Test automatic diagram type detection based on query content"""
        test_cases = [
            ("flowchart of the login process", "flowchart"),
            ("class diagram showing inheritance", "class"),
            ("entity relationship model", "er"),
            ("component architecture diagram", "component"),
            ("sequence of user authentication", "sequence")
        ]
        
        for query, expected_type in test_cases:
            with self.subTest(query=query):
                # Mock appropriate documents based on expected type
                if expected_type == "flowchart":
                    self.mock_vectorstore.similarity_search.return_value = self.flowchart_docs
                elif expected_type == "class":
                    self.mock_vectorstore.similarity_search.return_value = self.class_docs
                elif expected_type == "er":
                    self.mock_vectorstore.similarity_search.return_value = self.er_docs
                elif expected_type == "component":
                    self.mock_vectorstore.similarity_search.return_value = self.component_docs
                else:
                    self.mock_vectorstore.similarity_search.return_value = self.flowchart_docs
                
                result = self.agent.process_query(query)
                self.assertEqual(result['diagram_type'], expected_type)
    
    def test_no_patterns_found_handling(self):
        """Test handling when no relevant patterns are found"""
        # Mock document with minimal code that won't produce patterns
        empty_doc = Document(
            page_content="const message = 'Hello World';\nconsole.log(message);",
            metadata={'file_type': 'js', 'repository': 'simple', 'file_path': 'hello.js'}
        )
        
        self.mock_vectorstore.similarity_search.return_value = [empty_doc]
        
        result = self.agent.process_query("Generate a flowchart diagram")
        
        # Should handle gracefully with warning status
        self.assertEqual(result['status'], 'warning')
        self.assertIsNotNone(result['mermaid_code'])
        self.assertIn("No flow patterns found", result['answer'])
    
    def test_error_handling_in_diagram_generation(self):
        """Test error handling during diagram generation"""
        # Mock vectorstore to raise an exception
        self.mock_vectorstore.similarity_search.side_effect = Exception("Database error")
        
        result = self.agent.process_query("Generate a diagram")
        
        # Should handle error gracefully
        self.assertEqual(result['status'], 'error')
        self.assertIsNotNone(result['error'])
        self.assertIn("error", result['answer'].lower())
    
    def test_supported_diagram_types(self):
        """Test that all expected diagram types are supported"""
        supported_types = self.agent.get_supported_diagram_types()
        
        expected_types = ['sequence', 'flowchart', 'class', 'er', 'component']
        
        for expected_type in expected_types:
            self.assertIn(expected_type, supported_types)
    
    def test_diagram_type_descriptions(self):
        """Test that diagram type descriptions are available"""
        supported_types = self.agent.get_supported_diagram_types()
        
        for diagram_type in supported_types:
            description = self.agent.get_diagram_type_description(diagram_type)
            self.assertIsNotNone(description)
            self.assertGreater(len(description), 0)
            self.assertNotEqual(description, 'Unknown diagram type')


class TestDiagramPatternExtractor(unittest.TestCase):
    """Test diagram pattern extraction utilities"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = DiagramPatternExtractor()
    
    def test_flow_pattern_extraction(self):
        """Test extraction of flow control patterns"""
        doc = Document(
            page_content="""def validate_user(user):
    if user is None:
        return False
    
    if user.is_active:
        for role in user.roles:
            if role.name == 'admin':
                return True
        return False
    else:
        return False
""",
            metadata={'file_path': 'validation.py'}
        )
        
        patterns = self.extractor.extract_flow_patterns([doc])
        
        self.assertGreater(len(patterns), 0)
        pattern = patterns[0]
        self.assertEqual(pattern['function_name'], 'validate_user')
        self.assertGreater(pattern['decisions'], 0)
        self.assertGreater(pattern['complexity'], 0)
    
    def test_class_pattern_extraction(self):
        """Test extraction of class patterns"""
        doc = Document(
            page_content="""class UserManager:
    def __init__(self):
        self.users = []
        self.cache = {}
    
    def add_user(self, user):
        self.users.append(user)
    
    def find_user(self, user_id):
        return self.cache.get(user_id)
""",
            metadata={'file_path': 'manager.py'}
        )
        
        patterns = self.extractor.extract_class_patterns([doc])
        
        self.assertGreater(len(patterns), 0)
        pattern = patterns[0]
        self.assertEqual(pattern['class_name'], 'UserManager')
        self.assertGreater(len(pattern['methods']), 0)
        self.assertGreater(len(pattern['attributes']), 0)


class TestMermaidGenerator(unittest.TestCase):
    """Test Mermaid diagram code generation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = MermaidGenerator()
    
    def test_flowchart_mermaid_generation(self):
        """Test Mermaid flowchart generation"""
        patterns = [
            {
                'function_name': 'login',
                'decisions': 2,
                'loops': 0,
                'returns': 1,
                'complexity': 3
            }
        ]
        
        mermaid_code = self.generator.create_flowchart_mermaid(patterns)
        
        self.assertTrue(mermaid_code.startswith('flowchart TD'))
        self.assertIn('login', mermaid_code)
        self.assertIn('Decision Point', mermaid_code)
        self.assertIn('Return', mermaid_code)
    
    def test_class_diagram_mermaid_generation(self):
        """Test Mermaid class diagram generation"""
        patterns = [
            {
                'class_name': 'User',
                'methods': ['getName', 'setEmail'],
                'attributes': ['name', 'email'],
                'method_count': 2,
                'attribute_count': 2
            }
        ]
        
        mermaid_code = self.generator.create_class_diagram_mermaid(patterns)
        
        self.assertTrue(mermaid_code.startswith('classDiagram'))
        self.assertIn('class User', mermaid_code)
        self.assertIn('+name', mermaid_code)
        self.assertIn('+getName()', mermaid_code)
    
    def test_empty_patterns_handling(self):
        """Test handling of empty pattern lists"""
        # Test all diagram types with empty patterns
        flowchart = self.generator.create_flowchart_mermaid([])
        class_diagram = self.generator.create_class_diagram_mermaid([])
        er_diagram = self.generator.create_er_diagram_mermaid([])
        component_diagram = self.generator.create_component_diagram_mermaid([])
        
        # Should return valid Mermaid code even with empty patterns
        self.assertTrue(flowchart.startswith('flowchart'))
        self.assertTrue(class_diagram.startswith('classDiagram'))
        self.assertTrue(er_diagram.startswith('erDiagram'))
        self.assertTrue(component_diagram.startswith('graph'))


if __name__ == '__main__':
    unittest.main()
