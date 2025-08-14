#!/usr/bin/env python3
"""
Demo script for the Multi-Repository Sequence Diagram feature
This script demonstrates the core functionality without requiring full system setup
"""

import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Mock the logging module
class MockLogger:
    def debug(self, msg): print(f"[DEBUG] {msg}")
    def info(self, msg): print(f"[INFO] {msg}")
    def warning(self, msg): print(f"[WARNING] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")

def get_logger(name):
    return MockLogger()

# Mock the langchain document
class MockDocument:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

# Monkey patch modules
sys.modules['src.utils.logging'] = type(sys)('mock_logging')
sys.modules['src.utils.logging'].get_logger = get_logger

sys.modules['langchain.docstore.document'] = type(sys)('mock_document')
sys.modules['langchain.docstore.document'].Document = MockDocument

# Now import our modules
from src.agents.agent_router import AgentRouter
from src.processors.diagram_handler import DiagramHandler
from src.processors.sequence_detector import SequenceDetector


class MockRAGAgent:
    """Mock RAG agent for demonstration"""
    def query(self, question):
        return {
            "answer": f"This is a regular RAG response for: {question}",
            "source_documents": [],
            "status": "success",
            "num_sources": 0
        }


class MockVectorStore:
    """Mock vector store with sample code data"""
    
    def __init__(self):
        self.sample_docs = [
            MockDocument(
                page_content="""
class AuthController:
    def __init__(self):
        self.user_service = UserService()
        self.session_manager = SessionManager()
    
    def login(self, credentials):
        user = self.user_service.authenticate(credentials)
        if user:
            session = self.session_manager.create_session(user)
            return session
        return None
    
    def logout(self, session_id):
        self.session_manager.destroy_session(session_id)
""",
                metadata={"file_path": "auth/controller.py", "repository": "auth-service"}
            ),
            MockDocument(
                page_content="""
class UserService:
    def __init__(self):
        self.database = Database()
        self.email_service = EmailService()
    
    def authenticate(self, credentials):
        user = self.database.find_user(credentials.email)
        if user and self.verify_password(credentials.password, user.password_hash):
            self.email_service.send_login_notification(user.email)
            return user
        return None
    
    def verify_password(self, password, hash):
        return bcrypt.checkpw(password, hash)
""",
                metadata={"file_path": "user/service.py", "repository": "user-service"}
            ),
            MockDocument(
                page_content="""
function PaymentController() {
    this.paymentService = new PaymentService();
    this.orderService = new OrderService();
}

PaymentController.prototype.processPayment = function(paymentData) {
    const validation = this.paymentService.validatePayment(paymentData);
    if (validation.isValid) {
        const result = this.paymentService.chargeCard(paymentData);
        if (result.success) {
            this.orderService.updateOrderStatus(paymentData.orderId, 'paid');
            return { success: true, transactionId: result.transactionId };
        }
    }
    return { success: false, error: 'Payment failed' };
};
""",
                metadata={"file_path": "payment/controller.js", "repository": "payment-service"}
            )
        ]
    
    def similarity_search(self, query, k=5):
        """Mock similarity search returning sample documents"""
        print(f"[MOCK] Searching for: {query} (k={k})")
        # Return relevant docs based on query keywords
        if any(word in query.lower() for word in ['auth', 'login', 'user']):
            return self.sample_docs[:2]  # Return auth-related docs
        elif any(word in query.lower() for word in ['payment', 'order', 'charge']):
            return [self.sample_docs[2]]  # Return payment doc
        else:
            return self.sample_docs  # Return all docs


def demonstrate_agent_routing():
    """Demonstrate intelligent agent routing"""
    print("=" * 60)
    print("DEMO: Agent Router Pattern")
    print("=" * 60)
    
    # Setup components
    mock_rag_agent = MockRAGAgent()
    mock_vectorstore = MockVectorStore()
    mock_llm = None  # Not needed for this demo
    
    diagram_handler = DiagramHandler(mock_vectorstore, mock_llm)
    agent_router = AgentRouter(mock_rag_agent, diagram_handler)
    
    # Test queries
    test_queries = [
        # Diagram requests
        "Show me a sequence diagram for user authentication",
        "Generate a flow diagram for the payment process",
        "Visualize how the login system works",
        "Create mermaid code for order processing",
        
        # Regular requests
        "How does authentication work in the system?",
        "What are the available API endpoints?",
        "Explain the payment validation logic"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: \"{query}\"")
        
        # Check routing decision
        is_diagram = agent_router._is_diagram_request(query)
        print(f"   → Routed to: {'DiagramHandler' if is_diagram else 'RAGAgent'}")
        
        # Get response (simplified for demo)
        if is_diagram:
            print("   → Response type: Diagram generation")
        else:
            print("   → Response type: Text-based answer")


