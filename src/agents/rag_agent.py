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
You are a helpful AI assistant that answers questions based on the provided context from code repositories and documentation.

Use the following context to answer the question. If you cannot find the answer in the context, please say so clearly.

Context:
{context}

Question: {question}

Please provide a detailed and accurate answer based on the context. Include relevant code snippets when applicable and cite the source files.

Answer:
"""
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        try:
            return RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(**self.retriever_kwargs),
                return_source_documents=True,
                chain_type_kwargs={"prompt": prompt}
            )
        except Exception as e:
            logger.error(f"Failed to create QA chain: {str(e)}")
            raise
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the knowledge base"""
        logger.info(f"Processing query: {question[:100]}...")
        
        try:
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
