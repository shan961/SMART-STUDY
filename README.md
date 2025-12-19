# 📚 StudySphere AI – RAG-Based Study Assistant

StudySphere AI is an **AI-powered study assistant** designed to help students learn more efficiently using their own study materials.  
The backend is built with **FastAPI** and implements a **Retrieval-Augmented Generation (RAG)** pipeline using **Google Gemini**.

Instead of giving generic answers, the system responds **only from the content of uploaded PDFs**, ensuring accuracy and relevance.

---

## 🧠 How It Works (RAG Pipeline)

1. Users upload PDF study materials  
2. The system:
   - Extracts text from PDFs
   - Splits content into smaller chunks
   - Converts chunks into vector embeddings
   - Stores embeddings using FAISS
3. When a student asks a question:
   - Relevant chunks are retrieved from stored embeddings
   - Gemini generates an answer **only from the retrieved context**
4. The system also auto-generates:
   - Summaries
   - MCQs
   - Flashcards for quick revision

---

## 🚀 Features

- 📄 PDF upload & text extraction
- 🧠 Retrieval-Augmented Generation (RAG)
- ❓ Context-aware question answering
- 📝 Automatic summary generation
- 🧪 MCQ & flashcard generation
- ⚡ FastAPI REST backend
- 🤖 Google Gemini integration

---

## 🛠️ Tech Stack

- **Backend Framework:** FastAPI
- **Language:** Python
- **AI Model:** Google Gemini
- **Vector Database:** FAISS
- **Embeddings:** Sentence Transformers
- **PDF Processing:** PyPDF / similar librarie


---

## ⚙️ Setup & Run Locally

##Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd backend

## 📦 Dependencies

- fastapi – Backend framework  
- uvicorn – ASGI server  
- pypdf – PDF text extraction  
- google-generativeai – Gemini API integration  
- sentence-transformers – Text embeddings  
- faiss-cpu – Vector similarity search  
- numpy – Numerical operations  
- python-multipart – File uploads

## Run the server

uvicorn main:app --reload

##API Documentation

Once the server is running, open for api testing:

http://127.0.0.1:8000/docs

---
## Screenshots


