"""
Translation Manager Module - Enhanced
Handles all text translations for multilingual support
Includes: English, Arabic, and Urdu
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
         "footer_chat":"AI Technology",
        
        # Sidebar
        "language_title": "🌐 Language",
        "stats_title": "📊 Live Statistics",
        "footer_title_voice": "Hajj Voice Assistant",
        "footer_tech": "AI Speech Technology",
        "footer_powered": "Powered by",

        "examples_title": "💡 Quick Examples",
        "clear_chat": "🧹 Clear Chat History",
        "features_title": "ℹ️ Features",
        "language_en": "English",
        "language_ar": "Arabic",
        "language_ur":"Urdu",
        
        # Mode Navigation
        "mode_title": "🔀 Mode",
        "mode_chatbot": "Chatbot",
        "mode_voicebot": "Voicebot",
        "voicebot_unavailable": "Voice assistant page not available",
        "voice_status_interrupted": "interrupted",
        
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
        "accessibility_title": "Accessibility",
        
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
        "font_normal": "Normal", 
                "feat_multilingual_desc": "Supports Arabic, English, and Urdu for better accessibility.",
        "language_switched": "Language switched to {lang}",
        "accessibility_title": "♿ Accessibility",
        "accessibility_desc": "Adjust font size or contrast for better visibility.",
        "font_size_label": "Font Size",
        "font_normal": "Normal",
        "font_large": "Large",
        "font_extra_large": "Extra Large",
        "font_size_updated": "Font size changed to {size}",
        "contrast_label": "Enable High Contrast Mode",
        "contrast_help": "Improves visibility for users with low vision.",
        "contrast_updated": "High contrast mode updated.",
        "memory_status_title": "🧠 Memory Status",
        "memory_status_desc": "Review your current session progress.",
        "voice_memory_messages": "Messages",
        "voice_session_duration": "Duration",
        "voice_clear_memory": "Clear Memory",
        "memory_cleared": "Memory cleared successfully!",
        "examples_title": "💡 Example Questions",
        "examples_caption": "Try one of these to get started quickly:",
        "sample_questions": [
            "What are the Hajj requirements?",
            "Find affordable packages",
            "When should I book?",
            "Tell me about Mina"
        ],
        "nav_title": "🏠 Navigation",
        "nav_caption": "Return to the main chat interface.",
        "voice_return_button": "Return",

        
        # Voice Bot Page
        "voice_page_title": "Hajj Voice Verification Assistant",
        "voice_main_title": "Hajj Voice Assistant",
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
        "voice_response_title": "Assistant Response",
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
          "feat_multilingual_desc": "يدعم العربية والإنجليزية والأردية لتحسين الوصول.",
    "language_switched": "تم تغيير اللغة إلى {lang}",
    "accessibility_title": "♿ سهولة الوصول",
    "accessibility_desc": "قم بتعديل حجم الخط أو التباين لتحسين الرؤية.",
    "font_size_label": "حجم الخط",
    "font_normal": "عادي",
    "font_large": "كبير",
    "font_extra_large": "كبير جدًا",
    "font_size_updated": "تم تغيير حجم الخط إلى {size}",
    "contrast_label": "تفعيل وضع التباين العالي",
    "contrast_help": "يحسن الرؤية للمستخدمين ضعيفي النظر.",
    "contrast_updated": "تم تحديث وضع التباين العالي.",
    "memory_status_title": "🧠 حالة الذاكرة",
    "memory_status_desc": "راجع تقدم الجلسة الحالية.",
    "voice_memory_messages": "الرسائل",
    "footer_title_voice": "مساعد الحج الصوتي",
        "footer_powered": "مدعوم بواسطة",
        "footer_tech": "تقنية الذكاء الاصطناعي الصوتية",
    "voice_session_duration": "المدة",
    "voice_clear_memory": "مسح الذاكرة",
    "memory_cleared": "تم مسح الذاكرة بنجاح!",
    "examples_title": "💡 أسئلة نموذجية",
    "examples_caption": "جرّب أحد هذه الأسئلة للبدء بسرعة:",
    "sample_questions": [
        "ما هي متطلبات الحج؟",
        "ابحث عن باقات بأسعار معقولة",
        "متى يجب أن أحجز؟",
        "أخبرني عن منى"
    ],
    "nav_title": "🏠 التنقل",
    "nav_caption": "العودة إلى واجهة الدردشة الرئيسية.",
    "voice_return_button": "عودة",
        
        # Sidebar
        "voice_status_interrupted": "تم الإيقاف",

        "language_title": "🌐 اللغة",
        "stats_title": "📊 الإحصائيات المباشرة",
        "examples_title": "💡 أمثلة سريعة",
        "clear_chat": "🧹 مسح سجل المحادثة",
        "features_title": "ℹ️ المميزات",
        "language_en": "الإنجليزية",
        "language_ar": "العربية",
        "language_ur":"أردو",
        
        # Mode Navigation
        "mode_title": "🔀 الوضع",
        "mode_chatbot": "المحادثة",
        "mode_voicebot": "المساعد الصوتي",
        "voicebot_unavailable": "صفحة المساعد الصوتي غير متاحة",
        
        # Stats
        "total_agencies": "إجمالي الشركات",
        "authorized": "المعتمدة",
        "countries": "الدول",
        "footer_chat": "تقنية الذكاء الاصطناعي",

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
        "feat_viz": "تصور البيانات",
        "feat_viz_desc": "جداول تفاعلية",
        "feat_secure": "آمن",
        "feat_secure_desc": "حماية من هجمات SQL",
        "font_normal": "عادي",
        
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
        
        # Voice Bot Page
        "voice_page_title": "مساعد الحج الصوتي للتحقق",
        "voice_main_title": "مساعد الحج الصوتي",
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
        "voice_response_title": "رد المساعد",
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
        "voice_stop_speaking": "إيقاف",
        "voice_memory_messages": "رسائل",
        "voice_session_duration": "مدة الجلسة",
    },
    
    "اردو": {
        # Page
        "page_title": "حج چیٹ بوٹ",
        "main_title": "حج ڈیٹا انٹیلیجنس",
        "subtitle": "دنیا بھر کی حج کمپنیوں کے بارے میں کچھ بھی پوچھیں • AI سے چلنے والا • حقیقی وقت کا ڈیٹا",
        
        # Assistant
        "assistant_title": "🕋 حج معاون",
        "assistant_subtitle": "آپ کا AI سے چلنے والا رہنما",
        
        # Sidebar
        "language_title": "🌐 زبان",
        "stats_title": "📊 براہ راست شماریات",
        "examples_title": "💡 فوری مثالیں",
        "clear_chat": "🧹 چیٹ کی تاریخ صاف کریں",
        "features_title": "ℹ️ خصوصیات",
        "language_en": "انگریزی",
        "language_ar": "عربی",
        "language_ur": "اردو",
        "font_normal": "عام",
        "feat_multilingual_desc": "بہتر رسائی کے لیے عربی، انگریزی اور اردو کی حمایت کرتا ہے۔",
    "language_switched": "زبان تبدیل کر دی گئی: {lang}",
    "accessibility_title": "♿ رسائی",
    "accessibility_desc": "بہتر نظر کے لیے فونٹ کا سائز یا فرق ترتیب دیں۔",
    "font_size_label": "فونٹ کا سائز",
    "font_normal": "عام",
    "font_large": "بڑا",
    "font_extra_large": "زبردست بڑا",
    "font_size_updated": "فونٹ کا سائز تبدیل کر دیا گیا: {size}",
    "contrast_label": "ہائی کانٹراسٹ موڈ فعال کریں",
    "contrast_help": "کمزور نظر والے صارفین کے لیے نظر بہتر بناتا ہے۔",
    "contrast_updated": "ہائی کانٹراسٹ موڈ اپ ڈیٹ ہو گیا۔",
    "memory_status_title": "🧠 یادداشت کی حالت",
    "memory_status_desc": "اپنے موجودہ سیشن کی پیش رفت دیکھیں۔",
    "voice_memory_messages": "پیغامات",
    "footer_title_voice": "حج وائس اسسٹنٹ",
        "footer_powered": "کے ذریعے چلنے والا",
        "footer_tech": "اے آئی آواز کی ٹیکنالوجی",
    "voice_session_duration": "دورانیہ",
    "voice_clear_memory": "یادداشت صاف کریں",
    "memory_cleared": "یادداشت کامیابی سے صاف ہو گئی!",
    "examples_title": "💡 مثال کے سوالات",
    "examples_caption": "شروع کرنے کے لیے ان میں سے کوئی ایک آزمائیں:",
    "sample_questions": [
        "حج کی ضروریات کیا ہیں؟",
        "سستے پیکجز تلاش کریں",
        "میں کب بکنگ کروں؟",
        "منا کے بارے میں بتائیں"
    ],
    "nav_title": "🏠 نیویگیشن",
    "nav_caption": "مین چیٹ انٹرفیس پر واپس جائیں۔",
    "voice_return_button": "واپس",
        



        # Mode Navigation
        "mode_title": "🔀 موڈ",
        "mode_chatbot": "چیٹ بوٹ",
        "mode_voicebot": "وائس بوٹ",
        "voicebot_unavailable": "صوتی معاون کا صفحہ دستیاب نہیں ہے",
        
        # Stats
        "total_agencies": "کل ایجنسیاں",
        "authorized": "مجاز",
        "countries": "ممالک",
        "cities": "شہر",
        
        # Examples
        "ex_all_auth": "🔍 تمام مجاز کمپنیاں",
        "ex_all_auth_q": "مجھے تمام مجاز حج کمپنیاں دکھائیں",
        "ex_saudi": "🇸🇦 سعودی عرب میں کمپنیاں",
        "ex_saudi_q": "سعودی عرب میں کمپنیوں کی فہرست بنائیں",
        "ex_by_country": "📊 ملک کے لحاظ سے ایجنسیاں",
        "ex_by_country_q": "ہر ملک میں کتنی ایجنسیاں ہیں؟",
        "ex_emails": "📧 ای میل والی کمپنیاں",
        "ex_emails_q": "ای میل ایڈریس والی کمپنیاں تلاش کریں",
        
        # Features
        "feat_ai": "AI سے چلنے والی تلاش",
        "feat_ai_desc": "قدرتی زبان کے سوالات",
        "feat_multilingual": "کثیر لسانی",
        "feat_viz": "ڈیٹا کی تصویر کشی",
        "feat_viz_desc": "انٹرایکٹو ٹیبلز",
        "feat_secure": "محفوظ",
        "feat_secure_desc": "SQL انجیکشن تحفظ",
        
        # Messages
        "welcome_msg": "خوش آمدید! 👋\n\nمیں آپ کا حج ڈیٹا معاون ہوں۔ حج کمپنیوں، مقامات، یا اجازت کی حیثیت کے بارے میں مجھ سے کچھ بھی پوچھیں!",
        "input_placeholder": "یہاں اپنا سوال پوچھیں... 💬",
        "thinking": "🤔 آپ کے سوال کا تجزیہ کر رہا ہوں...",
        "searching": "🔍 ڈیٹا بیس تلاش کر رہا ہوں...",
        "found_results": "✅ {count} نتائج ملے",
        "results_badge": "{count} نتائج",
        "authorized_badge": "{count} مجاز",
        "download_results": "نتائج ڈاؤن لوڈ کریں",
        
        # Responses
        "greeting": "السلام علیکم! 👋\n\nمیں بہت اچھا ہوں، شکریہ! میں یہاں حج کمپنیوں کے بارے میں معلومات تلاش کرنے میں آپ کی مدد کے لیے ہوں۔ آپ کیا جانا چاہتے ہیں؟",
        "no_results": "کوئی نتائج نہیں ملے۔ سوال کو دوبارہ لکھنے یا تلاش کو وسیع کرنے کی کوشش کریں۔",
        "sql_error": "ڈیٹا بیس میں خرابی پیش آئی۔ اپنا سوال دوبارہ لکھنے کی کوشش کریں۔",
        "general_error": "معذرت، آپ کی درخواست پر کارروائی کرتے وقت مجھے ایک خرابی کا سامنا ہوا۔",
        "hint_rephrase": "💡 اپنے سوال کو دوبارہ لکھنے یا مختلف مطلوبہ الفاظ استعمال کرنے کی کوشش کریں",
        
        # Voice
        "voice_assistant": "صوتی معاون پر جائیں",
        "voice_not_available": "صوتی معاون کا صفحہ نہیں ملا",
        
        # Validation
        "input_empty": "براہ کرم ایک سوال درج کریں",
        "input_too_long": "سوال بہت لمبا ہے (زیادہ سے زیادہ 500 حروف)",
        "input_invalid": "آپ کے سوال میں غلط حروف کا پتہ چلا",

        # Quick Actions
        "find_authorized": "مجاز ایجنسیاں تلاش کریں",
        "show_stats": "شماریات دکھائیں",
        "find_by_country": "ملک کے لحاظ سے تلاش کریں",
        "general_help": "عمومی مدد",
        
        # Voice Bot Page - Urdu
        "voice_page_title": "حج صوتی تصدیق معاون",
        "voice_main_title": "حج صوتی معاون",
        "voice_subtitle": "مجاز حج ایجنسیوں کی تصدیق اور حجاج کی حفاظت کے لیے آپ کا قابل اعتماد ساتھی",
        "voice_return_button": "چیٹ پر واپس جائیں",
        "voice_recording": "آپ کی آواز سن رہا ہوں...",
        "voice_press_to_speak": "سوال پوچھنے کے لیے ٹیپ کریں",
        "voice_speaking": "معاون جواب دے رہا ہے...",
        "voice_status_ready": "تیار",
        "voice_status_processing": "آپ کی درخواست سمجھ رہا ہوں...",
        "voice_status_listening": "سن رہا ہوں",
        "voice_status_completed": "جواب مکمل",
        "voice_status_speaking": "بول رہا ہوں",
        "voice_status_analyzing": "آپ کے سوال پر کارروائی کر رہا ہوں...",
        "voice_status_error": "براہ کرم دوبارہ کوشش کریں",

        "voice_transcript_title": "آپ کا سوال",
        "voice_status_interrupted": "روک دیا گیا",
        "voice_response_title": "معاون کا جواب",
        "voice_speak_now": "حج ایجنسیوں کے بارے میں مجھ سے کچھ بھی پوچھیں...",
        "voice_response_placeholder": "آپ کا جواب یہاں ظاہر ہوگا...",
        "voice_key_points": "اہم معلومات",
        "voice_suggested_actions": "تجویز کردہ اگلے اقدامات",
        "voice_verification_steps": "تصدیق کیسے کریں",
        "voice_no_speech": "میں آپ کو واضح طور پر نہیں سن سکا",
        "voice_try_again": "براہ کرم واضح طور پر بولیں اور دوبارہ کوشش کریں",
        "voice_error_occurred": "کچھ غلط ہو گیا۔ آئیے دوبارہ کوشش کریں۔",
                "footer_chat": "اے آئی ٹیکنالوجی",

        "voice_could_not_understand": "میں یہ نہیں سمجھ سکا۔ کیا آپ دوبارہ کہہ سکتے ہیں؟",
        "voice_error_processing": "مجھے اس درخواست پر کارروائی کرنے میں دشواری ہو رہی ہے",

        # Additional helpful labels in Urdu
        "voice_stop_speaking": "رکیں",
        "voice_memory_messages": "پیغامات",
        "voice_session_duration": "سیشن کا وقت",
    }
}


def t(key: str, lang: str = "English", **kwargs) -> str:
    """
    Get translation for key in specified language with optional formatting
    
    Args:
        key: Translation key
        lang: Language (English, العربية, or اردو)
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


# Language mapping for easier lookup
LANGUAGE_MAP = {
    'en': 'English',
    'english': 'English',
    'ar': 'العربية',
    'arabic': 'العربية',
    'العربية': 'العربية',
    'ur': 'اردو',
    'urdu': 'اردو',
    'اردو': 'اردو'
}


def get_language_name(code: str) -> str:
    """Convert language code to full language name"""
    return LANGUAGE_MAP.get(code.lower(), 'العربية')