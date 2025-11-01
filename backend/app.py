import asyncio
from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage
import tempfile, os, json
from dotenv import load_dotenv
from fireworks.client import Fireworks  # 🔥 Fireworks SDK

load_dotenv()

fw_api_key = os.getenv("FIREWORKS_API_KEY")
if fw_api_key is None:
    raise ValueError("FIREWORKS_API_KEY environment variable is not set.")

client = Fireworks(api_key=fw_api_key)  # ✅ Doğru client

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_feedback(cv_text, job_text, lang_sel):
    prompt = f"""
Sen bir kariyer asistanısın.Sadece seninle paylaşılan CV ve ilan metnini göz önünde bulundurarak {lang_sel} dilinde kullanıcıya cevap verirsin. 

CV:
{cv_text}

İş İlanı:
{job_text}

Cevabı şu iki bölüm halinde ver:
[1] JSON formatında skorlar(Sadece bu JSON'u döndür):
{{
    "technical_skills": yüzde(0-100),
    "communication_skills": yüzde(0-100),
    "problem_solving": yüzde(0-100),
    "teamwork": yüzde(0-100),
    "adaptability": yüzde(0-100), 
    "overall_fit": yüzde(0-100) 
}}

[2] Açıklayıcı analiz ({lang_sel} dilinde, emoji kullanarak): 
- Kullanıcının güçlü yönleri(✅ ile sırala)
- Eksik yönleri(⚠️ ile sırala)
- Cv'yi bu ilana daha uygun hale getirmek için öneriler(💡 ile sırala)
- Genel değerlendirme ve öneriler(📊 ile sırala)
"""
    
    response = client.chat.completions.create(
        model="accounts/fireworks/models/gpt-oss-20b",  # Fireworks modeli
        messages=[
            {"role": "system", "content": "Sen kariyer danışmanı bir asistansın."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1024,
        temperature=0.2,
    )

    return response.choices[0].message.content



# ---------- API ROUTES ----------
@app.post("/analyze")
async def analyze(cv: UploadFile, job_text: str = Form(...), lang_sel: str = Form("Türkçe")):
    # Geçici dosyaya kaydet
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await cv.read())
        tmp_path = tmp.name

    # PDF yükle
    loader = PyPDFLoader(tmp_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
    docs = splitter.split_documents(documents)

    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-MiniLM-L3-v2")
    # knowledge_base = FAISS.from_documents(docs, embedding)

    cv_text = "\n".join([doc.page_content for doc in documents])
    response = generate_feedback(cv_text, job_text, lang_sel)

    # JSON ve analiz kısmını ayıkla
    json_start = response.find("{")
    json_end = response.find("}") + 1
    scores = json.loads(response[json_start:json_end])
    analysis = response[json_end:]

    return JSONResponse(content={"scores": scores, "analysis": analysis})
