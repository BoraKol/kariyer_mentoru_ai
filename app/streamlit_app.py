import streamlit as st # streamlit kullanarak web arayüzü oluşturmak için

# from langchain_openai import ChatOpenAI, OpenAIEmbeddings # openai modelleri ve embedding'leri için
from langchain_community.vectorstores import FAISS # vektör tabanlı arama(semantic search) için
from langchain_community.document_loaders import PyPDFLoader # PDF dosyasını metne çevirmek için
from langchain.text_splitter import RecursiveCharacterTextSplitter # Metni küçük parçalara ayırmak için
from langchain_community.embeddings import HuggingFaceEmbeddings # huggingface tabanlı embedding modeli
from langchain_together import ChatTogether
from langchain_core.messages import AIMessage , HumanMessage

from dotenv import load_dotenv

import tempfile # geçici dosyalar oluşturmak için
import os 

import json

load_dotenv()

together_key = os.getenv("TOGETHER_AI_API_KEY")
if together_key is None:
    raise ValueError("TOGETHER_AI_API_KEY environment variable is not set.")

# streamlit Sayfa başlığı ve ikon ayarları
st.set_page_config(page_title="Kariyer Mentoru Asistanı", page_icon="🧠")
st.markdown("## <div style='text-align:center;'> 🧠 Kariyer Mentoru AI </div>" , unsafe_allow_html= True) ## unsafe_allow_html ile html tag'leri aktif oluyor
st.write("Bilgilerinizi girin , başvurmak istediğiniz ilan ve CV'nizin uyumunu Kariyer Mentoru AI değerlendirsin.")

# Geri bildirim fonksiyonu
def generate_feedback(llm, cv_text, job_text , lang_sel):
    prompt = f"""
Sen bir kariyer asistanısın.Sadece seninle paylaşılan CV ve ilan metnini göz önünde bulundurarak {lang_sel} dilinde kullanıcıya cevap verirsin. 
Aşağıda bir kullanıcının özgeçmişi (CV) ve başvurmak istediği iş ilanı metni verilmiştir. 

CV:
{cv_text}

İş İlanı:
{job_text}

Dil Seçimi: 
{lang_sel}

Cevabı şu iki bölüm halinde ver:
[1] JSON formatında skorlar(Sadece bu JSON'u döndür):
{{
    "technical_skills: yüzde(0-100),
    "communication_skills": yüzde(0-100),
    "problem_solving": yüzde(0-100),
    teamwork": yüzde(0-100),
    "adaptability": yüzde(0-100), 
    "overall_fit": yüzde(0-100) 
}}

[2] Açıklayıcı analiz ({lang_sel} dilinde, emoji kullanarak): 
- Kullanıcının güçlü yönleri(✅ ile sırala)
- Eksik yönleri(⚠️ ile sırala)
- Cv'yi bu ilana daha uygun hale getirmek için öneriler(💡 ile sırala)
- Genel değerlendirme ve öneriler(📊 ile sırala)
"""
    response =  llm.invoke([HumanMessage(content = prompt)]) 
    return response.content # modelden yanıt alıp sadece içeriğini döndürüyoruz


# Arayüz düzeni - 1'e 2 oranında 2 kolon oluşturalım
col1, col2 = st.columns([1, 2])

# Sol sütun: Girdiler, kullanıcıdan veri alma kısmı 
with col1:
    # st.header("📄 Bilgilerinizi Girin") # başlık
    uploaded_file = st.file_uploader("CV'nizi yükleyin (.pdf)", type="pdf") # kullanıcıdan .pdf formatında CV dosyasını yüklemesini istiyoruz
    
    if uploaded_file is not None: # eğer dosya yüklendiyse , kullanıcıya başarılı mesajı göster
        st.success("CV başarıyla işlendi!")
    
    user_input = st.text_area("💼 Başvurmak istediğiniz iş ilanını buraya yapıştırın:", height=100) # kullanıcının başvurmak isteği ilanı metin kutusuna yazması için alan
    lang_sel = st.radio("Dil Seçimi:" , ['Türkçe' ,'İngilizce']) ## modelin dil desteginden oturu diger diller kaldirildi.

    # if lang_sel == "Türkçe":
    #     st.success("Türkçe")
    # else : 
    #     st.success("İngilizce")

    submit = st.button("🚀 Değerlendir") # değerlendirme butonu

