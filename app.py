"""
app.py — Deployment Streamlit
Tugas Besar ML — Prediksi Sentimen Review Game Steam
Jalankan dengan:  streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import joblib
from datetime import date

# ----------------------- Load model -----------------------
@st.cache_resource
def load_model():
    model = joblib.load("model/model_steam_sentiment.pkl")
    meta = joblib.load("model/model_meta.pkl")
    return model, meta

model, meta = load_model()
FEATURES = meta["feature_cols"]
LABELS = meta["label_names"]

# ----------------------- Tampilan -----------------------
st.set_page_config(page_title="Prediksi Sentimen Game Steam", page_icon="🎮", layout="centered")
st.title("🎮 Prediksi Sentimen Review Game Steam")
st.caption("Tugas Besar Machine Learning — Klasifikasi 3 tier sentimen review")

st.markdown(
    "Masukkan karakteristik sebuah game, model akan memprediksi "
    "**tingkat sentimen review**-nya: *Mixed/Negatif*, *Positif*, atau *Sangat Positif*."
)

with st.form("input_form"):
    col1, col2 = st.columns(2)

    with col1:
        nama = st.text_input("Nama game", "Contoh Game")
        is_free = st.checkbox("Game gratis (Free)?", value=False)
        orig_price = st.number_input("Harga asli (Rp)", min_value=0, value=200000, step=10000,
                                     disabled=is_free)
        diskon_pct = st.slider("Besar diskon (%)", 0, 100, 0)

    with col2:
        reviews_count = st.number_input("Jumlah review", min_value=0, value=10000, step=1000)
        tahun_rilis = st.number_input("Tahun rilis", min_value=2006, max_value=2026, value=2022)
        kategori = st.selectbox("Kategori Steam",
                                ["topsellers", "mostplayed", "newreleases", "upcomingreleases"])

    submit = st.form_submit_button("🔮 Prediksi Sentimen")

# ----------------------- Prediksi -----------------------
if submit:
    # Susun fitur sesuai urutan saat training
    orig = 0.0 if is_free else float(orig_price)
    disc = orig * (1 - diskon_pct / 100.0)          # harga setelah diskon
    age_days = max((date(2026, 5, 28) - date(int(tahun_rilis), 1, 1)).days, 0)

    row = {
        "orig_price": orig,
        "disc_price": disc,
        "disc_pct": float(diskon_pct),
        "Reviews Count": float(reviews_count),
        "game_age_days": float(age_days),
        "is_free": int(is_free),
        "has_discount": int(diskon_pct > 0),
        "name_len": float(len(nama)),
        "filter_mostplayed": int(kategori == "mostplayed"),
        "filter_newreleases": int(kategori == "newreleases"),
        "filter_topsellers": int(kategori == "topsellers"),
        "filter_upcomingreleases": int(kategori == "upcomingreleases"),
    }
    X = pd.DataFrame([row])[FEATURES]   # pastikan urutan kolom sama

    pred = int(model.predict(X)[0])
    proba = model.predict_proba(X)[0]

    warna = {"Mixed/Negatif": "🔴", "Positif": "🟡", "Sangat Positif": "🟢"}
    hasil = LABELS[pred]
    st.success(f"### {warna.get(hasil,'')} Prediksi: **{hasil}**")

    st.markdown("#### Probabilitas tiap kelas")
    prob_df = pd.DataFrame({"Sentimen": LABELS, "Probabilitas": proba})
    st.bar_chart(prob_df.set_index("Sentimen"))
    st.dataframe(prob_df.style.format({"Probabilitas": "{:.1%}"}), use_container_width=True)

# ----------------------- Sidebar info -----------------------
with st.sidebar:
    st.header("ℹ️ Tentang Model")
    st.write("**Algoritma:** Gradient Boosting (dituning via GridSearchCV)")
    st.write("**Akurasi test:** ~66% | **F1-macro:** ~0.57")
    st.write("**Penanganan imbalance:** SMOTE")
    st.write("**Fitur terpenting:** umur game & jumlah review")
    st.divider()
    st.caption("Catatan: kolom '% positif' sengaja tidak dipakai untuk mencegah data leakage.")
