FROM python:3.13.2

# calisma dizini 
WORKDIR /app 

# Gereksinimleri kopyalayalim ve yukleyelim 
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# Kodları kopyalayalim 
COPY . .  

EXPOSE 8000 

# uvicorn ile FastAPI'yi calistir 
CMD ["uvicorn" , "app:app" , "--host" , "0.0.0.0" , "--port" , "8000" , "--reload"]











