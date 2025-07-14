#!/usr/bin/env python3
"""
Test script to validate API keys and embedding functionality
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_api():
    """Test OpenAI API connection and embeddings"""
    try:
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OpenAI API key not found in environment")
            return False
        
        client = OpenAI(api_key=api_key)
        
        # Test basic API connection
        try:
            response = client.embeddings.create(
                input="test text",
                model="text-embedding-ada-002"
            )
            print("✅ OpenAI API working correctly")
            print(f"   Embedding dimension: {len(response.data[0].embedding)}")
            return True
        except Exception as e:
            print(f"❌ OpenAI embedding test failed: {e}")
            return False
            
    except ImportError:
        print("❌ OpenAI package not installed")
        return False

def test_gemini_api():
    """Test Gemini API connection and embeddings"""
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ Gemini API key not found in environment")
            return False
        
        genai.configure(api_key=api_key)
        
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("Hello")
            print("✅ Gemini API working correctly")
            return True
        except Exception as e:
            print(f"❌ Gemini API test failed: {e}")
            return False
            
    except ImportError:
        print("❌ Gemini package not installed")
        return False

def test_huggingface_local():
    """Test local HuggingFace embeddings"""
    try:
        from sentence_transformers import SentenceTransformer
        
        # Test loading a small model
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        embeddings = model.encode(["test text"])
        print("✅ HuggingFace local embeddings working correctly")
        print(f"   Embedding dimension: {len(embeddings[0])}")
        return True
        
    except ImportError:
        print("❌ sentence-transformers package not installed")
        return False
    except Exception as e:
        print(f"❌ HuggingFace local test failed: {e}")
        return False

def test_chroma_connection():
    """Test Chroma database connection"""
    try:
        import chromadb
        
        chroma_host = os.getenv('CHROMA_HOST', 'localhost')
        chroma_port = int(os.getenv('CHROMA_PORT', '8000'))
        
        try:
            client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
            client.heartbeat()
            print(f"✅ Chroma connection successful ({chroma_host}:{chroma_port})")
            return True
        except Exception as e:
            print(f"❌ Chroma connection failed ({chroma_host}:{chroma_port}): {e}")
            print("   Make sure Chroma server is running")
            return False
            
    except ImportError:
        print("❌ chromadb package not installed")
        return False

def main():
    """Run all tests"""
    print("🔍 Testing API Keys and Services...")
    print("=" * 50)
    
    # Test all services
    tests = [
        ("OpenAI API", test_openai_api),
        ("Gemini API", test_gemini_api),
        ("HuggingFace Local", test_huggingface_local),
        ("Chroma Database", test_chroma_connection)
    ]
    
    results = {}
    for name, test_func in tests:
        print(f"\n🧪 Testing {name}...")
        results[name] = test_func()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    working_count = sum(results.values())
    total_count = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")
    
    print(f"\n📈 {working_count}/{total_count} services working")
    
    if working_count == 0:
        print("\n⚠️  No embedding services are working!")
        print("   Please check your API keys and service configurations.")
        return 1
    elif results.get("HuggingFace Local", False):
        print("\n✅ At least HuggingFace local embeddings are working - you can proceed!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
