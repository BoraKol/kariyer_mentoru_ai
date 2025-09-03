import streamlit as st
import requests 

API_URL = "http://backend:8000/analyze"

st.set_page_config(page_title="Kariyer Mentoru Asistanı" , page_icon="🧠")
st.markdown("## <div style='text-align:center;'> 🧠 Kariyer Mentoru AI </div> " , unsafe_allow_html=True)
st.write("CV'nizi yükleyin ve iş ilanı metnini girin. AI değerlendirsin!")

col1,col2 = st.columns([1,2])

with col1: 
    uploaded_file = st.file_uploader("📄 CV yükle (.pdf)" , type = "pdf")
    user_input = st.text_area("💼 İş ilanı metnini girin" , height=100)
    lang_sel = st.radio("Dil Seçimi: " , ["Türkçe" , "İngilizce"])
    submit = st.button("🚀 Değerlendir")

with col2: 
    if submit: 
        if uploaded_file is None or not user_input.strip():
            st.warning("Lütfen hem CV'nizi yükleyin hem de iş ilanı metnini girin.")
        else:
            files = {"cv": uploaded_file}
            data = {"job_text" : user_input , 
            "lang_sel" : lang_sel}

            with st.spinner("Analiz ediliyor..."): 
                response = requests.post(API_URL , files = files , data = data)

            if response.status_code == 200:
                result = response.json()
                scores = result["scores"]
                analysis = result["analysis"]   

                st.subheader("📊 Kategori Bazlı Değerlendirme")
                for category , score in scores.items():
                    st.write(f"**{category.capitalize()}**: {score}%")
                    st.progress(score/100) 
            
                st.subheader("📝 Detaylı Analiz ve Öneriler")
                st.write(analysis)

                st.download_button("📥 Analizi İndir ", analysis , file_name = "analysis.txt")
            else:
                st.error("API isteği başarısız oldu.")