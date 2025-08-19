from typing import Dict, Any, List, Optional
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
from ..utils.logging import get_logger
from .prompts import PromptComponents
from .query_optimizer import AdvancedQueryOptimizer, QueryOptimizationResult
from .response_quality_enhancer import EnhancedResponseQualityEnhancer, EnhancementResult

logger = get_logger(__name__)

class QueryAnalysis:
    """Query analysis result with intent and complexity assessment"""
    
    def __init__(self, original: str, optimized: str, intent: str, complexity: str, 
                 retrieval_strategy: str, reasoning_steps: List[str] = None):
        self.original = original
        self.optimized = optimized
        self.intent = intent
        self.complexity = complexity
        self.retrieval_strategy = retrieval_strategy
        self.reasoning_steps = reasoning_steps or []

class RAGAgent:
    """Enhanced RAG Agent with Chain-of-Thought reasoning and advanced capabilities"""
    
    def __init__(self, llm, vectorstore, retriever_kwargs=None, enhancement_config=None):
        self.llm = llm
        self.vectorstore = vectorstore
        self.retriever_kwargs = retriever_kwargs or {"k": 5}
        
        # Enhancement configuration
        self.enhancement_config = enhancement_config or self._get_default_enhancement_config()
        
        # Initialize components
        self.qa_chain = self._create_qa_chain()
        self.query_analyzer = QueryAnalyzer(llm)
        self.context_refiner = ContextRefiner(llm, self.enhancement_config)
        self.response_enhancer = ResponseEnhancer(llm, self.enhancement_config)
        
        # Initialize advanced query optimizer
        self.query_optimizer = AdvancedQueryOptimizer(llm, self.enhancement_config.get("query_optimization", {}))
        
        # Initialize enhanced response quality enhancer
        self.response_quality_enhancer = EnhancedResponseQualityEnhancer(llm, self.enhancement_config.get("response_quality", {}))
        
    def _get_default_enhancement_config(self) -> Dict[str, Any]:
        """Get default enhancement configuration"""
        return {
            "max_reasoning_steps": 5,
            "reasoning_transparency": True,
            "max_refinement_iterations": 3,
            "quality_threshold": 0.8,
            "context_optimization": True,
            "max_enhancement_iterations": 2,
            "quality_validation": True,
            "response_improvement": True
        }
        
    def _create_qa_chain(self):
        """Create the QA chain with custom prompt"""

        prompt_template = PromptComponents.build_full_prompt()
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
    
    def process_query(self, question: str) -> Dict[str, Any]:
        """Enhanced query method with Chain-of-Thought reasoning and advanced query optimization"""
        logger.info(f"Processing enhanced query with optimization: {question[:100]}...")
        
        try:
            # Step 1: Advanced query optimization
            optimization_result = self._optimize_query(question)
            logger.info(f"Query optimization completed: strategy={optimization_result.strategy_used.value}, confidence={optimization_result.confidence_score:.2f}")
            
            # Step 2: Analyze optimized queries for intent and complexity
            primary_query = optimization_result.optimized_queries[0]
            query_analysis = self._analyze_query(primary_query)
            logger.info(f"Query analysis: intent={query_analysis.intent}, complexity={query_analysis.complexity}")
            
            # Step 3: Build context using optimized queries
            if len(optimization_result.optimized_queries) > 1:
                # Use multi-query strategy for comprehensive retrieval
                context = self._build_context_with_multi_queries(optimization_result.optimized_queries, query_analysis)
            else:
                # Use single optimized query
                context = self._build_context_with_reasoning(primary_query, query_analysis)
            
            logger.info(f"Context built with {len(context)} documents using {len(optimization_result.optimized_queries)} queries")
            
            # Step 4: Refine context iteratively
            refined_context = self._refine_context(context, primary_query)
            logger.info(f"Context refined to {len(refined_context)} documents")
            
            # Step 5: Generate response with reasoning transparency
            response = self._generate_response_with_reasoning(primary_query, refined_context, query_analysis)
            
            # Step 6: Validate and enhance response quality
            enhanced_response = self._enhance_response_quality(response, refined_context, primary_query)
            
            # Format final response with enhancement and optimization metadata
            return self._format_enhanced_response_with_optimization(enhanced_response, query_analysis, refined_context, optimization_result)
            
        except Exception as e:
            logger.error(f"Enhanced query with optimization failed: {str(e)}")
            return self._fallback_to_basic_query(question, e)
    
    def _analyze_query(self, question: str) -> QueryAnalysis:
        """Analyze query for intent, complexity, and optimization"""
        try:
            return self.query_analyzer.analyze_query(question)
        except Exception as e:
            logger.warning(f"Query analysis failed, using fallback: {str(e)}")
            return QueryAnalysis(
                original=question,
                optimized=question,
                intent="general",
                complexity="medium",
                retrieval_strategy="standard"
            )
    
    def _build_context_with_reasoning(self, question: str, query_analysis: QueryAnalysis) -> List[Document]:
        """Build initial context with reasoning about relevance"""
        try:
            # Adjust retrieval strategy based on query analysis
            retrieval_kwargs = self._get_adaptive_retrieval_kwargs(query_analysis)
            
            # Perform initial retrieval
            initial_docs = self.vectorstore.similarity_search(question, **retrieval_kwargs)
            
            # Add reasoning about document relevance
            for doc in initial_docs:
                doc.metadata['relevance_reasoning'] = self._assess_document_relevance(doc, question, query_analysis)
            
            return initial_docs
        except Exception as e:
            logger.warning(f"Context building failed, using fallback: {str(e)}")
            return self.vectorstore.similarity_search(question, k=5)
    
    def _get_adaptive_retrieval_kwargs(self, query_analysis: QueryAnalysis) -> Dict[str, Any]:
        """Get adaptive retrieval parameters based on query analysis"""
        base_kwargs = self.retriever_kwargs.copy()
        
        # Adjust retrieval count based on complexity
        if query_analysis.complexity == "high":
            base_kwargs["k"] = min(base_kwargs.get("k", 5) * 2, 20)
        elif query_analysis.complexity == "low":
            base_kwargs["k"] = max(base_kwargs.get("k", 5) // 2, 3)
        
        # Add metadata filtering for specific intents
        if query_analysis.intent == "code_analysis":
            base_kwargs["filter"] = {"language": {"$in": ["python", "javascript", "typescript", "csharp"]}}
        elif query_analysis.intent == "configuration":
            base_kwargs["filter"] = {"file_path": {"$regex": ".*\\.(yml|yaml|json|toml|ini|conf)$"}}
        
        return base_kwargs
    
    def _optimize_query(self, question: str) -> QueryOptimizationResult:
        """Optimize query using advanced optimization strategies"""
        try:
            # Get query optimization configuration
            query_opt_config = self.enhancement_config.get("query_optimization", {})
            
            # Create context for optimization
            optimization_context = {
                "original_query": question,
                "enhancement_config": self.enhancement_config
            }
            
            # Perform query optimization
            optimization_result = self.query_optimizer.optimize_query(question, optimization_context)
            
            logger.info(f"Query optimization completed: {len(optimization_result.optimized_queries)} queries, strategy: {optimization_result.strategy_used.value}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Query optimization failed: {str(e)}")
            # Return fallback optimization result
            return QueryOptimizationResult(
                original_query=question,
                optimized_queries=[question],
                strategy_used=self.query_optimizer.strategy_selector.select_strategy(
                    self.query_optimizer.semantic_analyzer.analyze_query(question)
                ),
                confidence_score=0.5,
                reasoning=f"Optimization failed, using original query: {str(e)}",
                metadata={"error": str(e)}
            )
    
    def _build_context_with_multi_queries(self, queries: List[str], query_analysis: QueryAnalysis) -> List[Document]:
        """Build context using multiple optimized queries for comprehensive retrieval"""
        all_documents = []
        
        try:
            for i, query in enumerate(queries):
                logger.info(f"Processing query {i+1}/{len(queries)}: {query[:50]}...")
                
                # Get adaptive retrieval parameters for this query
                retrieval_kwargs = self._get_adaptive_retrieval_kwargs(query_analysis)
                
                # Retrieve documents for this query
                try:
                    documents = self.vectorstore.similarity_search(query, **retrieval_kwargs)
                    all_documents.extend(documents)
                    logger.info(f"Retrieved {len(documents)} documents for query {i+1}")
                except Exception as e:
                    logger.warning(f"Failed to retrieve documents for query {i+1}: {str(e)}")
                    continue
            
            # Remove duplicate documents based on content
            unique_documents = self._deduplicate_documents(all_documents)
            logger.info(f"Multi-query context built: {len(unique_documents)} unique documents from {len(queries)} queries")
            
            return unique_documents
            
        except Exception as e:
            logger.error(f"Multi-query context building failed: {str(e)}")
            # Fallback to single query
            return self._build_context_with_reasoning(queries[0], query_analysis)
    
    def _deduplicate_documents(self, documents: List[Document]) -> List[Document]:
        """Remove duplicate documents based on content similarity"""
        if not documents:
            return []
        
        unique_documents = []
        seen_contents = set()
        
        for doc in documents:
            # Create a content hash for deduplication
            content_hash = hash(doc.page_content[:100])  # Use first 100 chars as hash
            
            if content_hash not in seen_contents:
                unique_documents.append(doc)
                seen_contents.add(content_hash)
        
        return unique_documents
    
    def _assess_document_relevance(self, doc: Document, question: str, query_analysis: QueryAnalysis) -> str:
        """Assess and explain document relevance to the query"""
        try:
            # Simple relevance assessment based on content overlap
            question_words = set(question.lower().split())
            content_words = set(doc.page_content.lower().split())
            
            overlap = len(question_words.intersection(content_words))
            relevance_score = overlap / len(question_words) if question_words else 0
            
            if relevance_score > 0.3:
                return f"High relevance: {overlap} key terms match"
            elif relevance_score > 0.1:
                return f"Medium relevance: {overlap} key terms match"
            else:
                return f"Low relevance: {overlap} key terms match"
        except Exception:
            return "Relevance assessment unavailable"
    
    def _refine_context(self, initial_context: List[Document], question: str) -> List[Document]:
        """Refine context iteratively for better quality"""
        try:
            return self.context_refiner.refine_context(initial_context, question)
        except Exception as e:
            logger.warning(f"Context refinement failed, using original context: {str(e)}")
            return initial_context
    
    def _generate_response_with_reasoning(self, question: str, context: List[Document], 
                                       query_analysis: QueryAnalysis) -> Dict[str, Any]:
        """Generate response with reasoning transparency"""
        try:
            # Use existing QA chain for response generation
            if hasattr(self.qa_chain, '__call__'):
                # Legacy RetrievalQA format
                result = self.qa_chain({"query": question})
                answer = result["result"]
                source_docs = result.get("source_documents", [])
            else:
                # New chain format
                result = self.qa_chain.invoke({"input": question})
                answer = result["answer"]
                source_docs = result.get("context", [])
            
            # Add reasoning metadata
            response = {
                "answer": answer,
                "source_documents": source_docs,
                "query_analysis": {
                    "intent": query_analysis.intent,
                    "complexity": query_analysis.complexity,
                    "retrieval_strategy": query_analysis.retrieval_strategy,
                    "reasoning_steps": query_analysis.reasoning_steps
                },
                "context_metadata": {
                    "total_documents": len(context),
                    "refinement_iterations": getattr(self.context_refiner, 'last_iterations', 0),
                    "context_quality_score": getattr(self.context_refiner, 'last_quality_score', 0.0)
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            raise
    
    def _enhance_response_quality(self, response: Dict[str, Any], context: List[Document], 
                                question: str) -> Dict[str, Any]:
        """Enhance response quality through validation and improvement"""
        try:
            # Use enhanced response quality enhancer for comprehensive quality improvement
            enhancement_result = self.response_quality_enhancer.enhance_response_quality(
                response, context, question
            )
            
            # Update response with enhanced answer
            enhanced_response = response.copy()
            enhanced_response["answer"] = enhancement_result.enhanced_response
            
            # Add enhancement metadata
            enhanced_response["enhancement_metadata"] = {
                "enhancement_type": enhancement_result.enhancement_type.value,
                "quality_improvement": enhancement_result.quality_improvement,
                "changes_made": enhancement_result.changes_made,
                "enhancement_details": enhancement_result.metadata
            }
            
            logger.info(f"Response quality enhancement completed: improvement={enhancement_result.quality_improvement:.2f}")
            return enhanced_response
            
        except Exception as e:
            logger.warning(f"Enhanced response quality enhancement failed, using original response: {str(e)}")
            # Fallback to basic enhancement
            try:
                return self.response_enhancer.enhance_response(response, context, question)
            except Exception as fallback_error:
                logger.warning(f"Basic response enhancement also failed: {str(fallback_error)}")
                return response
    
    def _format_enhanced_response(self, response: Dict[str, Any], query_analysis: QueryAnalysis, 
                                context: List[Document]) -> Dict[str, Any]:
        """Format final response with enhancement metadata"""
        try:
            # Format source documents
            source_docs = []
            for doc in response.get("source_documents", []):
                source_docs.append({
                    "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    "metadata": doc.metadata
                })
            
            # Build enhanced response
            enhanced_response = {
                "answer": response["answer"],
                "source_documents": source_docs,
                "status": "success",
                "num_sources": len(source_docs),
                "error": None,
                
                # Enhancement metadata
                "reasoning_steps": response.get("query_analysis", {}).get("reasoning_steps", []),
                "query_analysis": response.get("query_analysis", {}),
                "context_quality_score": response.get("context_metadata", {}).get("context_quality_score"),
                "enhancement_iterations": response.get("context_metadata", {}).get("refinement_iterations", 0),
                
                # Enhanced response quality metadata
                "response_quality_enhancement": response.get("enhancement_metadata", {}),
                
                # Maintain backward compatibility
                "mermaid_code": None,
                "diagram_type": None
            }
            
            logger.info(f"Enhanced query processed successfully with {len(source_docs)} source documents")
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Response formatting failed: {str(e)}")
            raise
    
    def _format_enhanced_response_with_optimization(self, response: Dict[str, Any], query_analysis: QueryAnalysis, 
                                                  context: List[Document], optimization_result: QueryOptimizationResult) -> Dict[str, Any]:
        """Format final response with enhancement and optimization metadata"""
        try:
            # Get base enhanced response
            enhanced_response = self._format_enhanced_response(response, query_analysis, context)
            
            # Add optimization metadata
            enhanced_response.update({
                # Query optimization metadata
                "query_optimization": {
                    "original_query": optimization_result.original_query,
                    "optimized_queries": optimization_result.optimized_queries,
                    "strategy_used": optimization_result.strategy_used.value,
                    "confidence_score": optimization_result.confidence_score,
                    "reasoning": optimization_result.reasoning,
                    "metadata": optimization_result.metadata
                },
                
                # Enhanced context information
                "context_metadata": {
                    **enhanced_response.get("context_metadata", {}),
                    "optimization_strategy": optimization_result.strategy_used.value,
                    "query_count": len(optimization_result.optimized_queries),
                    "optimization_confidence": optimization_result.confidence_score
                }
            })
            
            logger.info(f"Enhanced response with optimization metadata: strategy={optimization_result.strategy_used.value}, confidence={optimization_result.confidence_score:.2f}")
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Response formatting with optimization failed: {str(e)}")
            # Fallback to basic enhanced response
            return self._format_enhanced_response(response, query_analysis, context)
    
    def _fallback_to_basic_query(self, question: str, error: Exception) -> Dict[str, Any]:
        """Fallback to basic query processing if enhancement fails"""
        logger.info("Falling back to basic query processing")
        
        try:
            # Use original basic query method
            if hasattr(self.qa_chain, '__call__'):
                result = self.qa_chain({"query": question})
                answer = result["result"]
                source_docs = result.get("source_documents", [])
            else:
                result = self.qa_chain.invoke({"input": question})
                answer = result["answer"]
                source_docs = result.get("context", [])
            
            # Format source documents
            formatted_docs = []
            for doc in source_docs:
                formatted_docs.append({
                    "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    "metadata": doc.metadata
                })
            
            return {
                "answer": answer,
                "source_documents": formatted_docs,
                "status": "success",
                "num_sources": len(formatted_docs),
                "error": None,
                "reasoning_steps": ["Fallback to basic processing due to enhancement error"],
                "query_analysis": {"intent": "fallback", "complexity": "unknown", "retrieval_strategy": "basic"},
                "context_quality_score": 0.5,
                "enhancement_iterations": 0
            }
            
        except Exception as fallback_error:
            logger.error(f"Fallback query also failed: {str(fallback_error)}")
            return {
                "answer": "I encountered an error while processing your query. Please try again.",
                "source_documents": [],
                "status": "error",
                "num_sources": 0,
                "error": str(error),
                "reasoning_steps": ["Error in both enhanced and basic processing"],
                "query_analysis": {"intent": "error", "complexity": "unknown", "retrieval_strategy": "none"},
                "context_quality_score": 0.0,
                "enhancement_iterations": 0
            }
    
    # Maintain backward compatibility with existing methods
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

# Enhancement component classes
class QueryAnalyzer:
    """Analyzes queries for intent, complexity, and optimization"""
    
    def __init__(self, llm):
        self.llm = llm
        self._intent_patterns = self._compile_intent_patterns()
        self._complexity_patterns = self._compile_complexity_patterns()
    
    def analyze_query(self, question: str) -> QueryAnalysis:
        """Analyze query for intent, complexity, and optimization"""
        # Analyze intent
        intent = self._classify_intent(question)
        
        # Assess complexity
        complexity = self._assess_complexity(question)
        
        # Optimize query
        optimized_question = self._optimize_query(question, intent)
        
        # Select retrieval strategy
        retrieval_strategy = self._select_retrieval_strategy(intent, complexity)
        
        # Generate reasoning steps
        reasoning_steps = self._generate_reasoning_steps(question, intent, complexity)
        
        return QueryAnalysis(
            original=question,
            optimized=optimized_question,
            intent=intent,
            complexity=complexity,
            retrieval_strategy=retrieval_strategy,
            reasoning_steps=reasoning_steps
        )
    
    def _compile_intent_patterns(self) -> Dict[str, List[str]]:
        """Compile patterns for intent classification"""
        return {
            "code_analysis": [
                "how does", "explain the code", "what does this function do",
                "analyze the implementation", "code structure", "algorithm"
            ],
            "configuration": [
                "config", "settings", "environment", "setup", "installation",
                "requirements", "dependencies", "configuration"
            ],
            "troubleshooting": [
                "error", "bug", "issue", "problem", "fix", "debug",
                "troubleshoot", "resolve", "workaround"
            ],
            "architecture": [
                "architecture", "design", "structure", "pattern", "flow",
                "diagram", "sequence", "interaction"
            ],
            "general": [
                "what is", "how to", "explain", "describe", "information"
            ]
        }
    
    def _compile_complexity_patterns(self) -> Dict[str, List[str]]:
        """Compile patterns for complexity assessment"""
        return {
            "low": [
                "what is", "define", "explain", "describe", "list"
            ],
            "medium": [
                "how does", "explain the", "what happens when", "compare"
            ],
            "high": [
                "analyze", "debug", "optimize", "refactor", "design",
                "architecture", "complex", "advanced", "sophisticated"
            ]
        }
    
    def _classify_intent(self, question: str) -> str:
        """Classify query intent based on patterns"""
        question_lower = question.lower()
        
        for intent, patterns in self._intent_patterns.items():
            if any(pattern in question_lower for pattern in patterns):
                return intent
        
        return "general"
    
    def _assess_complexity(self, question: str) -> str:
        """Assess query complexity based on patterns and structure"""
        question_lower = question.lower()
        
        # Check for complexity indicators
        for complexity, patterns in self._complexity_patterns.items():
            if any(pattern in question_lower for pattern in patterns):
                return complexity
        
        # Additional complexity factors
        word_count = len(question.split())
        if word_count > 20:
            return "high"
        elif word_count > 10:
            return "medium"
        else:
            return "low"
    
    def _optimize_query(self, question: str, intent: str) -> str:
        """Optimize query for better retrieval"""
        question_lower = question.lower()
        
        # Simple optimization based on intent
        if intent == "code_analysis":
            # Add code-specific terms if not present
            if "code" not in question_lower and "function" not in question_lower:
                question = question + " code implementation"
        elif intent == "configuration":
            # Add config-specific terms if not present
            if "config" not in question_lower and "setting" not in question_lower and "settings" not in question_lower:
                question = question + " configuration settings"
        
        return question
    
    def _select_retrieval_strategy(self, intent: str, complexity: str) -> str:
        """Select appropriate retrieval strategy"""
        if complexity == "high":
            return "multi_pass"
        elif intent == "code_analysis":
            return "code_focused"
        elif intent == "configuration":
            return "config_focused"
        else:
            return "standard"
    
    def _generate_reasoning_steps(self, question: str, intent: str, complexity: str) -> List[str]:
        """Generate reasoning steps for transparency"""
        steps = [
            f"Analyzed query intent: {intent}",
            f"Assessed complexity: {complexity}",
            f"Selected retrieval strategy: {self._select_retrieval_strategy(intent, complexity)}"
        ]
        
        if intent != "general":
            steps.append(f"Applied {intent}-specific optimization")
        
        return steps

class ContextRefiner:
    """Refines context iteratively for better quality"""
    
    def __init__(self, llm, config: Dict[str, Any]):
        self.llm = llm
        self.config = config
        self.last_iterations = 0
        self.last_quality_score = 0.0
    
    def refine_context(self, initial_context: List[Document], question: str) -> List[Document]:
        """Refine context iteratively for better quality"""
        context = initial_context
        self.last_iterations = 0
        
        for iteration in range(self.config.max_refinement_iterations):
            # Assess current context quality
            quality_score = self._assess_context_quality(context, question)
            self.last_quality_score = quality_score
            
            if quality_score >= self.config.quality_threshold:
                break
            
            # Optimize context based on quality assessment
            context = self._optimize_context(context, question, quality_score)
            self.last_iterations += 1
        
        return context
    
    def _assess_context_quality(self, context: List[Document], question: str) -> float:
        """Assess context quality based on relevance and coverage"""
        if not context:
            return 0.0
        
        # Simple quality assessment based on content overlap
        question_words = set(question.lower().split())
        total_overlap = 0
        
        for doc in context:
            content_words = set(doc.page_content.lower().split())
            overlap = len(question_words.intersection(content_words))
            total_overlap += overlap
        
        # Normalize by question length and document count
        avg_overlap = total_overlap / (len(question_words) * len(context)) if question_words else 0
        return min(avg_overlap * 10, 1.0)  # Scale to 0-1 range
    
    def _optimize_context(self, context: List[Document], question: str, quality_score: float) -> List[Document]:
        """Optimize context based on quality assessment"""
        if quality_score > 0.6:
            # High quality - minimal optimization
            return context
        
        # Low quality - try to improve
        try:
            # Re-rank documents by relevance
            question_words = set(question.lower().split())
            scored_docs = []
            
            for doc in context:
                content_words = set(doc.page_content.lower().split())
                overlap = len(question_words.intersection(content_words))
                scored_docs.append((doc, overlap))
            
            # Sort by relevance score
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            # Return top documents
            return [doc for doc, score in scored_docs[:len(context)]]
            
        except Exception:
            # If optimization fails, return original context
            return context

class ResponseEnhancer:
    """Enhances response quality through validation and improvement"""
    
    def __init__(self, llm, config: Dict[str, Any]):
        self.llm = llm
        self.config = config
    
    def enhance_response(self, response: Dict[str, Any], context: List[Document], question: str) -> Dict[str, Any]:
        """Enhance response quality through validation and improvement"""
        enhanced_response = response.copy()
        
        for iteration in range(self.config.max_enhancement_iterations):
            # Validate current response quality
            validation_result = self._validate_response(enhanced_response, context, question)
            
            if validation_result.get("is_satisfactory", True):
                break
            
            # Improve response based on validation feedback
            enhanced_response = self._improve_response(
                enhanced_response, context, question, validation_result
            )
        
        return enhanced_response
    
    def _validate_response(self, response: Dict[str, Any], context: List[Document], question: str) -> Dict[str, Any]:
        """Validate response quality"""
        answer = response.get("answer", "")
        
        # Simple validation checks
        validation_result = {
            "is_satisfactory": True,
            "issues": [],
            "suggestions": []
        }
        
        # Check answer length
        if len(answer) < 50:
            validation_result["is_satisfactory"] = False
            validation_result["issues"].append("Answer too short")
            validation_result["suggestions"].append("Provide more detailed explanation")
        
        # Check for source attribution
        if not response.get("source_documents"):
            validation_result["issues"].append("No source documents")
            validation_result["suggestions"].append("Include source references")
        
        # Check for code examples when appropriate
        if any(word in question.lower() for word in ["code", "function", "implementation"]):
            if "```" not in answer:
                validation_result["suggestions"].append("Consider including code examples")
        
        return validation_result
    
    def _improve_response(self, response: Dict[str, Any], context: List[Document], 
                         question: str, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Improve response based on validation feedback"""
        improved_response = response.copy()
        answer = improved_response.get("answer", "")
        
        # Apply improvements based on validation feedback
        for suggestion in validation_result.get("suggestions", []):
            if "detailed explanation" in suggestion:
                # Add more detailed explanation
                improved_response["answer"] = answer + "\n\n*Note: This answer has been enhanced with additional context. Please review the source documents for more comprehensive information.*"
            elif "code examples" in suggestion and "```" not in answer:
                # Add a note about code examples
                improved_response["answer"] = answer + "\n\n*Note: Consider reviewing the source code for specific implementation details.*"
            elif "source references" in suggestion:
                # Ensure source documents are included
                if not improved_response.get("source_documents"):
                    improved_response["source_documents"] = []
        
        return improved_response
