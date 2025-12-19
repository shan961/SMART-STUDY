from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models, crud
import os
from pypdf import PdfReader
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from fpdf import FPDF
from fastapi.responses import FileResponse

# ---------------- SETUP ----------------

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads/pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Gemini
genai.configure(api_key="AIzaSyD5wfrOkQYUaudEky2C3Nbv8h1H_CV3Le4")
gemini = genai.GenerativeModel("gemini-2.5-flash")

# Embeddings
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# -------- SINGLE PDF STATE --------
chunks = []
index = None
active_pdf_id = None

# ---------------- DB ----------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- HELPERS ----------------

def extract_text(file):
    reader = PdfReader(file)
    return " ".join(page.extract_text() or "" for page in reader.pages)

def chunk_text(text, size=400, overlap=80):
    words = text.split()
    out = []
    start = 0
    while start < len(words):
        out.append(" ".join(words[start:start + size]))
        start += size - overlap
    return out

def build_faiss(chunks):
    emb = embedder.encode(chunks).astype(np.float32)
    idx = faiss.IndexFlatL2(emb.shape[1])
    idx.add(emb)
    return idx

def gemini_response(prompt):
    return gemini.generate_content(prompt).text

def get_context(top_k=6):
    return " ".join(chunks[:top_k])

# ---------------- ROUTES ----------------

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    global chunks, index, active_pdf_id

    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF allowed")

    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, "wb") as f:
        f.write(await file.read())

    # Reset previous PDF
    chunks = []
    index = None

    pdf = crud.create_pdf(db, file.filename)
    active_pdf_id = pdf.id

    with open(path, "rb") as f:
        text = extract_text(f)

    chunks = chunk_text(text)
    index = build_faiss(chunks)

    return {"message": "PDF uploaded and activated"}

# ---------------- QA ----------------

@app.get("/qa")
def ask(q: str, db: Session = Depends(get_db)):
    if not index or not chunks:
        raise HTTPException(400, "Upload a PDF first")

    q_emb = embedder.encode([q]).astype(np.float32)
    _, ids = index.search(q_emb, 3)
    context = " ".join(chunks[i] for i in ids[0])

    prompt = f"""
Answer ONLY from the notes.

Notes:
{context}

Question:
{q}
"""

    answer = gemini_response(prompt)

    if active_pdf_id:
        crud.save_chat(db, active_pdf_id, q, answer)

    return {"answer": answer}

# ---------------- SUMMARY ----------------

@app.get("/summary")
def summary(db: Session = Depends(get_db)):
    if not active_pdf_id:
        raise HTTPException(400, "No PDF uploaded")

    saved = crud.get_generated(db, active_pdf_id)
    if saved and saved.summary:
        return {"summary": saved.summary}

    context = get_context()
    result = gemini_response(
        f"Create a concise bullet-point summary:\n{context}"
    )

    crud.save_generated(db, active_pdf_id, summary=result)
    return {"summary": result}


# ---------------- FLASHCARDS ----------------

@app.get("/flashcards")
def flashcards(db: Session = Depends(get_db)):
    if not active_pdf_id:
        raise HTTPException(400, "No PDF uploaded")

    saved = crud.get_generated(db, active_pdf_id)
    if saved and saved.flashcards:
        return {"flashcards": saved.flashcards}

    context = get_context()

    prompt = f"""
Create 10 flashcards from the notes below.
Format exactly like:

Q: ...
A: ...

Notes:
{context}
"""

    result = gemini_response(prompt)

    crud.save_generated(db, active_pdf_id, flashcards=result)

    return {"flashcards": result}


# ---------------- MCQs ----------------

@app.get("/mcq")
def mcq(db: Session = Depends(get_db)):
    if not active_pdf_id:
        raise HTTPException(400, "No PDF uploaded")

    saved = crud.get_generated(db, active_pdf_id)
    if saved and saved.mcqs:
        return {"mcqs": saved.mcqs}

    context = get_context()

    prompt = f"""
Create 5 multiple choice questions (MCQs) from the notes below.
Format each question as:

Q: ...
A) ...
B) ...
C) ...
D) ...
Answer: <correct option letter>

Notes:
{context}
"""

    result = gemini_response(prompt)

    crud.save_generated(db, active_pdf_id, mcqs=result)

    return {"mcqs": result}

@app.get("/download_summary")
def download_summary(db: Session = Depends(get_db)):
    data = crud.get_generated(db, active_pdf_id)
    if not data or not data.summary:
        raise HTTPException(404, "No summary")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in data.summary.split("\n"):
        pdf.multi_cell(0, 8, line)

    path = "summary.pdf"
    pdf.output(path)

    return FileResponse(path, filename="summary.pdf")
@app.get("/download_mcq")
def download_mcq(db: Session = Depends(get_db)):
    data = crud.get_generated(db, active_pdf_id)
    if not data or not data.mcqs:
        raise HTTPException(404, "No MCQs")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in data.mcqs.split("\n"):
        pdf.multi_cell(0, 8, line)

    path = "mcqs.pdf"
    pdf.output(path)

    return FileResponse(path, filename="mcqs.pdf")

@app.get("/download_flashcards")
def download_flashcards(db: Session = Depends(get_db)):
    data = crud.get_generated(db, active_pdf_id)
    if not data or not data.flashcards:
        raise HTTPException(404, "No flashcards")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in data.flashcards.split("\n"):
        pdf.multi_cell(0, 8, line)

    path = "flashcards.pdf"
    pdf.output(path)

    return FileResponse(path, filename="flashcards.pdf")
