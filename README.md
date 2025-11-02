# 🧠 Kariyer Mentor Asistanı  
**LLM + Streamlit + FastAPI + Docker Compose Entegrasyonlu Uçtan Uca Proje**

Kariyer Mentor Asistanı, kullanıcıların CV’lerini ve başvurmak istedikleri iş ilanlarını karşılaştırarak güçlü ve zayıf yönlerini analiz eden, kişiselleştirilmiş öneriler sunan bir **LLM tabanlı değerlendirme sistemi**dir.


## 🚀 Özellikler

- 📄 PDF formatında CV yükleme desteği  
- 💼 İş ilanı metnini girerek detaylı uyumluluk analizi  
- 🧠 Gelişmiş LLM modeli ile güçlü-zayıf yön analizi ve öneriler  
- ⚙️ Streamlit tabanlı frontend arayüz  
- 🌐 Render üzerinde çalışan FastAPI tabanlı backend (model API servisi)  
- 🐳 Docker destekli frontend mimarisi  
- 🌍 Tam Türkçe destekli akıllı değerlendirme süreci  

---

## 🧩 Proje Mimarisi

Proje iki ana bileşenden oluşur:  
**Frontend (Streamlit)** ve **Backend (FastAPI)**.  

> Backend Render ortamında deploy edilmiştir.  
> Frontend, Docker Compose ile lokal olarak çalıştırıldığında Render’daki backend’e bağlanır.

---

``` markdown
📁 kariyer_mentoru_ai/
│
├── .env
├── .gitignore
├── docker-compose.yml
├── README.md
│
├── backend/ # Render ortamına deploy edilen API
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
└── frontend/ # Lokal veya Docker üzerinden çalışan Streamlit arayüzü
    ├── main.py
    ├── Dockerfile
    └── requirements.txt

```

---

## ⚙️ Ortam Değişkenleri

Kök dizindeki `.env` dosyasında şu bilgileri tanımlayın:

``` bash
BACKEND_URL=https://your-render-backend.onrender.com
MODEL_PROVIDER_API_KEY=your_api_key_here
```

> Bu sayede frontend, Render’daki backend’e otomatik olarak bağlanır.

---
 
## 🐳 Docker Compose ile Çalıştırma

Backend zaten Render üzerinde aktif olduğundan, sadece frontend’i Docker üzerinden başlatmanız yeterlidir:

``` bash
docker compose up --build
```

Komut tamamlandığında Streamlit arayüzü şu adreste çalışacaktır:
👉 http://localhost:8501

---

## 🌐 Servis Erişimleri

| Servis | Adres |
|--------|-------|
| **Frontend (Streamlit)** | [http://localhost:8501](http://localhost:8501) |
| **Backend (Render)** | [https://your-render-backend.onrender.com](https://your-render-backend.onrender.com) |
| **Backend Docs (Swagger UI)** | [https://your-render-backend.onrender.com/docs](https://your-render-backend.onrender.com/docs) |

---

## 🧠 Model Entegrasyonu

Backend, `app.py` içinde yapılandırılmış LLM API’sine bağlanarak kullanıcı girişlerini işler.
Kullanılan model: **Qwen3, DeepSeek-R1, veya Llama4-Maverick-Instruct** gibi gelişmiş açık kaynak modellerden biri olabilir.

Model seçimi `.env` dosyasındaki yapılandırmaya göre değiştirilebilir.

---

## 🧪 Lokal Geliştirme Modu
Backend’i Lokal Çalıştırma (Render’a deploy öncesi test için)

``` bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```
Frontend’i Lokal Çalıştırma

``` bash
cd frontend
pip install -r requirements.txt
streamlit run main.py
```

---

## ☁️ Render Üzerinde Backend Deploy Adımları

1. Render.com hesabınıza giriş yapın.
2. Yeni bir Web Service oluşturun.
3. Kaynak olarak backend/ klasörünü içeren GitHub repo’sunu seçin.
4. Environment: Docker
5. Start Command:
    ``` bash
    sh -c "uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000}"
    ```

6. Deploy tamamlandığında size bir https://<app-name>.onrender.com URL’si verilir.
7. Bu URL’yi `.env` dosyasındaki BACKEND_URL değerine yazın.

---

## 🧱 Kullanılan Teknolojiler

* Python 3.13+
* FastAPI – Backend API servisi
* Streamlit – Kullanıcı arayüzü
* Docker – Frontend konteynerizasyonu
* Render – Backend deploy platformu
* Fireworks / HuggingFace / Together API – LLM sağlayıcı entegrasyonları
* LangChain – PDF yükleme ve metin işleme desteği

---

## 🏁 Katkı ve Geliştirme

Katkıda bulunmak için yeni bir branch oluşturun ve pull request gönderin.
Yeni model veya analiz çıktısı eklemek isterseniz `backend/app.py` içindeki generate_feedback() fonksiyonunu düzenleyebilirsiniz.

---

## 🎬 Canlı Demo

Projeyi Deneyin:
* 👉 [Demo](https://kariyer-mentoru-ai.streamlit.app/)

---


