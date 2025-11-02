"""
Flask web application for Multi-User Document Search and Conversational Q&A System.
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
from document_processor import DocumentIndex
from conversational_qa import ConversationalQA
from access_control import get_user_documents, can_access_document

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'  # Change this in production

# Global document index and QA system
document_index = None
qa_system = None


def initialize_system():
    """
    Initialize the document index and QA system.
    This loads all documents into memory.
    """
    global document_index, qa_system
    
    documents_dir = "documents"
    
    if not os.path.exists(documents_dir):
        print(f"Warning: Documents directory '{documents_dir}' not found!")
        print("Please create the directory and add PDF files.")
        return False
    
    # Initialize document index
    print("Initializing document index...")
    document_index = DocumentIndex()
    document_index.load_documents(documents_dir)
    print(f"Loaded {len(document_index.chunks)} text chunks from documents.")
    
    # Initialize conversational QA system
    qa_system = ConversationalQA(document_index)
    print("System initialized successfully!")
    
    return True


@app.route('/')
def index():
    """Redirect to login page."""
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        user_email = request.form.get('email', '').strip().lower()
        
        if not user_email:
            return render_template('login.html', error='Please enter an email address.')
        
        # Check if user has access to any documents
        user_docs = get_user_documents(user_email)
        
        if not user_docs:
            return render_template('login.html', 
                                 error=f'No documents found for user: {user_email}. '
                                       f'Available users: alice@email.com, bob@email.com, charlie@email.com')
        
        # Store user in session
        session['user_email'] = user_email
        session['user_documents'] = user_docs
        
        return redirect(url_for('chat'))
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Handle user logout."""
    if 'user_email' in session:
        # Clear conversation history for user
        if qa_system:
            qa_system.clear_user_conversation(session['user_email'])
        session.clear()
    return redirect(url_for('login'))


@app.route('/chat')
def chat():
    """Display chat interface."""
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['user_email']
    user_docs = session.get('user_documents', [])
    
    return render_template('chat.html', 
                         user_email=user_email, 
                         user_documents=user_docs)


@app.route('/api/query', methods=['POST'])
def handle_query():
    """Handle query requests via API."""
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if not qa_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    data = request.get_json()
    query = data.get('query', '').strip()
    use_context = data.get('use_context', True)
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    user_email = session['user_email']
    
    try:
        # Get answer from QA system
        result = qa_system.answer_query(
            user_email=user_email,
            query=query,
            use_context=use_context
        )
        
        return jsonify({
            'answer': result['answer'],
            'sources': result['sources'],
            'context_used': result['context_used']
        })
    except Exception as e:
        return jsonify({'error': f'Error processing query: {str(e)}'}), 500


@app.route('/api/clear-conversation', methods=['POST'])
def clear_conversation():
    """Clear conversation history for current user."""
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if not qa_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    user_email = session['user_email']
    qa_system.clear_user_conversation(user_email)
    
    return jsonify({'success': True})


@app.route('/api/user-info')
def user_info():
    """Get current user information."""
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_email = session['user_email']
    user_docs = session.get('user_documents', [])
    
    return jsonify({
        'email': user_email,
        'documents': user_docs,
        'document_count': len(user_docs)
    })


if __name__ == '__main__':
    # Initialize system on startup
    if initialize_system():
        print("\n" + "="*50)
        print("Starting Flask application...")
        print("="*50)
        print("\nAvailable test users:")
        print("  - alice@email.com (Company A)")
        print("  - bob@email.com (Company B & C)")
        print("  - charlie@email.com (Company D & E)")
        print("\nOpen your browser and go to: http://127.0.0.1:5000")
        print("="*50 + "\n")
        
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Failed to initialize system. Please check that the 'documents' directory exists and contains PDF files.")

