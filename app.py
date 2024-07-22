import streamlit as st
import openai
from docx import Document
from PyPDF2 import PdfReader
import io
from database import Interview, Question, Response, Analysis, get_db
from sqlalchemy.orm import Session
from typing import List
import os
from dotenv import load_dotenv
import re

# Загрузка переменных окружения
load_dotenv()

# Установка ключа API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text_from_file(file) -> str:
    text = ""
    if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(io.BytesIO(file.getvalue()))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    elif file.type == "application/pdf":
        pdf = PdfReader(io.BytesIO(file.getvalue()))
        text = "\n".join([page.extract_text() for page in pdf.pages])
    else:
        st.error("Неподдерживаемый формат файла. Пожалуйста, загрузите файл DOCX или PDF.")
    return text

def generate_questions(vacancy_info: str, num_questions: int = 5) -> List[str]:
    prompt = f"""Исходя из следующей информации о вакансии, сгенерируйте {num_questions} соответствующих и содержательных вопросов для собеседования:

Информация о вакансии:
{vacancy_info}

Пожалуйста, предоставьте ровно {num_questions} вопросов для собеседования, которые помогут оценить пригодность кандидата для данной должности. Форматируйте каждый вопрос на новой строке, без нумерации.

Сгенерированные вопросы:"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Вы являетесь опытным помощником по кадровым вопросам, которому поручено создание соответствующих вопросов для собеседования."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500,
        n=1,
        stop=None,
    )

    # Вывод сырого ответа API для отладки
    print("Сырой ответ API:", response.choices[0].message.content)

    # Извлечение вопросов из ответа
    raw_questions = response.choices[0].message.content.strip().split('\n')
    
    # Очистка и форматирование вопросов
    cleaned_questions = []
    for question in raw_questions:
        # Удаление ведущих чисел и точек
        cleaned_question = re.sub(r'^\d+\.?\s*', '', question).strip()
        if cleaned_question:
            cleaned_questions.append(cleaned_question)

    return cleaned_questions[:num_questions]

def save_interview(db: Session, vacancy_info: str, questions: List[str]) -> int:
    new_interview = Interview(vacancy_info=vacancy_info)
    db.add(new_interview)
    db.flush()

    for question in questions:
        new_question = Question(interview_id=new_interview.id, question_text=question)
        db.add(new_question)

    db.commit()
    return new_interview.id

def get_interview(db: Session, interview_id: int):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    questions = db.query(Question).filter(Question.interview_id == interview_id).all()
    return interview, questions

def save_responses(db: Session, interview_id: int, responses: dict):
    for question_id, response_text in responses.items():
        new_response = Response(interview_id=interview_id, question_id=question_id, response_text=response_text)
        db.add(new_response)
    db.commit()

def analyze_responses(vacancy_info: str, questions: List[str], responses: List[str]) -> str:
    prompt = f"""Analyze the candidate's responses to the following interview questions based on the job vacancy information:

Job Vacancy Information:
{vacancy_info}

Interview Questions and Responses:
"""

    for q, r in zip(questions, responses):
        prompt += f"Q: {q}\nA: {r}\n\n"

    prompt += """Please provide a comprehensive analysis of the candidate's suitability for the position in Russian, considering:
1. Relevance of responses to the job requirements
2. Depth of knowledge and experience demonstrated
3. Problem-solving and critical thinking skills
4. Communication skills and clarity of responses
5. Cultural fit and alignment with company values
6. Overall strengths and areas for improvement

Analysis:"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert HR analyst tasked with evaluating candidate responses to interview questions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000,
        n=1,
        stop=None,
    )

    return response.choices[0].message.content.strip()

def save_analysis(db: Session, interview_id: int, analysis_text: str):
    new_analysis = Analysis(interview_id=interview_id, analysis_text=analysis_text)
    db.add(new_analysis)
    db.commit()


st.title("Помощник по собеседованиям")

# Боковая панель для навигации
page = st.sidebar.selectbox("Выберите страницу", ["Создать собеседование", "Провести собеседование", "Просмотр результатов"])

# Сессия базы данных
db = next(get_db())

