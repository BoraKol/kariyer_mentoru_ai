FROM python:3.13.2

# calisma dizini 
WORKDIR /app 

# Gereksinimleri kopyalayalim ve yukleyelim 
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# Kodları kopyalayalim 
COPY . .  

## render'da deploy edecegimiz icin render'in kullandigi portu acalim
EXPOSE 10000 

# uvicorn ile FastAPI'yi calistir , render ortamında $PORT degiskeni atanir ve fastapi bu portu dinler
CMD ["uvicorn" , "app:app" , "--host" , "0.0.0.0" , "--port ${PORT:-10000}"]