def demonstrate_sequence_detection():
    """Demonstrate sequence pattern detection"""
    print("\n" + "=" * 60)
    print("DEMO: Sequence Pattern Detection")
    print("=" * 60)
    
    detector = SequenceDetector()
    
    test_codes = [
        ("Python", """
class OrderProcessor:
    def process_order(self, order):
        payment = self.payment_service.charge(order.total)
        if payment.success:
            self.inventory_service.reserve_items(order.items)
            self.email_service.send_confirmation(order.customer_email)
        return payment
"""),
        ("JavaScript", """
function checkoutOrder(order) {
    const validation = validationService.validateOrder(order);
    if (validation.isValid) {
        const payment = paymentGateway.processPayment(order.payment);
        if (payment.success) {
            orderService.createOrder(order);
            emailService.sendReceipt(order.customerEmail);
        }
    }
    return validation;
}
"""),
        ("C#", """
public class UserController 
{
    public ActionResult Register(UserModel user)
    {
        var validation = this.validationService.ValidateUser(user);
        if (validation.IsValid)
        {
            var hashedPassword = this.cryptoService.HashPassword(user.Password);
            var savedUser = this.userRepository.SaveUser(user, hashedPassword);
            this.emailService.SendWelcomeEmail(savedUser.Email);
            return Ok(savedUser);
        }
        return BadRequest(validation.Errors);
    }
}
""")
    ]
    
    for language, code in test_codes:
        print(f"\n{language} Code Analysis:")
        print("-" * 30)
        
        result = detector.analyze_code(code, language.lower())
        print(f"Language: {result.get('language', 'unknown')}")
        print(f"Interactions found: {len(result.get('interactions', []))}")
        
        for interaction in result.get('interactions', []):
            caller = interaction.get('caller', 'Unknown')
            callee = interaction.get('callee', 'Unknown')
            method = interaction.get('method', 'unknown')
            print(f"  {caller} → {callee}.{method}()")


def demonstrate_mermaid_generation():
    """Demonstrate Mermaid diagram generation"""
    print("\n" + "=" * 60)
    print("DEMO: Mermaid Diagram Generation")
    print("=" * 60)
    
    # Setup
    mock_vectorstore = MockVectorStore()
    diagram_handler = DiagramHandler(mock_vectorstore, None)
    
    # Generate diagram for authentication flow
    query = "Show me a sequence diagram for user authentication"
    print(f"Query: {query}")
    print("-" * 40)
    
    result = diagram_handler.generate_sequence_diagram(query)
    
    print(f"Status: {result['status']}")
    print(f"Analysis: {result['analysis_summary']}")
    print(f"Sources: {len(result['source_documents'])} documents")
    
    if result['mermaid_code']:
        print("\nGenerated Mermaid Code:")
        print("-" * 25)
        # Replace \\n with actual newlines for display
        mermaid_code = result['mermaid_code'].replace('\\n', '\n')
        print(mermaid_code)
    else:
        print("\nNo diagram generated")


def main():
    """Run all demonstrations"""
    print("Multi-Repository Sequence Diagram Feature Demo")
    print("=" * 60)
    
    try:
        demonstrate_agent_routing()
        demonstrate_sequence_detection()
        demonstrate_mermaid_generation()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)
        print("\nKey Features Demonstrated:")
        print("✅ Intelligent query routing (diagram vs text)")
        print("✅ Multi-language code pattern detection")
        print("✅ Mermaid sequence diagram generation")
        print("✅ Vector store integration")
        print("✅ Error handling and validation")
        
        print("\nTo test with real repositories:")
        print("1. Start the API server: python main.py")
        print("2. Open web/index.html in a browser")
        print("3. Add GitHub repositories")
        print("4. Ask diagram questions like:")
        print("   - 'Show me a sequence diagram for authentication'")
        print("   - 'Generate a flow diagram for payment processing'")
        print("   - 'Visualize how the API handles requests'")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()