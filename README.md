# ✉️ AI Email Auto-Responder

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLM-F55036?logo=groq&logoColor=white)

AI agent that reads an incoming business email and drafts a polished, ready-to-send reply in **Bahasa Indonesia** — complete with the right salutation, a body that answers every question, a clear call-to-action, and a professional closing.

Built for service businesses (rope access, glass cleaning, building maintenance, waterproofing) where fast, professional email turnaround wins deals.

---

## ✨ Features

- **Intent & urgency analysis** — classifies intent, urgency (High/Medium/Low), and sentiment before writing a word.
- **Smart drafting** — answers *all* detected key questions and proposes the right CTA (site visit / quotation / meeting).
- **Tone selection** — Profesional, Santai tapi Profesional, Assertive, or Empatik.
- **Context presets** — PT RKARI, AVA.Group, or Generic.
- **One-click copy** — copy the finished draft to clipboard and jump straight to Gmail.

---

## 🛠️ Tech Stack

| Layer | Tool |
|-------|------|
| UI | Streamlit (wide layout) |
| LLM | Groq (`llama-3.3-70b-versatile`) |
| Language | Python 3.14 |

---

## 🚀 Run It

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Groq API key (PowerShell)
$env:GROQ_API_KEY = "gsk_your_key_here"

# 3. Launch
streamlit run app.py
```

> No API key in your environment? Paste it directly into the sidebar.

---

## 🎬 Demo Example

**Input (email masuk):**
```
Dari: gm@megatower.co.id
Subjek: Pembersihan kaca gedung 18 lantai

Halo, kami butuh pembersihan kaca eksterior gedung 18 lantai di SCBD.
Berapa estimasi biaya dan kapan tim bisa survei lokasi?
```

**Output (draft balasan):**
```
Yth. Bapak/Ibu di Mega Tower,

Terima kasih atas ketertarikan Anda pada layanan pembersihan kaca eksterior kami...
Untuk gedung 18 lantai, estimasi awal berada pada rentang Rp 60-100jt tergantung
hasil survei. Kami dapat menjadwalkan survei lokasi minggu ini...

Hormat kami,
Avatar Putra Sigit
```

---

## 📊 Key Insights

1. **~6 seconds** from paste to finished draft — vs. ~8 minutes writing manually (≈98% time saved).
2. **5 analysis fields** (intent, urgency, sentiment, key questions, CTA) extracted before drafting, so no question goes unanswered.
3. **4 tone profiles × 3 context presets = 12 reply styles** from a single email, no prompt engineering required.

---

## 👤 Author

**Avatar Putra Sigit**
- GitHub: [qurrrrsebastian-prog](https://github.com/qurrrrsebastian-prog)
- LinkedIn: [avatarputrasigit](https://www.linkedin.com/in/avatarputrasigit)
