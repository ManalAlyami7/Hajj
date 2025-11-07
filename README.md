# 🕋 Smart Hajj Chatbot & Voice Assistant

An **AI-powered multilingual platform** combining a **data chatbot** and a **voice assistant** to help pilgrims verify and explore Hajj agency data — in both **Arabic** and **English**.

---

## 🌍 Features

### 💬 Chatbot (`app.py`)
- 🧠 **AI Query Engine** – Converts natural language into optimized SQL.  
- 🌐 **Multilingual Recognition** – Supports Arabic and English text.  
- 🕋 **Smart Verification** – Detects verification requests and asks for more details if needed.  
- 📈 **Database Insights** – Provides live analytics and statistics.  
- 🗺️ **Google Maps Integration** – Shows agency locations.  

### 🎙️ Voice Assistant (`voicebot.py`)
- 🗣️ **Voice Interaction** – Speak to the bot instead of typing.  
- 🌐 **Multilingual Recognition** – Supports Arabic and English speech.  
- 🔊 **Text-to-Speech Responses** – The assistant replies using natural AI-generated voice.  
- 🤖 **Smart Context Handling** – Analyzes user voice queries and provides matching responses.  
- 🕋 **Fraud Prevention Focus** – Can verify agency legitimacy by name or location.  
- ⚡ **Streamlit Interface** – Clean, responsive voice interface with a record button and audio playback.

---

## ⚙️ Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Add your API keys**
   Create a `.streamlit/secrets.toml` file:
   ```toml
   OPENAI_API_KEY = "your-openai-api-key"
   GOOGLE_MAPS_API_KEY = "your-google-maps-api-key"  # optional
   ```

3. **Add your database**
   Make sure `hajj_companies.db` is in the same directory.

4. **Run the chatbot**
   ```bash
   streamlit run app.py
   ```

5. **Run the voice bot**
   ```bash
   streamlit run voicebot.py
   ```

---

## 🗄️ Database Schema

The SQLite database must contain a table named **`agencies`** with these columns:

| Column | Description |
|--------|--------------|
| `hajj_company_ar` | Arabic company name |
| `hajj_company_en` | English company name |
| `formatted_address` | Full address |
| `city` | City name |
| `country` | Country |
| `email` | Contact email |
| `contact_Info` | Additional contact details |
| `rating_reviews` | Reviews or ratings |
| `is_authorized` | 'Yes' or 'No' |
| `google_maps_link` | Link of Google maps |
| `link_valid` | 'True' or 'False' |


---

## 🧠 Example Interactions

### 💬 Text Chatbot
| Query | Bot Response |
|--------|---------------|
| “Show all authorized agencies in Makkah” | Displays a table of authorized agencies. |
| “List companies in Egypt” | Shows all Egyptian agencies. |
| “I want to verify an agency” | 🕋 “Please provide the agency name or any details to help me verify it.” |

### 🎙️ Voice Bot
| Spoken Command | Voice Response |
|----------------|----------------|
| “Check if Royal City Travel is authorized” | “Royal City Travel is authorized and located in Cairo, Egypt.” |
| “أرني الشركات في مكة” | “يوجد 52 شركة معتمدة في مكة المكرمة.” |
| “تحقق من وكالة جابال عمر جميرا” | “وكالة جابال عمر جميرا معتمدة وتقع في مكة المكرمة.” |

---

## 🗺️ Google Maps Integration

If `formatted_address` exists and you add your Google Maps API key,  
the app can:
- Display clickable Google Maps links for agencies  
- Plot agency locations directly on an interactive map  

---

## 📦 Project Structure

```
├── app.py                    # Main chatbot (text-based)
├── voicebot.py              # Voice-enabled assistant
├── hajj_companies.db         # SQLite database
├── requirements.txt          # Dependencies
├── .streamlit/
│   └── secrets.toml          # API keys
└── README.md                 # Documentation
```

---

## 📜 License

This project is open for educational and research purposes.  
Developed with ❤️ to protect pilgrims from fraud and enhance trust in authorized Hajj services.
