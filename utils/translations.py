"""
Translation Manager Module - Enhanced
Handles all text translations for multilingual support
Includes: English, Arabic, and Urdu
Updated with Report Page translations
"""

TRANSLATIONS = {
    "English": {
        # Page
        "page_title": "Talbiyah",
        "main_title": "Talbiyah",
        "subtitle": "Ask anything about Hajj companies worldwide • AI-powered • Real-time data",
        
        # Assistant
        "assistant_title": "🕋 Talbiyah Assistant",
        "assistant_subtitle": "Your AI-powered guide",
        "footer_chat": "AI Technology",
        
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
        "language_ur": "Urdu",
        
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
        "feat_multilingual_desc": "Supports Arabic, English, and Urdu for better accessibility.",
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
        
        # Accessibility
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
        "language_switched": "Language switched to {lang}",
        
        # Memory Status
        "memory_status_title": "🧠 Memory Status",
        "memory_status_desc": "Review your current session progress.",
        "voice_memory_messages": "Messages",
        "voice_session_duration": "Duration",
        "voice_clear_memory": "Clear Memory",
        "memory_cleared": "Memory cleared successfully!",
        
        # Navigation
        "nav_title": "🏠 Navigation",
        "nav_caption": "Return to the main chat interface.",
        "voice_return_button": "Return",
        
        # Quick Actions
        "find_authorized": "Find Authorized Agencies",
        "show_stats": "Show Statistics",
        "find_by_country": "Search by Country",
        "general_help": "General Help",
        
        # Voice Bot
        "voice_page_title": "Talbiyah Voice Verification Assistant",
        "voice_main_title": "Talbiyah Voice Assistant",
        "voice_subtitle": "Your trusted companion for verifying authorized Hajj agencies and protecting pilgrims",
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
        "voice_stop_speaking": "Stop",
        
        # Report Page Translations
        "report_page_title": "Talbiyah Complaint Reporting",
        "report_main_title": "Talbiyah Reporting Office",
        "report_subtitle": "Secure and Encrypted Channel for Filing Agency Complaints",
        "report_badge": "🔒 Trustworthy • Secure • Official",
        "report_welcome": "🛡️ <strong>Welcome to the Confidential Reporting Office</strong><br><br>Thank you for your courage. Your report is vital in protecting Hajj and Umrah integrity.<br><br><strong>All information is encrypted and confidential.</strong>",
        "report_step_1": "<strong>Step 1 of 4:</strong> What is the <strong>full name</strong> of the agency you want to report?",
        "report_step_2": "<strong>Step 2 of 4:</strong> Which <strong>city</strong> is this agency located in?",
        "report_step_3": "<strong>Step 3 of 4:</strong> Please describe the incident in detail:<br>- What happened?<br>- When? (approximate date)<br>- Any amounts or payments involved?<br>- Promises made that were broken?",
        "report_step_4": "<strong>Step 4 of 4 (Optional):</strong> Provide contact info for follow-up, or type \"<strong>skip</strong>\" to remain anonymous.",
        "report_agency_recorded": "✅ <strong>Agency recorded:</strong> {name}",
        "report_location_recorded": "✅ <strong>Location recorded:</strong> {city}",
        "report_details_recorded": "✅ <strong>Details recorded</strong>",
        "report_summary": "<strong>Summary:</strong><br>- Agency: {agency}<br>- City: {city}<br>- Details: {details}",
        "report_success": "✅ <strong>Report Successfully Filed</strong><br><br>{message}<br><br><strong>Status:</strong> Pending Review<br><br>Your report is now with the relevant authorities. Redirecting to main chat...",
        "report_failed": "❌ <strong>Submission Failed</strong><br><br>{message}<br><br>Please try again or modify your submission.",
        "report_validation_error": "⚠️ <strong>Validation Issue</strong><br><br>{feedback}",
        "db_connection_error": "⚠️ Database connection failed. Please contact support.",
        "secure_reporting": "🔒 Secure Reporting",
        "all_encrypted": "All communications are encrypted and confidential",
        "current_progress": "Current Progress",
        "progress_complete": "{pct}% Complete",
        "exit_reporting": "🚪 Exit Reporting Channel",
        "quick_save": "💾 Quick Save Draft",
        "draft_saved": "✅ Draft saved!",
        "exit_not_started": "You haven't started the report yet.",
        "exit_just_started": "You've only entered basic information.",
        "exit_partial": "You're halfway through. Your agency and location are saved.",
        "exit_almost_complete": "You're almost done! Only contact info remains.",
        "exit_unsaved": "You have unsaved progress.",
        "draft_found_title": "💾 Draft Report Found!",
        "draft_found_desc": "You have a saved draft from your previous session. Would you like to continue where you left off?",
        "draft_agency": "**Agency:** {name}",
        "draft_city": "**City:** {city}",
        "draft_details": "**Details:** {preview}",
        "draft_saved_at": "📅 <em>Saved at step {step} of 4</em>",
        "resume_draft": "✅ Resume Draft",
        "start_fresh": "🗑️ Start Fresh",
        "draft_restored": "✅ Draft restored!",
        "draft_discarded": "Draft discarded. Starting new report...",
        "modal_return_chat": "Return to Main Chat?",
        "modal_not_started_desc": "You haven't started filing a report yet. You can return anytime to file a complaint.",
        "modal_yes_return": "✅ Yes, Return to Chat",
        "modal_stay_file": "📝 Stay & File Report",
        "modal_exit_title": "Exit Reporting?",
        "modal_save_draft": "💾 Save Draft",
        "modal_discard_exit": "🗑️ Discard & Exit",
        "modal_continue": "↩️ Continue",
        "modal_significant_progress": "You Have Significant Progress!",
        "modal_important": "⏰ Your report is important! Consider saving a draft to continue later.",
        "modal_save_and_exit": "💾 Save Draft & Exit",
        "modal_discard_progress": "🗑️ Discard Progress",
        "modal_continue_filing": "✍️ Continue Filing",
        "modal_confirm_discard": "⚠️ Are you sure? Click 'Discard Progress' again to confirm.",
        "progress_discarded": "Progress discarded.",
        "draft_saved_success": "✅ Draft saved! You can resume later.",
        "draft_saved_resume": "✅ Draft saved! Resume anytime from the main menu.",
        "resuming_draft": "🛡️ <strong>Welcome back!</strong> Resuming your saved draft...",
        "chat_input_placeholder": "Type your response here...",
        "report_submitted": "✅ Report submitted successfully!",
        
        # Sample Questions
        "sample_questions": [
            "What are the Hajj requirements?",
            "Find affordable packages",
            "When should I book?",
            "Tell me about Mina"
        ],
        "examples_caption": "Try one of these to get started quickly:",
    },
    
    "العربية": {
        # Page
        "page_title": " تلبية",
        "main_title": " مساعد تلبية",
        "subtitle": "اسأل عن شركات الحج حول العالم • مدعوم بالذكاء الاصطناعي • بيانات فورية",
        
        # Assistant
        "assistant_title": " مساعد تلبية",
        "assistant_subtitle": "دليلك الذكي المدعوم بالذكاء الاصطناعي",
        "footer_chat": "تقنية الذكاء الاصطناعي",
        
        # Sidebar
        "language_title": "🌐 اللغة",
        "stats_title": "📊 الإحصائيات المباشرة",
        "footer_title_voice": "مساعد الحج الصوتي",
        "footer_powered": "مدعوم بواسطة",
        "footer_tech": "تقنية الذكاء الاصطناعي الصوتية",
        "examples_title": "💡 أمثلة سريعة",
        "clear_chat": "🧹 مسح سجل المحادثة",
        "features_title": "ℹ️ المميزات",
        "language_en": "الإنجليزية",
        "language_ar": "العربية",
        "language_ur": "أردو",
        
        # Mode Navigation
        "mode_title": "🔀 الوضع",
        "mode_chatbot": "المحادثة",
        "mode_voicebot": "المساعد الصوتي",
        "voicebot_unavailable": "صفحة المساعد الصوتي غير متاحة",
        "voice_status_interrupted": "تم الإيقاف",
        
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
        "feat_multilingual_desc": "يدعم العربية والإنجليزية والأردية لتحسين الوصول.",
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
        
        # Accessibility
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
        "language_switched": "تم تغيير اللغة إلى {lang}",
        
        # Memory Status
        "memory_status_title": "🧠 حالة الذاكرة",
        "memory_status_desc": "راجع تقدم الجلسة الحالية.",
        "voice_memory_messages": "الرسائل",
        "voice_session_duration": "المدة",
        "voice_clear_memory": "مسح الذاكرة",
        "memory_cleared": "تم مسح الذاكرة بنجاح!",
        
        # Navigation
        "nav_title": "🏠 التنقل",
        "nav_caption": "العودة إلى واجهة الدردشة الرئيسية.",
        "voice_return_button": "عودة",
        
        # Quick Actions
        "find_authorized": "ابحث عن الشركات المعتمدة",
        "show_stats": "عرض الإحصائيات",
        "find_by_country": "البحث حسب الدولة",
        "general_help": "مساعدة عامة",
        
        # Voice Bot
        "voice_page_title": " مساعد تلبية الصوتي",
        "voice_main_title": " مساعد تلبية الصوتي",
        "voice_subtitle": "رفيقك الموثوق للتحقق من وكالات الحج المعتمدة وحماية الحجاج",
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
        "voice_stop_speaking": "إيقاف",
        
        # Report Page Translations
        "report_page_title": " إبلاغ تلبية",
        "report_main_title": " مركز إبلاغ تلبية",
        "report_subtitle": "قناة آمنة ومشفرة للإبلاغ عن شكاوى الوكالات"
        "report_badge": "🔒 موثوق • آمن • رسمي",
        "report_welcome": "🛡️ <strong>مرحباً بك في مكتب الإبلاغ السري</strong><br><br>شكراً لشجاعتك. تقريرك حيوي في حماية سلامة الحج والعمرة.<br><br><strong>جميع المعلومات مشفرة وسرية.</strong>",
        "report_step_1": "<strong>الخطوة 1 من 4:</strong> ما هو <strong>الاسم الكامل</strong> للوكالة التي تريد الإبلاغ عنها؟",
        "report_step_2": "<strong>الخطوة 2 من 4:</strong> في أي <strong>مدينة</strong> تقع هذه الوكالة؟",
        "report_step_3": "<strong>الخطوة 3 من 4:</strong> يرجى وصف الحادثة بالتفصيل:<br>- ماذا حدث؟<br>- متى؟ (تاريخ تقريبي)<br>- أي مبالغ أو مدفوعات متضمنة؟<br>- وعود قُطعت ولم تُنفذ؟",
        "report_step_4": "<strong>الخطوة 4 من 4 (اختياري):</strong> قدم معلومات الاتصال للمتابعة، أو اكتب \"<strong>تخطي</strong>\" للبقاء مجهولاً.",
        "report_agency_recorded": "✅ <strong>تم تسجيل الوكالة:</strong> {name}",
        "report_location_recorded": "✅ <strong>تم تسجيل الموقع:</strong> {city}",
        "report_details_recorded": "✅ <strong>تم تسجيل التفاصيل</strong>",
        "report_summary": "<strong>ملخص:</strong><br>- الوكالة: {agency}<br>- المدينة: {city}<br>- التفاصيل: {details}",
        "report_success": "✅ <strong>تم تقديم التقرير بنجاح</strong><br><br>{message}<br><br><strong>الحالة:</strong> قيد المراجعة<br><br>تقريرك الآن مع السلطات المعنية. إعادة التوجيه إلى المحادثة الرئيسية...",
        "report_failed": "❌ <strong>فشل الإرسال</strong><br><br>{message}<br><br>يرجى المحاولة مرة أخرى أو تعديل إرسالك.",
        "report_validation_error": "⚠️ <strong>مشكلة في التحقق</strong><br><br>{feedback}",
        "db_connection_error": "⚠️ فشل الاتصال بقاعدة البيانات. يرجى الاتصال بالدعم.",
        "secure_reporting": "🔒 إبلاغ آمن",
        "all_encrypted": "جميع الاتصالات مشفرة وسرية",
        "current_progress": "التقدم الحالي",
        "progress_complete": "{pct}٪ مكتمل",
        "exit_reporting": "🚪 الخروج من قناة الإبلاغ",
        "quick_save": "💾 حفظ سريع للمسودة",
        "draft_saved": "✅ تم حفظ المسودة!",
        "exit_not_started": "لم تبدأ التقرير بعد.",
        "exit_just_started": "لقد أدخلت معلومات أساسية فقط.",
        "exit_partial": "أنت في منتصف الطريق. تم حفظ الوكالة والموقع.",
        "exit_almost_complete": "أنت على وشك الانتهاء! تبقى معلومات الاتصال فقط.",
        "exit_unsaved": "لديك تقدم غير محفوظ.",
        "draft_found_title": "💾 تم العثور على مسودة تقرير!",
        "draft_found_desc": "لديك مسودة محفوظة من جلستك السابقة. هل تريد المتابعة من حيث توقفت؟",
        "draft_agency": "**الوكالة:** {name}",
        "draft_city": "**المدينة:** {city}",
        "draft_details": "**التفاصيل:** {preview}",
        "draft_saved_at": "📅 <em>محفوظة في الخطوة {step} من 4</em>",
        "resume_draft": "✅ استئناف المسودة",
        "start_fresh": "🗑️ ابدأ من جديد",
        "draft_restored": "✅ تم استعادة المسودة!",
        "draft_discarded": "تم تجاهل المسودة. بدء تقرير جديد...",
        "modal_return_chat": "العودة إلى المحادثة الرئيسية؟",
        "modal_not_started_desc": "لم تبدأ في تقديم تقرير بعد. يمكنك العودة في أي وقت لتقديم شكوى.",
        "modal_yes_return": "✅ نعم، العودة إلى المحادثة",
        "modal_stay_file": "📝 البقاء وتقديم التقرير",
        "modal_exit_title": "الخروج من الإبلاغ؟",
        "modal_save_draft": "💾 حفظ المسودة",
        "modal_discard_exit": "🗑️ تجاهل والخروج",
        "modal_continue": "↩️ متابعة",
        "modal_significant_progress": "لديك تقدم كبير!",
        "modal_important": "⏰ تقريرك مهم! فكر في حفظ مسودة للمتابعة لاحقاً.",
        "modal_save_and_exit": "💾 حفظ المسودة والخروج",
        "modal_discard_progress": "🗑️ تجاهل التقدم",
        "modal_continue_filing": "✍️ متابعة التقديم",
        "modal_confirm_discard": "⚠️ هل أنت متأكد؟ انقر على 'تجاهل التقدم' مرة أخرى للتأكيد.",
        "progress_discarded": "تم تجاهل التقدم.",
        "draft_saved_success": "✅ تم حفظ المسودة! يمكنك الاستئناف لاحقاً.",
        "draft_saved_resume": "✅ تم حفظ المسودة! استأنف في أي وقت من القائمة الرئيسية.",
        "resuming_draft": "🛡️ <strong>مرحباً بعودتك!</strong> استئناف المسودة المحفوظة...",
        "chat_input_placeholder": "اكتب إجابتك هنا...",
        "report_submitted": "✅ تم تقديم التقرير بنجاح!",
        
        # Sample Questions
        "sample_questions": [
            "ما هي متطلبات الحج؟",
            "ابحث عن باقات بأسعار معقولة",
            "متى يجب أن أحجز؟",
            "أخبرني عن منى"
        ],
        "examples_caption": "جرّب أحد هذه الأسئلة للبدء بسرعة:",
    },
    
    "اردو": {
        # Page
        "page_title": " تلبیہ",
        "main_title": " تلبیہ",
        "subtitle": "دنیا بھر کی حج کمپنیوں کے بارے میں کچھ بھی پوچھیں • AI سے چلنے والا • حقیقی وقت کا ڈیٹا",
        
        # Assistant
        "assistant_title": " تلبیہ اسسٹنٹ",
        "assistant_subtitle": "آپ کا AI سے چلنے والا رہنما",
        "footer_chat": "اے آئی ٹیکنالوجی",
        
        # Sidebar
        "language_title": "🌐 زبان",
        "stats_title": "📊 براہ راست شماریات",
        "footer_title_voice": "حج وائس اسسٹنٹ",
        "footer_powered": "کے ذریعے چلنے والا",
        "footer_tech": "اے آئی آواز کی ٹیکنالوجی",
        "examples_title": "💡 فوری مثالیں",
        "clear_chat": "🧹 چیٹ کی تاریخ صاف کریں",
        "features_title": "ℹ️ خصوصیات",
        "language_en": "انگریزی",
        "language_ar": "عربی",
        "language_ur": "اردو",
        
        # Mode Navigation
        "mode_title": "🔀 موڈ",
        "mode_chatbot": "چیٹ بوٹ",
        "mode_voicebot": "وائس بوٹ",
        "voicebot_unavailable": "صوتی معاون کا صفحہ دستیاب نہیں ہے",
        "voice_status_interrupted": "روک دیا گیا",
        
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
        "feat_multilingual_desc": "بہتر رسائی کے لیے عربی، انگریزی اور اردو کی حمایت کرتا ہے۔",
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
        
        # Accessibility
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
        "language_switched": "زبان تبدیل کر دی گئی: {lang}",
        
        # Memory Status
        "memory_status_title": "🧠 یادداشت کی حالت",
        "memory_status_desc": "اپنے موجودہ سیشن کی پیش رفت دیکھیں۔",
        "voice_memory_messages": "پیغامات",
        "voice_session_duration": "دورانیہ",
        "voice_clear_memory": "یادداشت صاف کریں",
        "memory_cleared": "یادداشت کامیابی سے صاف ہو گئی!",
        
        # Navigation
        "nav_title": "🏠 نیویگیشن",
        "nav_caption": "مین چیٹ انٹرفیس پر واپس جائیں۔",
        "voice_return_button": "واپس",
        
        # Quick Actions
        "find_authorized": "مجاز ایجنسیاں تلاش کریں",
        "show_stats": "شماریات دکھائیں",
        "find_by_country": "ملک کے لحاظ سے تلاش کریں",
        "general_help": "عمومی مدد",
        
        # Voice Bot
        "voice_page_title": " تلبیہ وائس اسسٹنٹ",
        "voice_main_title": " تلبیہ وائس اسسٹنٹ",
        "voice_subtitle": "آپ کا اعتماد مند ساتھی جو مجاز حج ایجنسیوں کی تصدیق اور عازمین کی حفاظت کے لیے ہے",
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
        "voice_response_title": "معاون کا جواب",
        "voice_speak_now": "حج ایجنسیوں کے بارے میں مجھ سے کچھ بھی پوچھیں...",
        "voice_response_placeholder": "آپ کا جواب یہاں ظاہر ہوگا...",
        "voice_key_points": "اہم معلومات",
        "voice_suggested_actions": "تجویز کردہ اگلے اقدامات",
        "voice_verification_steps": "تصدیق کیسے کریں",
        "voice_no_speech": "میں آپ کو واضح طور پر نہیں سن سکا",
        "voice_try_again": "براہ کرم واضح طور پر بولیں اور دوبارہ کوشش کریں",
        "voice_error_occurred": "کچھ غلط ہو گیا۔ آئیے دوبارہ کوشش کریں۔",
        "voice_could_not_understand": "میں یہ نہیں سمجھ سکا۔ کیا آپ دوبارہ کہہ سکتے ہیں؟",
        "voice_error_processing": "مجھے اس درخواست پر کارروائی کرنے میں دشواری ہو رہی ہے",
        "voice_stop_speaking": "رکیں",
        
        # Report Page Translations
        "report_page_title": " تلبیہ رپورٹنگ",
        "report_main_title": " تلبیہ رپورٹنگ دفتر",
        "report_subtitle": "ایجنسی کی شکایات درج کرنے کے لیے محفوظ اور خفیہ کاری شدہ چینل"
        "report_badge": "🔒 قابل اعتماد • محفوظ • سرکاری",
        "report_welcome": "🛡️ <strong>خفیہ رپورٹنگ دفتر میں خوش آمدید</strong><br><br>آپ کی ہمت کا شکریہ۔ آپ کی رپورٹ حج اور عمرہ کی سالمیت کی حفاظت میں اہم ہے۔<br><br><strong>تمام معلومات خفیہ کاری شدہ اور رازداری میں ہیں۔</strong>",
        "report_step_1": "<strong>مرحلہ 1 از 4:</strong> اس ایجنسی کا <strong>مکمل نام</strong> کیا ہے جس کی آپ رپورٹ کرنا چاہتے ہیں؟",
        "report_step_2": "<strong>مرحلہ 2 از 4:</strong> یہ ایجنسی کس <strong>شہر</strong> میں واقع ہے؟",
        "report_step_3": "<strong>مرحلہ 3 از 4:</strong> براہ کرم واقعے کی تفصیل سے وضاحت کریں:<br>- کیا ہوا؟<br>- کب؟ (تقریباً تاریخ)<br>- کوئی رقم یا ادائیگیاں شامل؟<br>- وعدے جو توڑے گئے؟",
        "report_step_4": "<strong>مرحلہ 4 از 4 (اختیاری):</strong> فالو اپ کے لیے رابطے کی معلومات فراہم کریں، یا گمنام رہنے کے لیے \"<strong>چھوڑیں</strong>\" لکھیں۔",
        "report_agency_recorded": "✅ <strong>ایجنسی ریکارڈ کی گئی:</strong> {name}",
        "report_location_recorded": "✅ <strong>مقام ریکارڈ کیا گیا:</strong> {city}",
        "report_details_recorded": "✅ <strong>تفصیلات ریکارڈ کی گئیں</strong>",
        "report_summary": "<strong>خلاصہ:</strong><br>- ایجنسی: {agency}<br>- شہر: {city}<br>- تفصیلات: {details}",
        "report_success": "✅ <strong>رپورٹ کامیابی سے درج کی گئی</strong><br><br>{message}<br><br><strong>حیثیت:</strong> زیر نظرثانی<br><br>آپ کی رپورٹ اب متعلقہ حکام کے پاس ہے۔ مین چیٹ پر واپس جا رہے ہیں...",
        "report_failed": "❌ <strong>جمع کروانا ناکام</strong><br><br>{message}<br><br>براہ کرم دوبارہ کوشش کریں یا اپنی جمع کروائی کو تبدیل کریں۔",
        "report_validation_error": "⚠️ <strong>توثیق کا مسئلہ</strong><br><br>{feedback}",
        "db_connection_error": "⚠️ ڈیٹا بیس کنکشن ناکام ہو گیا۔ براہ کرم سپورٹ سے رابطہ کریں۔",
        "secure_reporting": "🔒 محفوظ رپورٹنگ",
        "all_encrypted": "تمام مواصلات خفیہ کاری شدہ اور رازداری میں ہیں",
        "current_progress": "موجودہ پیش رفت",
        "progress_complete": "{pct}٪ مکمل",
        "exit_reporting": "🚪 رپورٹنگ چینل سے باہر نکلیں",
        "quick_save": "💾 فوری ڈرافٹ محفوظ کریں",
        "draft_saved": "✅ ڈرافٹ محفوظ ہو گیا!",
        "exit_not_started": "آپ نے ابھی رپورٹ شروع نہیں کی۔",
        "exit_just_started": "آپ نے صرف بنیادی معلومات درج کیں۔",
        "exit_partial": "آپ آدھے راستے پر ہیں۔ آپ کی ایجنسی اور مقام محفوظ ہیں۔",
        "exit_almost_complete": "آپ تقریباً مکمل ہو چکے ہیں! صرف رابطے کی معلومات باقی ہیں۔",
        "exit_unsaved": "آپ کی غیر محفوظ شدہ پیش رفت ہے۔",
        "draft_found_title": "💾 ڈرافٹ رپورٹ ملی!",
        "draft_found_desc": "آپ کے پچھلے سیشن سے ایک محفوظ شدہ ڈرافٹ موجود ہے۔ کیا آپ جہاں چھوڑا تھا وہاں سے جاری رکھنا چاہتے ہیں؟",
        "draft_agency": "**ایجنسی:** {name}",
        "draft_city": "**شہر:** {city}",
        "draft_details": "**تفصیلات:** {preview}",
        "draft_saved_at": "📅 <em>مرحلہ {step} از 4 پر محفوظ کیا گیا</em>",
        "resume_draft": "✅ ڈرافٹ جاری رکھیں",
        "start_fresh": "🗑️ نئے سرے سے شروع کریں",
        "draft_restored": "✅ ڈرافٹ بحال ہو گیا!",
        "draft_discarded": "ڈرافٹ مسترد کر دیا گیا۔ نئی رپورٹ شروع کر رہے ہیں...",
        "modal_return_chat": "مین چیٹ پر واپس جائیں؟",
        "modal_not_started_desc": "آپ نے ابھی رپورٹ درج کرنا شروع نہیں کیا۔ آپ کسی بھی وقت شکایت درج کرنے کے لیے واپس آ سکتے ہیں۔",
        "modal_yes_return": "✅ ہاں، چیٹ پر واپس جائیں",
        "modal_stay_file": "📝 رہیں اور رپورٹ درج کریں",
        "modal_exit_title": "رپورٹنگ سے باہر نکلیں؟",
        "modal_save_draft": "💾 ڈرافٹ محفوظ کریں",
        "modal_discard_exit": "🗑️ مسترد کریں اور باہر نکلیں",
        "modal_continue": "↩️ جاری رکھیں",
        "modal_significant_progress": "آپ کی اہم پیش رفت ہے!",
        "modal_important": "⏰ آپ کی رپورٹ اہم ہے! بعد میں جاری رکھنے کے لیے ڈرافٹ محفوظ کرنے پر غور کریں۔",
        "modal_save_and_exit": "💾 ڈرافٹ محفوظ کریں اور باہر نکلیں",
        "modal_discard_progress": "🗑️ پیش رفت مسترد کریں",
        "modal_continue_filing": "✍️ فائلنگ جاری رکھیں",
        "modal_confirm_discard": "⚠️ کیا آپ کو یقین ہے؟ تصدیق کے لیے 'پیش رفت مسترد کریں' پر دوبارہ کلک کریں۔",
        "progress_discarded": "پیش رفت مسترد کر دی گئی۔",
        "draft_saved_success": "✅ ڈرافٹ محفوظ ہو گیا! آپ بعد میں جاری رکھ سکتے ہیں۔",
        "draft_saved_resume": "✅ ڈرافٹ محفوظ ہو گیا! مین مینو سے کسی بھی وقت جاری رکھیں۔",
        "resuming_draft": "🛡️ <strong>واپسی مبارک!</strong> آپ کا محفوظ شدہ ڈرافٹ جاری ہو رہا ہے...",
        "chat_input_placeholder": "اپنا جواب یہاں لکھیں...",
        "report_submitted": "✅ رپورٹ کامیابی سے جمع کرائی گئی!",
        
        # Sample Questions
        "sample_questions": [
            "حج کی ضروریات کیا ہیں؟",
            "سستے پیکجز تلاش کریں",
            "میں کب بکنگ کروں؟",
            "منا کے بارے میں بتائیں"
        ],
        "examples_caption": "شروع کرنے کے لیے ان میں سے کوئی ایک آزمائیں:",
    }
}


def t(key: str, lang: str = "العربية", **kwargs) -> str:
    """
    Get translation for key in specified language with optional formatting
    
    Args:
        key: Translation key
        lang: Language (English, العربية, or اردو)
        **kwargs: Format arguments for string interpolation
    
    Returns:
        Translated string
    """
    text = TRANSLATIONS.get(lang, TRANSLATIONS["العربية"]).get(key, key)
    
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
