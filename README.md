<!-- # CleverQuery: AI-Powered Document Analysis Platform -->

<div align="center">
  <img src="staticfiles/logo.png" alt="CleverQuery Logo" width="300"/>
  <br>
  <small>AI-Powered Document Analysis Platform</small>
</div>

## 🚀 Overview

CleverQuery is an AI-powered document analysis platform that helps users extract insights, answer questions, and analyze documents using advanced Retrieval-Augmented Generation (RAG). This project uses Django for the web framework, Gemini AI for text generation, and FAISS for efficient vector search.

With CleverQuery, you can:
- Upload PDF documents for analysis
- Ask questions about your documents and get intelligent answers
- Use specialized session types for different document categories
- Enjoy real-time streaming responses as the AI generates answers
- Create multiple document sessions for different use cases

## ✨ Features

### 📊 Specialized Document Analysis

Choose from various specialized analysis modes:
- **Exam Preparation Guide**: Study materials and educational content
- **Technical Manual Interpreter**: Technical documents and instruction manuals
- **Legal Document Analysis**: Contracts, agreements, and legal texts
- **Nutritional Label Interpreter**: Food labels and nutritional information
- **Financial Report Analysis**: Financial statements and reports
- **Contract Review Assistant**: Contract analysis and review

### 🧠 Advanced RAG Technology

CleverQuery uses a sophisticated Retrieval-Augmented Generation system:
- Document text is split into semantic chunks
- Vector embeddings are created using SentenceTransformers
- FAISS vector database enables semantic search
- Context-aware responses are generated based on the most relevant document sections

### 💬 Interactive Chat Interface

- Real-time streaming responses with typing indicators
- Predefined questions for each document type
- Conversation history for context-aware responses
- Markdown rendering with syntax highlighting for code
- Mobile-responsive design using Tailwind CSS

## 🛠️ Technology Stack

- **Backend**: Django 4.2
- **AI**: Google Generative AI (Gemini 2.0)
- **Vector Database**: FAISS
- **Embedding Model**: Sentence-Transformers (all-MiniLM-L6-v2)
- **Frontend**: HTML, JavaScript, Tailwind CSS
- **Text Processing**: NLTK, PyPDF2
- **Markdown**: Python-Markdown with extensions

## 📋 Installation

### Prerequisites
- Python 3.9+
- pip package manager

### Steps

1. Clone the repository:
```bash
git clone https://github.com/ghubrakesh/CleverQuery.git
cd CleverQuery
```

2. Create and activate a virtual environment:
```bash
python -m venv ccenv
source ccenv/bin/activate  # On Windows: ccenv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create a .env file in the project root
echo "GENERATIVEAI_API_KEY=your_google_gemini_api_key" > .env
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

8. Access the application at http://localhost:8000

## 🧑‍💻 Usage

1. **Register/Login**: Create an account or log in
2. **Create Session**: Choose a specialized session type for your document
3. **Upload Document**: Upload a PDF document for analysis
4. **Ask Questions**: Type your questions or use the predefined questions
5. **Get Insights**: Receive AI-generated answers based on your document content
