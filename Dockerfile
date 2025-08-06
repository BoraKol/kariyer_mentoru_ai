FROM python:3.13.2

WORKDIR /app

COPY requirements.txt . 
RUN pip install -r requirements.txt

## app içerigi app klasoru icine kopyalandir
COPY ./app . 

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]