from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Interview(Base):
    __tablename__ = 'interviews'

    id = Column(Integer, primary_key=True)
    vacancy_info = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    questions = relationship("Question", back_populates="interview")
    responses = relationship("Response", back_populates="interview")
    analysis = relationship("Analysis", back_populates="interview", uselist=False)

class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    question_text = Column(Text, nullable=False)
    
    interview = relationship("Interview", back_populates="questions")
    responses = relationship("Response", back_populates="question")

class Response(Base):
    __tablename__ = 'responses'

    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    response_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    interview = relationship("Interview", back_populates="responses")
    question = relationship("Question", back_populates="responses")

class Analysis(Base):
    __tablename__ = 'analyses'

    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    analysis_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    interview = relationship("Interview", back_populates="analysis")


# Настройка базы данных
engine = create_engine('sqlite:///interview_assistant.db', echo=True)
Base.metadata.create_all(engine)

# Фабрика сессий
SessionLocal = sessionmaker(bind=engine)

# Функция для получения новой сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
