"""
Conversational Q&A module for maintaining context across multiple queries.
"""

from typing import List, Dict, Optional
from document_processor import DocumentIndex
from access_control import get_allowed_documents_set


class ConversationManager:
    """
    Manages conversation context for each user.
    """
    
    def __init__(self):
        # Store conversation history per user
        # Format: {user_email: [{'query': str, 'answer': str, 'context': str}, ...]}
        self.conversations: Dict[str, List[Dict]] = {}
    
    def get_conversation_history(self, user_email: str) -> List[Dict]:
        """
        Get conversation history for a user.
        
        Args:
            user_email: User's email address
            
        Returns:
            List of conversation entries
        """
        return self.conversations.get(user_email, [])
    
    def add_to_conversation(self, user_email: str, query: str, answer: str, context: str = ""):
        """
        Add a query-answer pair to conversation history.
        
        Args:
            user_email: User's email address
            query: User's query
            answer: System's answer
            context: Relevant context from documents
        """
        if user_email not in self.conversations:
            self.conversations[user_email] = []
        
        self.conversations[user_email].append({
            'query': query,
            'answer': answer,
            'context': context
        })
    
    def clear_conversation(self, user_email: str):
        """
        Clear conversation history for a user.
        
        Args:
            user_email: User's email address
        """
        if user_email in self.conversations:
            self.conversations[user_email] = []
    
    def build_context_string(self, user_email: str, max_entries: int = 3) -> str:
        """
        Build a context string from recent conversation history.
        
        Args:
            user_email: User's email address
            max_entries: Maximum number of recent entries to include
            
        Returns:
            Context string for use in query enhancement
        """
        history = self.get_conversation_history(user_email)
        if not history:
            return ""
        
        # Get the last N entries
        recent = history[-max_entries:]
        
        context_parts = []
        for entry in recent:
            context_parts.append(f"Previous question: {entry['query']}")
            context_parts.append(f"Previous answer: {entry['answer'][:200]}...")  # Truncate long answers
        
        return "\n".join(context_parts)


class ConversationalQA:
    """
    Handles conversational Q&A with context maintenance.
    """
    
    def __init__(self, document_index: DocumentIndex):
        self.document_index = document_index
        self.conversation_manager = ConversationManager()
    
    def answer_query(self, user_email: str, query: str, use_context: bool = True) -> Dict:
        """
        Answer a user query with conversational context.
        
        Args:
            user_email: User's email address
            query: User's query text
            use_context: Whether to use conversation context
            
        Returns:
            Dictionary with 'answer', 'sources', and 'context_used' keys
        """
        # Get user's allowed documents
        allowed_docs = get_allowed_documents_set(user_email)
        
        # Check if query mentions company names that user doesn't have access to
        query_lower = query.lower()
        company_mapping = {
            'company_a': 'company_a_earnings.pdf',
            'company_b': 'company_b_earnings.pdf',
            'company_c': 'company_c_earnings.pdf',
            'company_d': 'company_d_earnings.pdf',
            'company_e': 'company_e_earnings.pdf',
            'company a': 'company_a_earnings.pdf',
            'company b': 'company_b_earnings.pdf',
            'company c': 'company_c_earnings.pdf',
            'company d': 'company_d_earnings.pdf',
            'company e': 'company_e_earnings.pdf',
        }
        
        # Also check for document filename patterns
        for doc_name in ['company_a_earnings.pdf', 'company_b_earnings.pdf', 'company_c_earnings.pdf', 
                         'company_d_earnings.pdf', 'company_e_earnings.pdf']:
            doc_base = doc_name.replace('_earnings.pdf', '').replace('.pdf', '')
            if doc_base in query_lower and doc_name not in company_mapping.values():
                company_mapping[doc_base] = doc_name
        
        # Detect if query asks about a specific company
        mentioned_companies = []
        for company_name, doc_name in company_mapping.items():
            if company_name in query_lower:
                mentioned_companies.append((company_name, doc_name))
        
        # If query mentions a company that user doesn't have access to, reject early
        if mentioned_companies:
            unauthorized_mentions = []
            for company_name, doc_name in mentioned_companies:
                if doc_name not in allowed_docs:
                    unauthorized_mentions.append(company_name.upper())
            
            if unauthorized_mentions:
                return {
                    'answer': f"I don't have access to information about {', '.join(unauthorized_mentions)}. I can only search within the documents you have access to: {', '.join(allowed_docs)}. Please ask questions about the companies I have access to.",
                    'sources': [],
                    'context_used': False
                }
        
        # Build enhanced query with context if enabled
        enhanced_query = query
        context_used = False
        
        if use_context:
            context_string = self.conversation_manager.build_context_string(user_email)
            if context_string:
                enhanced_query = f"{query}\n\nContext from previous conversation:\n{context_string}"
                context_used = True
        
        # Search for relevant chunks
        search_results = self.document_index.search(
            query=enhanced_query,
            top_k=3,
            allowed_documents=allowed_docs
        )
        
        # If no results found, try without context
        if not search_results and context_used:
            search_results = self.document_index.search(
                query=query,
                top_k=3,
                allowed_documents=allowed_docs
            )
            context_used = False
        
        # Minimum similarity threshold to ensure relevance
        # Higher threshold = more relevant results only
        MIN_SIMILARITY_THRESHOLD = 0.40  # Only return results above this similarity score (increased from 0.35)
        
        # Build answer from search results
        if search_results:
            # Double-check access control - ensure all results are from allowed documents
            # This is a safety check to prevent any unauthorized access
            filtered_results = []
            for result in search_results:
                doc_name = result.get('document', '')
                if doc_name in allowed_docs:
                    filtered_results.append(result)
                else:
                    # Log warning if unauthorized document found (should not happen)
                    print(f"WARNING: Unauthorized document '{doc_name}' found in results for user '{user_email}'")
            
            # Filter by similarity threshold - only include results with reasonable similarity
            high_similarity_results = []
            for result in filtered_results:
                similarity = result.get('similarity', 0)
                if similarity >= MIN_SIMILARITY_THRESHOLD:
                    high_similarity_results.append(result)
            
            if high_similarity_results:
                # Combine top chunks into answer (only high similarity results)
                answer_parts = []
                sources = []
                
                for result in high_similarity_results[:3]:  # Top 3 results
                    answer_parts.append(result['text'])
                    sources.append({
                        'document': result['document'],
                        'page': result.get('page', 'N/A'),
                        'similarity': f"{result['similarity']:.2f}"
                    })
                
                answer = "\n\n".join(answer_parts)
                
                # Truncate if too long
                if len(answer) > 1000:
                    answer = answer[:1000] + "..."
            else:
                # No results above similarity threshold
                answer = f"I couldn't find highly relevant information in the documents you have access to ({', '.join(allowed_docs)}). The search results didn't meet the relevance threshold (minimum similarity: {MIN_SIMILARITY_THRESHOLD:.2f}). Please try rephrasing your question or asking about topics that might be in your accessible documents."
                sources = []
        else:
            answer = "I couldn't find relevant information in the documents you have access to. Please try rephrasing your question."
            sources = []
        
        # Store in conversation history
        self.conversation_manager.add_to_conversation(
            user_email=user_email,
            query=query,
            answer=answer,
            context="; ".join([s['document'] for s in sources])
        )
        
        return {
            'answer': answer,
            'sources': sources,
            'context_used': context_used
        }
    
    def clear_user_conversation(self, user_email: str):
        """
        Clear conversation history for a user.
        
        Args:
            user_email: User's email address
        """
        self.conversation_manager.clear_conversation(user_email)

