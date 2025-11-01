import asyncio
from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
# from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_core.messages import HumanMessage
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
Sen profesyonel bir kariyer danışmanısın. Görevin, bir adayın CV'sini ve iş ilanı metnini karşılaştırarak
uyumluluk değerlendirmesi yapmaktır. Yanıtın {lang_sel} dilinde olmalıdır.

---
📄 CV:
{cv_text}

💼 İş İlanı:
{job_text}
---

Aşağıdaki kurallara **kesinlikle uymalısın**:

1️⃣ **İlk olarak sadece geçerli JSON formatında** şu yapıyı döndür:
{{
  "technical_skills": 0-100 arasında bir tam sayı,
  "communication_skills": 0-100 arasında bir tam sayı,
  "problem_solving": 0-100 arasında bir tam sayı,
  "teamwork": 0-100 arasında bir tam sayı,
  "adaptability": 0-100 arasında bir tam sayı,
  "overall_fit": 0-100 arasında bir tam sayı
}}

2️⃣ JSON çıktısından sonra, aşağıdaki başlıklarla **detaylı ve doğal** açıklama ver:
---
📝 **Detaylı Analiz ve Öneriler ({lang_sel})**
✅ Güçlü Yönler:
- ...

⚠️ Geliştirilmesi Gereken Alanlar:
- ...

💡 İyileştirme Önerileri:
- ...

📊 Genel Değerlendirme:
- ...
---

Kurallar:
- JSON kısmı ve analiz kısmı arasında en az bir boş satır bırak.
- JSON formatına ek yorum ekleme.
- Yanıtın tamamı {lang_sel} dilinde olmalı.
"""
    
    response = client.chat.completions.create(
        model="accounts/fireworks/models/qwen3-coder-480b-a35b-instruct",  # Fireworks modeli
        messages=[
            {"role": "system", "content": "Sen kariyer danışmanı bir asistansın."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=4096,
        temperature=0.2,
    )

    return response.choices[0].message.content


# ---------- API ROUTES ----------
@app.get("/")
def root():
    return {"status" : "ok"}

@app.post("/analyze")
async def analyze(cv: UploadFile, job_text: str = Form(...), lang_sel: str = Form("Türkçe")):
    # Geçici dosyaya kaydet
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await cv.read())
        tmp_path = tmp.name

    # PDF yükle
    loader = PyPDFLoader(tmp_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.split_documents(documents)

    # embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    # knowledge_base = FAISS.from_documents(docs, embedding)

    cv_text = "\n".join([doc.page_content for doc in docs])
    response = generate_feedback(cv_text, job_text, lang_sel)

    # JSON ve analiz kısmını ayıkla
    json_start = response.find("{")
    json_end = response.find("}") + 1
    scores = json.loads(response[json_start:json_end])
    analysis = response[json_end:]

    return JSONResponse(content={"scores": scores, "analysis": analysis})
