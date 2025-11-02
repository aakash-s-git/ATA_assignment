# Multi-User Document Search and Conversational Q&A System

A Python-based web application that provides multi-user document search with conversational Q&A capabilities, featuring user-specific access control and context-aware responses.

## Features

- **Multi-User Support**: Multiple users can access the system simultaneously with isolated sessions
- **Access Control**: Each user can only access documents they're authorized to view
- **Document Search**: Semantic search using sentence transformers for finding relevant excerpts
- **Conversational Q&A**: Maintains context across multiple queries for natural follow-up questions
- **Web Interface**: Simple and intuitive web UI for login and querying

## Project Structure

```
aakash_s_project/
│
├── app.py                      # Main Flask application
├── document_processor.py       # PDF processing and embedding generation
├── access_control.py            # User-document access management
├── conversational_qa.py         # Conversational Q&A with context management
├── requirements.txt             # Python dependencies
├── README.md                    # This file
│
├── documents/                   # Directory for PDF documents
│   ├── company_a_earnings.pdf
│   ├── company_b_earnings.pdf
│   ├── company_c_earnings.pdf
│   ├── company_d_earnings.pdf
│   └── company_e_earnings.pdf
│
└── templates/                   # HTML templates
    ├── login.html              # Login page
    └── chat.html               # Chat interface
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: The first run will download the sentence transformer model (~80MB), which may take a few minutes.

### 2. Prepare Documents

1. Create a `documents` folder in the project root (if it doesn't exist)
2. Add your PDF files to the `documents` folder
3. Name them according to the access control mapping:
   - `company_a_earnings.pdf`
   - `company_b_earnings.pdf`
   - `company_c_earnings.pdf`
   - `company_d_earnings.pdf`
   - `company_e_earnings.pdf`

**Note**: You can use any PDF files. The system will work with any PDFs as long as they match the filenames in `access_control.py`.

### 3. Run the Application

```bash
python app.py
```

The application will start on `http://127.0.0.1:5000`

## Execution Order

1. **Initialization** (`app.py` → `initialize_system()`):
   - Loads all PDF documents from the `documents/` folder
   - Extracts text chunks from each PDF
   - Generates embeddings for all text chunks using sentence transformers
   - Creates the document index in memory
   - Initializes the conversational QA system

2. **User Login** (`/login` route):
   - User enters email address
   - System checks access control mapping
   - If valid, user session is created

3. **Query Processing** (`/api/query` route):
   - User submits a query through the chat interface
   - System retrieves conversation history (if any)
   - Enhances query with context from previous interactions
   - Searches document index with user's allowed documents filter
   - Returns relevant excerpts with sources
   - Stores query-answer pair in conversation history

4. **Context Maintenance**:
   - Each user has isolated conversation history
   - Recent conversation entries are used to enhance follow-up queries
   - Context is automatically included when answering questions

## Test Users

The system comes with pre-configured test users:

- **alice@email.com**: Access to Company A documents only
- **bob@email.com**: Access to Company B and Company C documents
- **charlie@email.com**: Access to Company D and Company E documents

You can add more users by modifying `access_control.py`.

## Usage Examples

### Scenario 1: Access Control Verification

1. Login as `alice@email.com`
2. Ask: "What was the revenue reported in Q4?"
3. System returns results only from Company A documents
4. Alice cannot see information from other companies

### Scenario 2: Conversational Context

1. Login as `bob@email.com`
2. Ask: "What was the revenue for Company B?"
3. Follow up: "What about the profit margin?"
4. The system maintains context and understands "profit margin" refers to Company B

## Technical Details

### Document Processing
- PDFs are split into text chunks (paragraphs)
- Each chunk is embedded using `all-MiniLM-L6-v2` model
- Embeddings are stored in memory for fast retrieval

### Search Algorithm
- Uses cosine similarity between query and document embeddings
- Filters results by user's allowed documents
- Returns top-k most relevant chunks

### Context Management
- Maintains conversation history per user
- Uses last 3 conversation entries for context
- Enhances queries with previous Q&A pairs

## Customization

### Adding New Users

Edit `access_control.py` and add entries to `USER_DOCUMENT_ACCESS`:

```python
USER_DOCUMENT_ACCESS = {
    'newuser@email.com': ['company_a_earnings.pdf', 'company_b_earnings.pdf'],
    # ... existing users
}
```

### Changing Document Directory

Modify the `documents_dir` variable in `app.py`:

```python
documents_dir = "your_custom_directory"
```

### Adjusting Search Results

Modify the `top_k` parameter in `conversational_qa.py`:

```python
search_results = self.document_index.search(
    query=enhanced_query,
    top_k=5,  # Change this number
    allowed_documents=allowed_docs
)
```

## Troubleshooting

### "Documents directory not found"
- Ensure the `documents/` folder exists in the project root
- Add at least one PDF file to the folder

### "No documents found for user"
- Check that the user email matches an entry in `access_control.py`
- Verify that the PDF filenames match those in the access control mapping

### Slow Performance
- First run downloads the sentence transformer model (~80MB)
- Initial document loading creates embeddings (may take time for large PDFs)
- Subsequent queries are fast as everything is in memory

## Limitations

- All documents are loaded into memory (not suitable for very large document collections)
- No persistent storage (conversation history is lost on server restart)
- Basic authentication (email-based, no passwords)
- Single server instance (for production, use proper session management)

## Future Enhancements

- Add vector database (e.g., FAISS) for scalable document storage
- Implement persistent conversation storage
- Add user authentication with passwords
- Support for multiple file formats (DOCX, TXT, etc.)
- Add document upload functionality

## License

This project is provided as-is for educational/demonstration purposes.

