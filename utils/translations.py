"""
Translation Manager Module
Handles all text translations for multilingual support
"""

TRANSLATIONS = {
    "English": {
        # Page
        "page_title": "Hajj Chatbot",
        "main_title": "Hajj Data Intelligence",
        "subtitle": "Ask anything about Hajj companies worldwide • AI-powered • Real-time data",
        
        # Assistant
        "assistant_title": "🕋 Hajj Assistant",
        "assistant_subtitle": "Your AI-powered guide",
        
        # Sidebar
        "language_title": "🌐 Language",
        "stats_title": "📊 Live Statistics",
        "examples_title": "💡 Quick Examples",
        "clear_chat": "🧹 Clear Chat History",
        "features_title": "ℹ️ Features",
        
        # Mode Navigation (NEW)
        "mode_title": "🔀 Mode",
        "mode_chatbot": "Chatbot",
        "mode_voicebot": "Voicebot",
        "voicebot_unavailable": "Voice assistant page not available",
        
        # Stats
        "total_agencies": "Total Agencies",
        "authorized": "Authorized",
        "countries": "Countries",
        "cities": "Cities",
        
        # Examples
        "ex_all_auth": "🔍 All authorized companies",
        "ex_all_auth_q": "Show me all authorized Hajj companies",
        "ex_saudi": "🇸🇦 Companies in Saudi Arabia",
        "ex_saudi_q": "List companies in Saudi Arabia",
        "ex_by_country": "📊 Agencies by country",
        "ex_by_country_q": "How many agencies are in each country?",
        "ex_emails": "📧 Companies with emails",
        "ex_emails_q": "Find companies with email addresses",
        
        # Features
        "feat_ai": "AI-Powered Search",
        "feat_ai_desc": "Natural language queries",
        "feat_multilingual": "Multilingual",
        "feat_multilingual_desc": "Arabic & English support",
        "feat_viz": "Data Visualization",
        "feat_viz_desc": "Interactive tables",
        "feat_secure": "Secure",
        "feat_secure_desc": "SQL injection protection",
        
        # Messages
        "welcome_msg": "Welcome! 👋\n\nI'm your Hajj Data Assistant. Ask me anything about Hajj companies, locations, or authorization status!",
        "input_placeholder": "Ask your question here... 💬",
        "thinking": "🤔 Analyzing your question...",
        "searching": "🔍 Searching database...",
        "found_results": "✅ Found {count} results",
        "results_badge": "{count} Results",
        "authorized_badge": "{count} Authorized",
        "download_results": "Download Results",
        
        # Responses
        "greeting": "Hello! 👋\n\nI'm doing great, thank you! I'm here to help you find information about Hajj companies. What would you like to know?",
        "no_results": "No results found. Try rephrasing the question or broadening the search.",
        "sql_error": "A database error occurred. Try rephrasing your question.",
        "general_error": "Sorry, I encountered an error processing your request.",
        "hint_rephrase": "💡 Try rephrasing your question or use different keywords",
        
        # Voice
        "voice_assistant": "Go to Voice Assistant",
        "voice_not_available": "Voice assistant page not found",
        
        # Validation
        "input_empty": "Please enter a question",
        "input_too_long": "Question is too long (max 500 characters)",
        "input_invalid": "Invalid characters detected in your question",

        # Quick Actions
        "find_authorized": "Find Authorized Agencies",
        "show_stats": "Show Statistics",
        "find_by_country": "Search by Country",
        "general_help": "General Help",
        
       # Voice Bot Page - Enhanced Naming
"voice_page_title": "Hajj Voice Verification Assistant",
"voice_main_title": "Hajj Guardian Voice Assistant",
"voice_subtitle": "Your trusted companion for verifying authorized Hajj agencies and protecting pilgrims",
"voice_return_button": "Back to Chat",
"voice_recording": "Listening to your voice...",
"voice_press_to_speak": "Tap to Ask a Question",
"voice_speaking": "Assistant Responding...",
"voice_status_ready": "Ready",
"voice_status_processing": "Understanding your request...",
"voice_status_listening": "Listening",
"voice_status_completed": "Response Complete",
"voice_status_speaking": "Speaking",
"voice_status_analyzing": "Processing your query...",
"voice_status_error": "Please Try Again",

"voice_transcript_title": "Your Question",
"voice_response_title": "Guardian's Response",
"voice_speak_now": "Ask me anything about Hajj agencies...",
"voice_response_placeholder": "Your answer will appear here...",
"voice_key_points": "Important Information",
"voice_suggested_actions": "Recommended Next Steps",
"voice_verification_steps": "How to Verify",
"voice_no_speech": "I couldn't hear you clearly",
"voice_try_again": "Please speak clearly and try again",
"voice_error_occurred": "Something went wrong. Let's try that again.",
"voice_could_not_understand": "I couldn't understand that. Could you rephrase?",
"voice_error_processing": "I'm having trouble processing that request",

# Additional helpful labels
"voice_clear_memory": " + Start New Conversation",
"voice_stop_speaking": "Stop",
"voice_memory_messages": "messages",
"voice_session_duration": "Session time",
    },
    
    "العربية": {
        # Page
        "page_title": "روبوت الحج",
        "main_title": "معلومات بيانات الحج الذكية",
        "subtitle": "اسأل عن شركات الحج حول العالم • مدعوم بالذكاء الاصطناعي • بيانات فورية",
        
        # Assistant
        "assistant_title": "🕋 مساعد الحج",
        "assistant_subtitle": "دليلك الذكي المدعوم بالذكاء الاصطناعي",
        
        # Sidebar
        "language_title": "🌐 اللغة",
        "stats_title": "📊 الإحصائيات المباشرة",
        "examples_title": "💡 أمثلة سريعة",
        "clear_chat": "🧹 مسح سجل المحادثة",
        "features_title": "ℹ️ المميزات",
        
        # Mode Navigation (NEW)
        "mode_title": "🔀 الوضع",
        "mode_chatbot": "المحادثة",
        "mode_voicebot": "المساعد الصوتي",
        "voicebot_unavailable": "صفحة المساعد الصوتي غير متاحة",
        
        # Stats
        "total_agencies": "إجمالي الشركات",
        "authorized": "المعتمدة",
        "countries": "الدول",
        "cities": "المدن",
        
        # Examples
        "ex_all_auth": "🔍 جميع الشركات المعتمدة",
        "ex_all_auth_q": "أظهر لي جميع شركات الحج المعتمدة",
        "ex_saudi": "🇸🇦 شركات في السعودية",
        "ex_saudi_q": "اعرض الشركات في المملكة العربية السعودية",
        "ex_by_country": "📊 الشركات حسب الدولة",
        "ex_by_country_q": "كم عدد الشركات في كل دولة؟",
        "ex_emails": "📧 شركات لديها بريد إلكتروني",
        "ex_emails_q": "ابحث عن الشركات التي لديها بريد إلكتروني",
        
        # Features
        "feat_ai": "بحث ذكي",
        "feat_ai_desc": "استعلامات باللغة الطبيعية",
        "feat_multilingual": "متعدد اللغات",
        "feat_multilingual_desc": "دعم العربية والإنجليزية",
        "feat_viz": "تصور البيانات",
        "feat_viz_desc": "جداول تفاعلية",
        "feat_secure": "آمن",
        "feat_secure_desc": "حماية من هجمات SQL",
        
        # Messages
        "welcome_msg": "السلام عليكم ورحمة الله وبركاته! 🌙\n\nأهلاً بك في مساعد معلومات الحج الذكي. كيف يمكنني مساعدتك اليوم؟",
        "input_placeholder": "اكتب سؤالك هنا... 💬",
        "thinking": "🤔 جارٍ تحليل سؤالك...",
        "searching": "🔍 جارٍ البحث في قاعدة البيانات...",
        "found_results": "✅ تم العثور على {count} نتيجة",
        "results_badge": "{count} نتيجة",
        "authorized_badge": "{count} معتمدة",
        "download_results": "تنزيل النتائج",
        
        # Responses
        "greeting": "وعليكم السلام ورحمة الله وبركاته! 🌙\n\nالحمد لله، أنا بخير! أنا هنا لمساعدتك في العثور على معلومات شركات الحج. كيف يمكنني مساعدتك؟",
        "no_results": "لم يتم العثور على نتائج. حاول إعادة صياغة السؤال أو توسيع نطاق البحث.",
        "sql_error": "حدث خطأ في قاعدة البيانات. حاول إعادة صياغة سؤالك.",
        "general_error": "عذراً، واجهت مشكلة في معالجة طلبك.",
        "hint_rephrase": "💡 حاول إعادة صياغة سؤالك أو استخدم كلمات مفتاحية مختلفة",
        
        # Voice
        "voice_assistant": "انتقل إلى المساعد الصوتي",
        "voice_not_available": "صفحة المساعد الصوتي غير موجودة",
        
        # Validation
        "input_empty": "الرجاء إدخال سؤال",
        "input_too_long": "السؤال طويل جداً (الحد الأقصى 500 حرف)",
        "input_invalid": "تم اكتشاف أحرف غير صالحة في سؤالك",

        # Quick Actions
        "find_authorized": "ابحث عن الشركات المعتمدة",
        "show_stats": "عرض الإحصائيات",
        "find_by_country": "البحث حسب الدولة",
        "general_help": "مساعدة عامة",
      # Voice Bot Page - Enhanced Arabic Naming
"voice_page_title": "مساعد الحج الصوتي للتحقق",
"voice_main_title": "مساعد حارس الحج الصوتي",
"voice_subtitle": "رفيقك الموثوق للتحقق من وكالات الحج المعتمدة وحماية الحجاج",
"voice_return_button": "العودة للمحادثة",
"voice_recording": "جاري الاستماع لصوتك...",
"voice_press_to_speak": "اضغط لطرح سؤال",
"voice_speaking": "المساعد يجيب...",
"voice_status_ready": "جاهز للمساعدة",
"voice_status_processing": "جاري فهم طلبك...",
"voice_status_listening": "أستمع بإنتباه",
"voice_status_completed": "اكتمل الرد",
"voice_status_speaking": "المساعد يتحدث",
"voice_status_analyzing": "جاري معالجة استفسارك...",
"voice_status_error": "يرجى المحاولة مرة أخرى",

"voice_transcript_title": "سؤالك",
"voice_response_title": "رد الحارس",
"voice_speak_now": "اسألني أي شيء عن وكالات الحج...",
"voice_response_placeholder": "ستظهر الإجابة هنا...",
"voice_key_points": "معلومات مهمة",
"voice_suggested_actions": "الخطوات الموصى بها",
"voice_verification_steps": "كيفية التحقق",
"voice_no_speech": "لم أتمكن من سماعك بوضوح",
"voice_try_again": "يرجى التحدث بوضوح والمحاولة مرة أخرى",
"voice_error_occurred": "حدث خطأ. دعنا نحاول مرة أخرى",
"voice_could_not_understand": "لم أتمكن من فهم ذلك. هل يمكنك إعادة صياغة السؤال؟",
"voice_error_processing": "أواجه صعوبة في معالجة هذا الطلب",

# Additional helpful labels in Arabic
"voice_clear_memory": "بدء محادثة جديدة",
"voice_stop_speaking": "إيقاف",
"voice_memory_messages": "رسائل",
"voice_session_duration": "مدة الجلسة",
    }
}


def t(key: str, lang: str = "English", **kwargs) -> str:
    """
    Get translation for key in specified language with optional formatting
    
    Args:
        key: Translation key
        lang: Language (English or العربية)
        **kwargs: Format arguments for string interpolation
    
    Returns:
        Translated string
    """
    text = TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, key)
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    
    return text