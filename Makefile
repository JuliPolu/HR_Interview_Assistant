.PHONY: *


make install:
	pip install -r requirements.txt


make run:
	rm interview_assistant.db
	python3 -c "from database import Base, engine; Base.metadata.create_all(engine)"
	streamlit run app.py


make app:
	streamlit run app.py


You are an expert and experienced python developer and NLP engineer, perfectly create custom chat bots, assistants, proficient in backend and frontend. 
you need to create application that uses llms to generate questions for interview based on vacancy information  and additional database of questions.
 Application should have interact with HR manager to create questions, create some web form to interact with candidate, 
 candidate fills in form with his answers the answers are sent back to HR  and llm analize answers and gives detailed comments on candidate performance. 
 offer please very quick, simple and elegant way to create MVP for described project. describe step by step, use python