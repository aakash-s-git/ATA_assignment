"""
Access control module for managing user-document permissions.
"""

from typing import List, Set

# User to document access mapping
# Format: user_email -> list of document filenames they can access
USER_DOCUMENT_ACCESS = {
    'alice@email.com': ['company_a_earnings.pdf'],
    'bob@email.com': ['company_b_earnings.pdf', 'company_c_earnings.pdf'],
    'charlie@email.com': ['company_d_earnings.pdf', 'company_e_earnings.pdf'],
    
    # Additional test users
    'aakash@email.com': ['company_a_earnings.pdf'],
    'test1@email.com': ['company_b_earnings.pdf', 'company_c_earnings.pdf'],
    'test2@email.com': ['company_a_earnings.pdf', 'company_b_earnings.pdf'],
}


def get_user_documents(user_email: str) -> List[str]:
    """
    Get list of documents a user can access.
    
    Args:
        user_email: User's email address
        
    Returns:
        List of document filenames the user can access
    """
    return USER_DOCUMENT_ACCESS.get(user_email, [])


def can_access_document(user_email: str, document_name: str) -> bool:
    """
    Check if a user can access a specific document.
    
    Args:
        user_email: User's email address
        document_name: Name of the document file
        
    Returns:
        True if user can access the document, False otherwise
    """
    user_docs = get_user_documents(user_email)
    return document_name in user_docs


def get_allowed_documents_set(user_email: str) -> Set[str]:
    """
    Get set of documents a user can access (for faster lookup).
    
    Args:
        user_email: User's email address
        
    Returns:
        Set of document filenames the user can access
    """
    return set(get_user_documents(user_email))

