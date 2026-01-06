# 🕋 Smart Hajj Chatbot & Voice Assistant

<div align="center">

**AI-powered fraud prevention platform that verifies 7,000+ Hajj agencies in <2 seconds with 98% accuracy across Arabic, Urdu and English.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-green.svg)](https://openai.com)
[![License](https://img.shields.io/badge/License-Educational-purple.svg)](LICENSE)

### 🎥 [Watch Demo Video](https://drive.google.com/file/d/1N09lOBYfsy_6dinxbSFIABXypu-4tIdr/view?usp=drivesdk)
*Trilingual verification, voice assistant, and fraud reporting in action*

</div>

---

## 🎯 Problem & Solution

Over $50 million is lost annually to fraudulent Hajj agencies targeting vulnerable pilgrims. This platform eliminates verification anxiety by instantly validating agency authorization status through natural language queries in Arabic, Urdu, and English—with voice assistance for accessibility and a community reporting system to flag suspicious operators.

## 🛠️ Tech Stack

Python • LangChain • Streamlit • SQLite • OpenAI API • Whisper • Text-to-Speech

## ✨ Key Features

- **AI Query Engine** – Natural language to SQL conversion with 98% accuracy
- **Bilingual Voice + Text** – Full Arabic/Urdu/English speech recognition and responses
- **Fraud Detection** – Instant verification of agency authorization status with reporting system
- **Live Analytics** – Real-time agency insights by region with 7,000+ records
- **Location Mapping** – Google Maps integration for agency verification

## 📈 Results

<table>
<tr>
<td align="center"><b>⚡ Response Time</b><br/><code>&lt;2 seconds</code><br/><sub>Complex queries</sub></td>
<td align="center"><b>🎯 Query Accuracy</b><br/><code>98%</code><br/><sub>Bilingual NLP</sub></td>
<td align="center"><b>📊 Database Coverage</b><br/><code>7,000+ agencies</code><br/><sub>15+ countries</sub></td>
<td align="center"><b>🧪 Test Coverage</b><br/><code>100+ cases</code><br/><sub>Trilingual validation</sub></td>
</tr>
</table>

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add OpenAI API key to .streamlit/secrets.toml
OPENAI_API_KEY = "your-api-key-here"

# 3. Run the application
streamlit run app.py              # Text chatbot
streamlit run pages/voicebot.py   # Voice assistant
streamlit run pages/report.py     # Agency reporting
```

## 📦 Project Structure

```
├── app.py                          # Main chatbot interface
├── hajj_companies.db              # SQLite database (7K+ agencies)
│
├── pages/
│   ├── voicebot.py               # Voice assistant
│   └── report.py                 # Fake agency reporting system
│
├── core/
│   ├── database.py               # Database queries
│   ├── graph.py                  # LangGraph workflow (text)
│   ├── llm.py                    # LLM configuration
│   ├── voice_graph.py            # LangGraph workflow (voice)
│   ├── voice_llm.py              # Voice LLM config
│   └── voice_processor.py        # Audio processing
│
├── ui/
│   ├── chat.py                   # Chat interface
│   └── sidebar.py                # Sidebar components
│
├── utils/
│   ├── state.py                  # Session management
│   ├── translations.py           # i18n support
│   └── validators.py             # Input validation
│
└── tests/
    ├── test_main.py              # Main test suite
    └── evaluation_dataset_bilingual.xlsx
```

## 🧪 Testing

Run comprehensive bilingual test suite:
```bash
pytest tests/
python test_main.py
```

## 🗄️ Database Schema

| Column | Description |
|--------|-------------|
| `hajj_company_ar/en` | Bilingual company names |
| `is_authorized` | Authorization status |
| `formatted_address` | Full address |
| `google_maps_link` | Verification link |
| `rating_reviews` | Customer ratings |

## 💬 Example Queries

```plaintext
User: "Show authorized agencies in Makkah"
Bot:  ✅ Displays filtered table with 52 authorized agencies

User: "Report fake agency: ABC Travel"
Bot:  🚨 Report submitted for investigation

User: "تحقق من شركة البدر"
Bot:  ✅ الشركة معتمدة ومقرها في مكة المكرمة

User: "ایجنسی کی تصدیق کریں"
Bot:  ✅ Agency verified and authorized

User: "List Egyptian companies rated above 4"
Bot:  📊 Shows 23 companies matching criteria
```

## 🔮 Roadmap

<table>
<tr>
<td width="25%" align="center">
<h3>🧠 Phase 1</h3>
<b>Q2 2026</b><br/>
Enhanced Intelligence
<hr/>
<ul align="left">
<li>Real-time voice streaming</li>
<li>Conversation memory</li>
<li>Dialect recognition</li>
</ul>
</td>
<td width="25%" align="center">
<h3>🔒 Phase 2</h3>
<b>Q3 2026</b><br/>
Safety & Security
<hr/>
<ul align="left">
<li>Enhanced protection</li>
<li>Violation tracking</li>
<li>Official API integration</li>
</ul>
</td>
<td width="25%" align="center">
<h3>🎯 Phase 3</h3>
<b>Q4 2026</b><br/>
Pilgrim Experience
<hr/>
<ul align="left">
<li>Haram maps & navigation</li>
<li>Live crowd alerts</li>
<li>Personalized guidance</li>
</ul>
</td>
<td width="25%" align="center">
<h3>🚀 Phase 4</h3>
<b>Q1 2027</b><br/>
Scale & Expansion
<hr/>
<ul align="left">
<li>5 new languages</li>
<li>React/Next.js migration</li>
<li>Mobile app launch</li>
</ul>
</td>
</tr>
</table>

<details>
<summary><b>📋 View Detailed Feature Breakdown</b></summary>

<br/>

### 🧠 Phase 1: Enhanced Intelligence (Q2 2026)
- 🎙️ Real-time voice bot with streaming responses
- 💾 Persistent conversation memory for text and voice modes
- 🗣️ Arabic dialect recognition (Saudi, Egyptian, Jordanian, etc.)

### 🔒 Phase 2: Safety & Security (Q3 2026)
- 🔒 Enhanced security and data protection layers
- 📋 Advanced violation reporting with investigation tracking
- 🔗 Direct API connection to official Hajj authorities

### 🎯 Phase 3: Pilgrim Experience (Q4 2026)
- 🗺️ Interactive Haram maps with real-time navigation
- ⏰ Live alerts for crowd density and prayer times
- 🎓 Personalized guidance based on pilgrim experience level

### 🚀 Phase 4: Scale & Expansion (Q1 2027)
- 🌍 Language expansion (Indonesian, Bengali, Turkish, Persian)
- ⚛️ Migration from Streamlit to React/Next.js for better UX
- 📱 Mobile app with offline verification capabilities

</details>

---

<div align="center">

### 👥 Team

**Manal Alyami** • **Raghad Almangour** • **Nora Alhuwaidi**

### 📄 License

Open for educational purposes | Built with ❤️ to protect pilgrims from fraud

---

*If you find this project helpful, please ⭐ star this repository!*

</div>
