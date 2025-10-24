# 🕋 Smart Hajj Voice Bot

## 🎯 Overview
**Smart Hajj Voice Bot** is an AI-powered assistant designed to help pilgrims **verify licensed Hajj agencies** and **prevent fraud or scams** during the booking process.  
The system supports **multilingual voice interaction** (Arabic & English) and connects to trusted data sources to ensure accuracy.

## ⚙️ Key Features
- 🎙️ **Voice Interaction** — Speech-to-text and text-to-speech for natural dialogue.  
- 🌐 **Automatic Language Detection** — Supports both Arabic and English seamlessly.  
- ✅ **Agency Verification** — Matches input against official Ministry of Hajj & Umrah data.  
- ⚠️ **Fraud Detection** — Flags unlisted or potentially fake agencies.  
- 💬 **Streamlit Interface** — Simple web-based app for demo and testing.

## 🧠 Tech Stack
- Python · Streamlit · SQLite/MySQL  
- OpenAI Whisper (Speech-to-Text)  
- Google TTS or ElevenLabs (Text-to-Speech)  
- FuzzyWuzzy / RapidFuzz for name matching  
- Ministry of Hajj & Umrah Open Data (API / Scraped)  

## 🗂️ System Workflow
1. User speaks or types an agency name.  
2. The system detects the language automatically.  
3. Voice is transcribed to text → verified in database.  
4. The model responds with voice and text results.  
5. Unverified agencies are flagged as potentially fraudulent.