# Sağ sütun: Sonuçların , ai asistanının cevabının olduğu sutun ve sohbet gecmisi
with col2:
    if submit: # eger degerlendir butonuna basildiysa
        if uploaded_file is None or not user_input.strip(): # dosya yuklenmemis veya is ilani metni bos birakilmissa uyari goster
            st.warning("Lütfen hem CV’nizi yükleyin hem de iş ilanı metnini girin.")
        else:
            # PDF dosyasını gecici olarak kaydet
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read()) # Dosya içeriğini yaz.
                tmp_path = tmp.name # Geçici dosya yolunu al 

            # PyPDFLoader ile PDF icerigini okuyup metne donustur
            loader = PyPDFLoader(tmp_path)
            documents = loader.load() # belge listesi olarak doner(sayfa sayfa)

            # Metni kucuk parçalara ayırmak icin TextSplitter kullanıyoruz
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            docs = splitter.split_documents(documents)

            # Embedding olusturmak icin Huggingface'den open source bir embedding modeli kullaniliyor
            embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2") 
            knowledge_base = FAISS.from_documents(docs, embedding) # parcalanmis dokumanlardan vektor veritabani olustur

            # Together dil modeli
            llm = ChatTogether(
                model="google/gemma-2-27b-it",  # veya birlikte çalıştığın başka bir model
                temperature=0.2,
                max_tokens=1024,
                together_api_key=together_key
            )

            # CV metnini tek bir string haline getiriyoruz
            cv_text = "\n".join([doc.page_content for doc in documents])
            job_text = user_input.strip() # is ilani metni de temizlenip hazir hale getiriliyor

            # Sohbet gecmisi varsa tekrar kullanilmak uzere session_state'e kaydediliyor
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []

            # dil modelinden geri bildirim alma metodu cagiriliyor ve geri bildirim aliniyor
            response = generate_feedback(llm, cv_text, job_text,lang_sel)

            ## response içerisindeki JSON Kısmını ayıkla(parse et)
            json_start = response.find("{")
            json_end = response.find("}") + 1
            scores = json.loads(response[json_start:json_end])

            ## metin analizi kısmını ayarlayalım 
            analysis = response[json_end:]

            ## Progress bar ile skorları gosterelim
            st.subheader("📊 Kategori Bazlı Değerlendirme")
            for category , score in scores.items():
                st.write(f"**{category.capitalize()}**: {score}%")
                st.progress(score/100)
            
            st.subheader("📝 Detaylı Analiz")
            st.write(analysis) 

            # kullanicinin girisi ve asistanin cevabi sohbet gecmisine ekleniyor
            st.session_state.chat_history.append(("🧑‍💼 CV & İş İlanı Gönderildi", job_text))
            st.session_state.chat_history.append(("🤖 AI Assistant", response))

    # Sohbet Gecmisi varsa ekranda gosteriyoruz
    if "chat_history" in st.session_state:
        # st.subheader("💬 Sohbet Geçmişi") # gecmis basligi
        
        if st.button("🧹 Sohbeti Temizle"): # sohbet gecmisini temizlemek icin bir buton
            st.session_state.chat_history = [] # gecmisi sifirla 
            st.rerun() # sayfayi yeniden yukle 

        # for message in st.session_state.chat_history: # sohbet gecmisindeki her mesaji sirayla goster 
        #     if(message[0] == "🤖 AI Assistant"): # burada message yapisi soyle oldugu icin message[0]'a gore filtreledik : message(("ai" , "ai mesaji burada"))
        #                                               # message[0] => ai , message[1] şeklinde bir tuple
        #         st.markdown(f"**{message[0]}**  : \n\n {message[1]}") # mesaji markdown olarak yazdir 
            
           
