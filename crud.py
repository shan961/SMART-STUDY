from sqlalchemy.orm import Session
from models import PDF, Chat, GeneratedContent

def create_pdf(db: Session, filename: str):
    pdf = PDF(filename=filename)
    db.add(pdf)
    db.commit()
    db.refresh(pdf)
    return pdf

def get_pdfs(db: Session):
    return db.query(PDF).all()

def save_chat(db: Session, pdf_id: int, question: str, answer: str):
    chat = Chat(pdf_id=pdf_id, question=question, answer=answer)
    db.add(chat)
    db.commit()

def get_chat_history(db: Session, pdf_id: int):
    return db.query(Chat).filter(Chat.pdf_id == pdf_id).all()

def get_generated(db: Session, pdf_id: int):
    return db.query(GeneratedContent).filter_by(pdf_id=pdf_id).first()

def save_generated(db: Session, pdf_id: int, summary=None, mcqs=None, flashcards=None):
    item = get_generated(db, pdf_id)

    if not item:
        item = GeneratedContent(pdf_id=pdf_id)
        db.add(item)

    if summary is not None:
        item.summary = summary
    if mcqs is not None:
        item.mcqs = mcqs
    if flashcards is not None:
        item.flashcards = flashcards

    db.commit()
    db.refresh(item)
    return item
