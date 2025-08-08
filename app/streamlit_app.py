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

load_dotenv()

together_key = os.getenv("TOGETHER_AI_API_KEY")
if together_key is None:
    raise ValueError("TOGETHER_AI_API_KEY environment variable is not set.")

# streamlit Sayfa başlığı ve ikon ayarları
st.set_page_config(page_title="Kariyer Mentoru Asistanı", page_icon="🧠")
st.title("🧠 Kariyer Mentoru AI")
st.write("Bilgilerinizi girin , başvurmak istediğiniz ilan ve CV'nizin uyumunu Kariyer Mentoru AI değerlendirsin.")

# Geri bildirim fonksiyonu
def generate_feedback(llm, cv_text, job_text):
    prompt = f"""
    Sen bir kariyer asistanısın ve kullanıcıların iş başvurularında en doğru yönlendirmeyi sağlamakla görevli profesyonel bir danışmansın. 
    Aşağıda kullanıcıya ait bir özgeçmiş (CV) ile başvurmak istediği iş ilanı metni bulunuyor. 

Lütfen bu bilgiler ışığında aşağıdaki soruları detaylı ve anlaşılır şekilde yanıtla:

CV:
{cv_text}

İş İlanı:
{job_text}

Sorular:
1. Kullanıcının bu ilana uygunluk seviyesi nedir? Uygunluk oranını ve sebeplerini belirt.
2. Kullanıcının sahip olmadığı ya da zayıf olduğu beceriler hangileridir? Bunların neden önemli olduğunu açıkla.
3. CV'nin bu ilana daha uygun hale gelmesi için somut önerilerde bulun; özellikle hangi beceriler, deneyimler veya anahtar kelimeler eklenmeli?
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
                model="mistralai/Mixtral-8x7B-Instruct-v0.1",  # veya birlikte çalıştığın başka bir model
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

        for message in st.session_state.chat_history: # sohbet gecmisindeki her mesaji sirayla goster 
            if(message[0] == "🤖 Kariyer Asistanı"): # burada message yapisi soyle oldugu icin message[0]'a gore filtreledik : message(("ai" , "ai mesaji burada"))
                                                      # message[0] => ai , message[1] şeklinde bir tuple
                st.markdown(f"**{message[0]}**  : \n\n {message[1]}") # mesaji markdown olarak yazdir 
            
           
