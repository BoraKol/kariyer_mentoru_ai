import streamlit as st # streamlit kullanarak web arayüzü oluşturmak için

from langchain_openai import ChatOpenAI, OpenAIEmbeddings # openai modelleri ve embedding'leri için
from langchain_community.vectorstores import FAISS # vektör tabanlı arama(semantic search) için
from langchain_community.document_loaders import PyPDFLoader # PDF dosyasını metne çevirmek için
from langchain.text_splitter import RecursiveCharacterTextSplitter # Metni küçük parçalara ayırmak için
from dotenv import load_dotenv # .env dosyasından API anahtarını okumak için
import tempfile # geçici dosyalar oluşturmak için
import os # ortam değişkenleriyle çalışmak için

load_dotenv() # ortam değişkenlerini yüklüyoruz

# OpenAI API keyini ortam değişkenlerinden alıp sisteme yüklüyoruz
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY is not found.")

# streamlit Sayfa başlığı ve ikon ayarları
st.set_page_config(page_title="Kariyer Mentor Asistanı", page_icon="🧠")
st.title("🧠 Kariyer Mentor Asistanı")
st.write("Bilgilerinizi girin , başvurmak istediğiniz ilan ve CV'nizin uyumunu Kariyer Mentoru AI değerlendirsin.")

# Geri bildirim fonksiyonu
def generate_feedback(llm, cv_text, job_text):
    prompt = f"""
Sen bir kariyer asistanısın. Aşağıda bir kullanıcının özgeçmişi (CV) ve başvurmak istediği iş ilanı metni verilmiştir.

CV:
{cv_text}

İş İlanı:
{job_text}

Lütfen aşağıdaki soruları yanıtla:
1. Kullanıcının bu ilana uygunluk seviyesi nedir?
2. Eksik veya zayıf görünen beceriler neler?
3. CV'yi bu ilana daha uygun hale getirmek için neler önerirsin?
"""
    return llm.invoke(prompt).content # modelden yanıt alıp sadece içeriğini döndürüyoruz


# Arayüz düzeni - 1'e 2 oranında 2 kolon oluşturalım
col1, col2 = st.columns([1, 2])

# Sol sütun: Girdiler, kullanıcıdan veri alma kısmı 
with col1:
    st.header("📄 Bilgilerinizi Girin") # başlık
    uploaded_file = st.file_uploader("CV'nizi yükleyin (.pdf)", type="pdf") # kullanıcıdan .pdf formatında CV dosyasını yüklemesini istiyoruz
    
    if uploaded_file is not None: # eğer dosya yüklendiyse , kullanıcıya başarılı mesajı göster
        st.success("CV başarıyla işlendi!")
    
    user_input = st.text_area("💼 Başvurmak istediğiniz iş ilanını buraya yapıştırın:", height=100) # kullanıcının başvurmak isteği ilanı metin kutusuna yazması için alan
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

            # Embedding olusturmak icin OPENAI embedding modeli kullaniliyor
            embedding = OpenAIEmbeddings(model="text-embedding-3-large") 
            knowledge_base = FAISS.from_documents(docs, embedding) # parcalanmis dokumanlardan vektor veritabani olustur

            # OPENAI dil modeli
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

            # CV metnini tek bir string haline getiriyoruz
            cv_text = "\n".join([doc.page_content for doc in documents])
            job_text = user_input.strip() # is ilani metni de temizlenip hazir hale getiriliyor

            # Sohbet gecmisi varsa tekrar kullanilmak uzere session_state'e kaydediliyor
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []

            # dil modelinden geri bildirim alma metodu cagiriliyor ve geri bildirim aliniyor
            response = generate_feedback(llm, cv_text, job_text)

            # kullanicinin girisi ve asistanin cevabi sohbet gecmisine ekleniyor
            st.session_state.chat_history.append(("🧑‍💼 CV & İş İlanı Gönderildi", job_text))
            st.session_state.chat_history.append(("🤖 Kariyer Asistanı", response))

    # Sohbet Gecmisi varsa ekranda gosteriyoruz
    if "chat_history" in st.session_state:
        st.subheader("💬 Sohbet Geçmişi") # gecmis basligi
        
        if st.button("🧹 Sohbeti Temizle"): # sohbet gecmisini temizlemek icin bir buton
            st.session_state.chat_history = [] # gecmisi sifirla 
            st.rerun() # sayfayi yeniden yukle 

        for role, message in st.session_state.chat_history: # sohbet gecmisindeki her mesaji sirayla goster 
            with st.chat_message(role.split()[0].lower()): # role gore mesaji goster : kullanici veya AI mesaji 
                st.markdown(message) # mesaji markdown olarak yazdir 
            
           