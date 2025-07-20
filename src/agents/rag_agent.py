from typing import Dict, Any, List
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
from ..utils.logging import get_logger

logger = get_logger(__name__)

class RAGAgent:
    """RAG Agent for knowledge base queries"""
    
    def __init__(self, llm, vectorstore, retriever_kwargs=None):
        self.llm = llm
        self.vectorstore = vectorstore
        self.retriever_kwargs = retriever_kwargs or {"k": 5}
        self.qa_chain = self._create_qa_chain()
        
    def _create_qa_chain(self):
        """Create the QA chain with custom prompt"""
        prompt_template = """
You are an expert AI assistant specialized in providing accurate, well-documented technical answers based on provided code repositories and documentation. Your responses must be comprehensive, technically precise, and properly sourced.

Guidelines for responses:
1. First analyze the question to determine what information is being requested
2. Thoroughly search the provided context for relevant information
3. If the answer exists in the context:
   - Provide a complete, detailed response
   - Include relevant code snippets with proper syntax highlighting when applicable
   - Cite exact source files with paths/line numbers where appropriate
   - Explain technical concepts clearly when helpful
4. If the answer cannot be found in the context:
   - Clearly state this upfront
   - Suggest potential alternative sources or approaches if possible
5. For technical answers:
   - Include any relevant warnings, limitations, or best practices
   - Note version-specific information if available in context
   - Provide complete examples rather than partial code when possible

Context:
{context}

Question: {question}

Please provide a professional, well-structured answer following these guidelines. Organize complex information clearly and prioritize accuracy over brevity.

Answer:
"""
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )

        logger.info("Creating QA chain with custom prompt")
        logger.debug(f"Creating QA chain with prompt: {prompt_template} with variables {prompt.input_variables}")
        
        try:
            # Use the new LangChain approach first, fall back to legacy if needed
            try:
                return RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=self.vectorstore.as_retriever(**self.retriever_kwargs),
                    return_source_documents=True,
                    chain_type_kwargs={"prompt": prompt}
                )
            except Exception as e:
                logger.warning(f"Failed to create QA chain with new approach: {str(e)}")
                # Alternative approach using create_retrieval_chain if available
                from langchain.chains.combine_documents import create_stuff_documents_chain
                from langchain.chains import create_retrieval_chain
                
                document_chain = create_stuff_documents_chain(self.llm, prompt)
                retrieval_chain = create_retrieval_chain(
                    self.vectorstore.as_retriever(**self.retriever_kwargs), 
                    document_chain
                )
                return retrieval_chain
                
        except Exception as e:
            logger.error(f"Failed to create QA chain: {str(e)}")
            raise
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the knowledge base"""
        logger.info(f"Processing query: {question[:100]}...")
        
        try:
            # Handle both legacy and new chain formats
            if hasattr(self.qa_chain, '__call__'):
                # Legacy RetrievalQA format
                result = self.qa_chain({"query": question})
                
                # Format source documents
                source_docs = []
                for doc in result.get("source_documents", []):
                    source_docs.append({
                        "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                        "metadata": doc.metadata
                    })
                
                response = {
                    "answer": result["result"],
                    "source_documents": source_docs,
                    "status": "success",
                    "num_sources": len(source_docs)
                }
            else:
                # New chain format
                result = self.qa_chain.invoke({"input": question})
                
                # Format source documents
                source_docs = []
                context_docs = result.get("context", [])
                if context_docs:
                    for doc in context_docs:
                        source_docs.append({
                            "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                            "metadata": doc.metadata
                        })
                
                response = {
                    "answer": result["answer"],
                    "source_documents": source_docs,
                    "status": "success",
                    "num_sources": len(source_docs)
                }
            
            logger.info(f"Query processed successfully with {len(source_docs)} source documents")
            return response
            
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            return {
                "answer": "I encountered an error while processing your query. Please try again.",
                "source_documents": [],
                "status": "error",
                "error": str(e)
            }
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Perform similarity search without LLM"""
        try:
            return self.vectorstore.similarity_search(query, k=k)
        except Exception as e:
            logger.error(f"Similarity search failed: {str(e)}")
            return []
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store"""
        try:
            return self.vectorstore.add_documents(documents)
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the vector store collection"""
        try:
            return self.vectorstore.get_collection_info()
        except Exception as e:
            logger.error(f"Failed to get collection info: {str(e)}")
            return {"error": str(e)}
