# Quick Setup Guide

## Step-by-Step Setup

### 1. Install Python Dependencies

Open a terminal/command prompt in the project directory and run:

```bash
pip install -r requirements.txt
```

**Note**: This will install:
- Flask (web framework)
- PyPDF2 (PDF processing)
- sentence-transformers (embeddings)
- numpy (numerical operations)
- torch (required by sentence-transformers)

The first installation may take a few minutes as it downloads the sentence transformer model (~80MB).

### 2. Prepare Document Files

1. Navigate to the project directory
2. Create a `documents` folder if it doesn't exist:
   ```bash
   mkdir documents
   ```
3. Add your PDF files to the `documents` folder
4. Rename them according to the access control mapping:
   - `company_a_earnings.pdf`
   - `company_b_earnings.pdf`
   - `company_c_earnings.pdf`
   - `company_d_earnings.pdf`
   - `company_e_earnings.pdf`

**Important**: You can use ANY PDF files. The system will work as long as the filenames match those in `access_control.py`.

### 3. Run the Application

```bash
python app.py
```

You should see output like:
```
Initializing document index...
Loaded X text chunks from documents.
System initialized successfully!
...
Starting Flask application...
Open your browser and go to: http://127.0.0.1:5000
```

### 4. Access the Application

1. Open your web browser
2. Go to: `http://127.0.0.1:5000`
3. You should see the login page

### 5. Test the System

#### Test User 1: Alice
1. Login with: `alice@email.com`
2. You'll have access to Company A documents only
3. Try asking: "What was the revenue reported?"
4. Follow up with: "What about the profit margin?"

#### Test User 2: Bob
1. Logout and login with: `bob@email.com`
2. You'll have access to Company B and C documents
3. Try asking questions about these companies

#### Test User 3: Charlie
1. Logout and login with: `charlie@email.com`
2. You'll have access to Company D and E documents
3. Try asking questions about these companies

### 6. Verify Access Control

1. Login as `alice@email.com`
2. Try asking about Company B or Company C
3. You should get no results (or very limited results)
4. This proves access control is working

## Troubleshooting

### "Documents directory not found"
- Make sure you created the `documents` folder
- Check that it's in the same directory as `app.py`

### "No documents found for user"
- Verify PDF files are in the `documents` folder
- Check that filenames match exactly with those in `access_control.py`
- File names are case-sensitive

### "Module not found" errors
- Run `pip install -r requirements.txt` again
- Make sure you're using Python 3.7 or higher

### Slow first startup
- The first run downloads the sentence transformer model (~80MB)
- Document processing may take time depending on PDF size
- Subsequent queries are fast

## Example PDF Files

If you don't have PDF files yet, you can:

1. **Use any existing PDFs**: Rename them to match the expected filenames
2. **Create sample PDFs**: Use any PDF creation tool
3. **Download sample PDFs**: Any text-heavy PDFs will work

The system works with any PDF content - it doesn't need to be earnings calls. Just make sure the filenames match!

## Next Steps

- Review the code in `app.py`, `document_processor.py`, etc.
- Customize user access in `access_control.py`
- Modify the UI templates in `templates/` folder
- Add more documents to the `documents/` folder

