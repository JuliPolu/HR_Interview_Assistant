from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Interview, Question, Response, Analysis

# Create engine and session
engine = create_engine('sqlite:///interview_assistant.db')
Session = sessionmaker(bind=engine)
session = Session()

def get_all_data():
    # # Retrieve all interviews
    # interviews = session.query(Interview).all()
    # print("Interviews:")
    # for interview in interviews:
    #     print(f"ID: {interview.id}, Vacancy Info: {interview.vacancy_info}, Created At: {interview.created_at}")
    # print("\n")

    # # Retrieve all questions
    # questions = session.query(Question).all()
    # print("Questions:")
    # for question in questions:
    #     print(f"ID: {question.id}, Interview ID: {question.interview_id}, Question Text: {question.question_text}")
    # print("\n")

    # # Retrieve all responses
    # responses = session.query(Response).all()
    # print("Responses:")
    # for response in responses:
    #     print(f"ID: {response.id}, Interview ID: {response.interview_id}, Question ID: {response.question_id}, Response Text: {response.response_text}, Created At: {response.created_at}")
    # print("\n")

    # Retrieve all analyses
    analyses = session.query(Analysis).all()
    print("Analyses:")
    for analysis in analyses:
        print(f"ID: {analysis.id}, Interview ID: {analysis.interview_id}, Analysis Text: {analysis.analysis_text}, Created At: {analysis.created_at}")

if __name__ == "__main__":
    get_all_data()
    session.close()