try:
    if page == "Создать собеседование":
        st.header("Создать новое собеседование")
        uploaded_file = st.file_uploader("Загрузите информацию о вакансии (DOCX или PDF)", type=["docx", "pdf"])
        vacancy_info = st.text_area("Или введите информацию о вакансии здесь:")

        if uploaded_file:
            vacancy_info = extract_text_from_file(uploaded_file)

        if st.button("Сгенерировать вопросы"):
            if vacancy_info:
                questions = generate_questions(vacancy_info)
                interview_id = save_interview(db, vacancy_info, questions)
                st.success(f"Собеседование успешно создано! Идентификатор собеседования: {interview_id}")
                st.subheader("Сгенерированные вопросы:")
                for i, question in enumerate(questions, 1):
                    st.write(f"{i}. {question}")
            else:
                st.error("Пожалуйста, предоставьте информацию о вакансии или загрузите файл.")

    elif page == "Провести собеседование":
        st.header("Провести собеседование")
        
        # Инициализация переменных состояния сессии, если они не существуют
        if 'interview_loaded' not in st.session_state:
            st.session_state.interview_loaded = False
        if 'current_interview' not in st.session_state:
            st.session_state.current_interview = None
        if 'current_questions' not in st.session_state:
            st.session_state.current_questions = None
        
        interview_id = st.number_input("Введите идентификатор собеседования", min_value=1, step=1)
        
        if st.button("Начать собеседование") or st.session_state.interview_loaded:
            if not st.session_state.interview_loaded:
                interview, questions = get_interview(db, interview_id)
                if interview:
                    st.session_state.current_interview = interview
                    st.session_state.current_questions = questions
                    st.session_state.interview_loaded = True
                else:
                    st.error("Собеседование не найдено. Пожалуйста, проверьте идентификатор собеседования.")
                    st.session_state.interview_loaded = False
                
            if st.session_state.interview_loaded:
                st.subheader(f"Собеседование для: {st.session_state.current_interview.vacancy_info[:100]}...")
                responses = {}
                for question in st.session_state.current_questions:
                    response = st.text_area(f"В: {question.question_text}", key=f"q_{question.id}")
                    responses[question.id] = response
                
                if st.button("Отправить ответы"):
                    save_responses(db, st.session_state.current_interview.id, responses)
                    st.success("Ответы успешно отправлены!")
                    # Сброс состояния собеседования после отправки
                    st.session_state.interview_loaded = False
                    st.session_state.current_interview = None
                    st.session_state.current_questions = None
                
        # Добавление кнопки для сброса состояния собеседования
        if st.button("Сбросить собеседование"):
            st.session_state.interview_loaded = False
            st.session_state.current_interview = None
            st.session_state.current_questions = None
            st.experimental_rerun()


    elif page == "Просмотр результатов":
        st.header("Просмотр результатов собеседования")

        # Инициализация переменных состояния сессии
        if 'results_loaded' not in st.session_state:
            st.session_state.results_loaded = False
        if 'current_results' not in st.session_state:
            st.session_state.current_results = None
        if 'analysis_result' not in st.session_state:
            st.session_state.analysis_result = None
            
        # Добавляем кнопку для сброса результатов
        if st.button("Сбросить результаты"):
            st.session_state.results_loaded = False
            st.session_state.current_results = None
            st.session_state.analysis_result = None
            st.experimental_rerun()
        
        interview_id = st.number_input("Введите ID интервью", min_value=1, step=1)
        
        if st.button("Просмотреть результаты") or st.session_state.results_loaded:
            if not st.session_state.results_loaded:
                interview, questions = get_interview(db, interview_id)
                if interview:
                    st.session_state.current_results = {
                        'interview': interview,
                        'questions': questions,
                        'responses': []
                    }
                    for question in questions:
                        response = db.query(Response).filter(Response.question_id == question.id).first()
                        if response:
                            st.session_state.current_results['responses'].append(response.response_text)
                        else:
                            st.session_state.current_results['responses'].append("")
                    
                    # Проверяем, есть ли уже сохраненный анализ
                    existing_analysis = db.query(Analysis).filter(Analysis.interview_id == interview_id).first()
                    if existing_analysis:
                        st.session_state.analysis_result = existing_analysis.analysis_text
                    
                    st.session_state.results_loaded = True
                else:
                    st.error("Интервью не найдено. Пожалуйста, проверьте ID интервью.")
                    st.session_state.results_loaded = False
            
            if st.session_state.results_loaded:
                st.subheader(f"Результаты для интервью ID: {interview_id}")
                st.write(f"Информация о вакансии: {st.session_state.current_results['interview'].vacancy_info}")
                
                for q, r in zip(st.session_state.current_results['questions'], st.session_state.current_results['responses']):
                    st.write(f"В: {q.question_text}")
                    st.write(f"О: {r if r else 'Ответ не предоставлен.'}")
                
                if st.button("Анализировать ответы"):
                    analysis = analyze_responses(
                        st.session_state.current_results['interview'].vacancy_info,
                        [q.question_text for q in st.session_state.current_results['questions']],
                        st.session_state.current_results['responses']
                    )
                    st.session_state.analysis_result = analysis
                    
                    # Сохраняем анализ в базу данных
                    save_analysis(db, interview_id, analysis)
                    st.success("Анализ сохранен в базу данных.")
                
                if st.session_state.analysis_result:
                    st.subheader("Анализ:")
                    st.write(st.session_state.analysis_result)
        



finally:
    # Закрытие сессии базы данных
    db.close()
