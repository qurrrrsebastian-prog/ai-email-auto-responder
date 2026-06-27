# Project #17 — AI Email Auto-Responder

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/Gemini%20API-4285F4?style=flat&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/LangChain-1C3C3C?style=flat&logo=chainlink&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat" />
</p>

> AI agent yang membaca email masuk dan otomatis membuat draft balasan profesional dalam Bahasa Indonesia. Tinggal copy-paste kirim.

---

## Demo Langsung

[![Deploy to Streamlit Cloud](https://img.shields.io/badge/Deploy-Streamlit%20Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://share.streamlit.io/deploy?repository=qurrrrsebastian-prog/ai-email-auto-responder)

**Tech Stack:** `Google Gemini API` · `LangChain` · `NLP` · `Streamlit`

---

## Fitur

| Fitur | Status |
|-------|--------|
| Draft reply profesional (ID) | ✅ |
| Tone adjustment (formal/casual) | ✅ |
| Context-aware response | ✅ |
| Copy-paste ready output | ✅ |
| Multiple email types support | ✅ |
| Tema gelap AVA purple | ✅ |

---

## Cara Menjalankan

```bash
git clone https://github.com/qurrrrsebastian-prog/ai-email-auto-responder.git
cd ai-email-auto-responder
pip install -r requirements.txt
$env:GEMINI_API_KEY="your_api_key_here"
streamlit run app.py
```

## Deploy ke Streamlit Cloud (GRATIS)

1. [share.streamlit.io](https://share.streamlit.io) → Login GitHub
2. **New app** → Pilih repo ini
3. Tambahkan secret: `GEMINI_API_KEY`
4. **Deploy**

---

## Struktur Project

```
ai-email-auto-responder/
├── app.py              # Main Streamlit app (12KB)
├── requirements.txt    # Dependencies
├── .streamlit/
│   └── config.toml    # AVA purple branding
├── .gitignore
└── LICENSE            # MIT License
```

---

**Dibuat oleh:** [Avatar Putra Sigit](https://github.com/qurrrrsebastian-prog) · Founder @AVA.Group
