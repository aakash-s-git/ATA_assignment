"""
Document processing module for loading PDFs and creating embeddings.
Uses simple and lightweight libraries to keep the solution simple.
"""

import os
from typing import List, Dict
import PyPDF2
from sentence_transformers import SentenceTransformer
import numpy as np
from collections import defaultdict

# Global variable to cache the embedding model
_embedding_model = None


def get_embedding_model():
    """Lazy load the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        # Using a lightweight sentence transformer model
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extract text chunks from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries with 'text', 'page', and 'chunk_id' keys
    """
    text_chunks = []
    chunk_id = 0
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    # Split text into smaller chunks (sentences or paragraphs)
                    # Simple approach: split by double newlines (paragraphs)
                    paragraphs = text.split('\n\n')
                    for para in paragraphs:
                        para = para.strip()
                        if len(para) > 50:  # Only include substantial chunks
                            text_chunks.append({
                                'text': para,
                                'page': page_num,
                                'chunk_id': chunk_id,
                                'document': os.path.basename(pdf_path)
                            })
                            chunk_id += 1
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
    
    return text_chunks


def create_embeddings(text_chunks: List[Dict]) -> np.ndarray:
    """
    Create embeddings for text chunks.
    
    Args:
        text_chunks: List of text chunk dictionaries
        
    Returns:
        NumPy array of embeddings
    """
    model = get_embedding_model()
    texts = [chunk['text'] for chunk in text_chunks]
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings


class DocumentIndex:
    """
    Simple in-memory document index for storing chunks and embeddings.
    """
    
    def __init__(self):
        self.chunks: List[Dict] = []
        self.embeddings: np.ndarray = None
        self.document_map: Dict[str, List[int]] = defaultdict(list)
        
    def add_document(self, pdf_path: str):
        """
        Add a document to the index.
        
        Args:
            pdf_path: Path to the PDF file
        """
        chunks = extract_text_from_pdf(pdf_path)
        if not chunks:
            return
        
        # Create embeddings for chunks
        chunk_embeddings = create_embeddings(chunks)
        
        # Store chunks and embeddings
        start_idx = len(self.chunks)
        self.chunks.extend(chunks)
        
        if self.embeddings is None:
            self.embeddings = chunk_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, chunk_embeddings])
        
        # Map document to chunk indices
        doc_name = os.path.basename(pdf_path)
        for i in range(start_idx, len(self.chunks)):
            self.document_map[doc_name].append(i)
    
    def search(self, query: str, top_k: int = 5, allowed_documents: set = None) -> List[Dict]:
        """
        Search for relevant chunks.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            allowed_documents: Set of document names the user can access (None = all documents)
            
        Returns:
            List of relevant chunks with similarity scores
        """
        if not self.chunks or self.embeddings is None:
            return []
        
        # If allowed_documents is an empty set, user has no access - return empty
        if allowed_documents is not None and len(allowed_documents) == 0:
            return []
        
        # Create query embedding
        model = get_embedding_model()
        query_embedding = model.encode([query])[0]
        
        # Calculate cosine similarity
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # If access control is enabled, we need to check ALL chunks that are allowed
        # Otherwise, just get top K
        if allowed_documents is not None:
            # Filter FIRST, then sort by similarity
            # This ensures we only consider chunks from allowed documents
            filtered_indices = []
            filtered_similarities = []
            
            for idx in range(len(self.chunks)):
                chunk = self.chunks[idx]
                doc_name = chunk['document']
                
                # Only include chunks from allowed documents
                if doc_name in allowed_documents:
                    filtered_indices.append(idx)
                    filtered_similarities.append(similarities[idx])
            
            # If no allowed documents found, return empty
            if not filtered_indices:
                return []
            
            # Sort by similarity and get top K
            filtered_indices = np.array(filtered_indices)
            filtered_similarities = np.array(filtered_similarities)
            top_indices = filtered_indices[np.argsort(filtered_similarities)[::-1][:top_k]]
            
            # Build results
            results = []
            for idx in top_indices:
                chunk = self.chunks[idx]
                results.append({
                    **chunk,
                    'similarity': float(similarities[idx]),
                    'chunk_index': int(idx)
                })
        else:
            # No access control - get top K directly
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                chunk = self.chunks[idx]
                results.append({
                    **chunk,
                    'similarity': float(similarities[idx]),
                    'chunk_index': int(idx)
                })
        
        return results
    
    def load_documents(self, documents_dir: str):
        """
        Load all PDFs from a directory.
        
        Args:
            documents_dir: Path to directory containing PDFs
        """
        if not os.path.exists(documents_dir):
            print(f"Documents directory not found: {documents_dir}")
            return
        
        pdf_files = [f for f in os.listdir(documents_dir) if f.endswith('.pdf')]
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(documents_dir, pdf_file)
            self.add_document(pdf_path)

