"""
Hajj Complaint Reporting Bot - Main Application
Enhanced UX with intelligent exit handling for all scenarios
Multi-language support: English, Arabic, Urdu
Updated to match Supabase schema with status field
"""

import streamlit as st
from datetime import datetime
import pytz
import time
from typing import Dict, Optional, Tuple
import logging

# Supabase imports
from supabase import create_client, Client

# Import core modules
from core.report_llm import RLLMManager
from utils.translations import t, LANGUAGE_MAP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================
COMPLAINT_STATUS = {
    "pending": "Pending Review",
    "under_investigation": "Under Investigation",
    "resolved": "Resolved",
    "closed": "Closed"
}


# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================

def get_supabase_client() -> Optional[Client]:
    """
    Initialize and return Supabase client with proper error handling
    Uses st.cache_resource for singleton pattern
    """
    @st.cache_resource
    def init_client() -> Optional[Client]:
        try:
            url = st.secrets.get('supabase_url')
            key = st.secrets.get("supabase_key")
            
            if not url or not key:
                logger.error("Supabase credentials missing in secrets")
                return None
                
            return create_client(url, key)
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            return None
    
    client = init_client()
    if client is None:
        lang = st.session_state.get("language", "العربية")
        st.error(t("db_connection_error", lang))
        st.stop()
    return client


# =============================================================================
# CSS STYLING WITH RTL SUPPORT
# =============================================================================

def get_css_styles(lang: str) -> str:
    """Generate CSS with RTL support for Arabic and Urdu"""
    is_rtl = lang in ["العربية", "اردو"]
    text_align = "right" if is_rtl else "left"
    direction = "rtl" if is_rtl else "ltr"
    
    # Font selection based on language
    if lang == "العربية":
        font_family = "'Cairo', 'Poppins', sans-serif"
    elif lang == "اردو":
        font_family = "'Noto Nastaliq Urdu', 'Cairo', 'Poppins', sans-serif"
    else:
        font_family = "'Poppins', sans-serif"
    
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Cairo:wght@400;600;700;800&family=Noto+Nastaliq+Urdu:wght@400;600;700&display=swap');

/* ===== Secure Reporting Theme Variables ===== */
:root {{
    --color-primary-authority: #1e3a8a;
    --color-secondary-security: #708090;
    --color-background-light: #ffffff;
    --color-background-mid: #f5f7fa;
    --color-text-dark: #1a1f2e;
    --color-text-mid: #4b5563;
    --color-border-subtle: #e5e7eb;
}}

/* ===== Global Styles with RTL Support ===== */
* {{
    font-family: {font_family};
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}

.main {{
    direction: {direction};
    text-align: {text_align};
    background-color: var(--color-background-mid);
    background-attachment: fixed;
}}

.block-container {{
    padding-top: 2.5rem;
    padding-bottom: 2.5rem;
    max-width: 1400px;
}}

/* ===== Elegant Header ===== */
.header-container {{
    background: linear-gradient(135deg, var(--color-background-light) 0%, var(--color-background-mid) 100%);
    backdrop-filter: blur(15px);
    border-radius: 20px;
    padding: 2.5rem 2rem;
    margin-bottom: 2.5rem;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
    text-align: center;
    border: 1px solid var(--color-secondary-security);
    animation: fadeInDown 0.6s ease-out;
    position: relative;
    overflow: hidden;
    direction: {direction};
}}

.header-container::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--color-primary-authority) 0%, #a5b4fc 50%, var(--color-primary-authority) 100%);
    animation: shimmer 3s infinite;
}}

@keyframes shimmer {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.8; }}
}}

.main-title {{
    font-size: 3.2rem;
    font-weight: 900;
    color: var(--color-text-dark);
    margin: 0;
    letter-spacing: -1px;
    text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.05);
}}

.title-highlight {{
    background: linear-gradient(135deg, var(--color-primary-authority) 0%, #3b82f6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.subtitle {{
    color: var(--color-text-mid);
    font-size: 1.1rem;
    margin-top: 0.5rem;
    font-weight: 400;
    line-height: 1.6;
}}

.header-badge {{
    background-color: var(--color-secondary-security); 
    color: white;
    padding: 0.3rem 1.15rem;
    border-radius: 50px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 1rem;
    box-shadow: 0 4px 10px rgba(112, 128, 144, 0.3);
}}

/* ===== Progress Indicator ===== */
.progress-container {{
    background: var(--color-background-light);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    border: 1px solid var(--color-border-subtle);
    direction: {direction};
}}

.progress-bar {{
    width: 100%;
    height: 6px;
    background: var(--color-border-subtle);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 0.5rem;
}}

.progress-fill {{
    height: 100%;
    background: linear-gradient(90deg, var(--color-primary-authority) 0%, #3b82f6 100%);
    border-radius: 10px;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}}

.progress-text {{
    display: flex;
    justify-content: space-between;
    color: var(--color-text-mid);
    font-size: 0.85rem;
    font-weight: 500;
    direction: {direction};
}}

/* ===== Elegant Modal ===== */
.modal-content {{
    background: var(--color-background-light);
    border-radius: 16px;
    padding: 2.5rem;
    max-width: 450px;
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
    animation: slideInScale 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    text-align: center;
    border: 2px solid var(--color-primary-authority);
    direction: {direction};
}}

.modal-icon {{
    font-size: 3rem;
    margin-bottom: 0.75rem;
    color: var(--color-primary-authority);
}}

.modal-title {{
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--color-text-dark);
    margin-bottom: 0.75rem;
}}

.modal-text {{
    color: var(--color-text-mid);
    font-size: 1rem;
    font-weight: 400;
    line-height: 1.5;
    margin-bottom: 1.5rem;
}}

/* ===== Chat Messages with RTL ===== */
.stChatMessage {{
    background: var(--color-background-light) !important;
    backdrop-filter: blur(8px);
    border-radius: 16px !important;
    padding: 1.5rem !important;
    margin: 1rem 0 !important;
    box-shadow: 0 2px 15px rgba(0, 0, 0, 0.05) !important;
    border: 1px solid var(--color-border-subtle);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    animation: slideInUp 0.4s ease-out;
    direction: {direction};
    text-align: {text_align};
}}

.stChatMessage:hover {{
    transform: translateY(-1px);
    box-shadow: 0 5px 20px rgba(0, 0, 0, 0.08) !important;
    border-color: var(--color-primary-authority);
}}

.stChatMessage[data-testid*="user"] {{
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%) !important;
    border-{text_align}: 4px solid var(--color-primary-authority);
}}

.stChatMessage[data-testid*="assistant"] {{
    background: linear-gradient(135deg, #f9fafb 0%, #eff6ff 100%) !important;
    border-{text_align}: 4px solid var(--color-secondary-security);
}}

.bot-message {{
    background: linear-gradient(135deg, #f0f8ff 0%, #e0f2fe 100%) !important;
    border: 2px solid var(--color-primary-authority) !important;
    border-{text_align}: 6px solid var(--color-primary-authority) !important;
    color: var(--color-text-dark) !important;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    font-weight: 500;
    direction: {direction};
    text-align: {text_align};
}}

.bot-message * {{
    color: var(--color-text-dark) !important;
}}

/* ===== Sidebar with RTL ===== */
[data-testid="stSidebar"] {{
    background: var(--color-background-light);
    border-{text_align}: 1px solid var(--color-border-subtle);
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);
    direction: {direction};
    text-align: {text_align};
}}

[data-testid="stSidebar"] *,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label {{
    color: var(--color-text-dark) !important;
}}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{
    color: var(--color-primary-authority) !important;
    font-weight: 700;
}}

/* ===== Modal Overlay ===== */
.modal-overlay-backdrop {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.75);
    z-index: 999998;
    backdrop-filter: blur(4px);
    animation: fadeIn 0.3s ease-out;
}}

.modal-popup {{
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 999999;
    background: white;
    border-radius: 20px;
    padding: 2.5rem;
    max-width: 550px;
    width: 90%;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
    animation: slideInScale 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    direction: {direction};
    text-align: center;
}}

@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
}}

@keyframes slideInScale {{
    from {{
        opacity: 0;
        transform: translate(-50%, -48%) scale(0.9);
    }}
    to {{
        opacity: 1;
        transform: translate(-50%, -50%) scale(1);
    }}
}}

@keyframes slideInUp {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
</style>
"""


# =============================================================================
# TRANSLATION ADDITIONS FOR REPORT PAGE
# =============================================================================

# Add missing translations to translation_manager.py content
REPORT_TRANSLATIONS = {
    "English": {
        "report_page_title": "Hajj Complaint Reporting",
        "report_main_title": "Confidential Reporting Office",
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
    },
    "العربية": {
        "report_page_title": "الإبلاغ عن شكوى الحج",
        "report_main_title": "مكتب الإبلاغ السري",
        "report_subtitle": "قناة آمنة ومشفرة لتقديم شكاوى الوكالات",
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
    },
    "اردو": {
        "report_page_title": "حج کی شکایت کی رپورٹنگ",
        "report_main_title": "خفیہ رپورٹنگ دفتر",
        "report_subtitle": "ایجنسی کی شکایات درج کرنے کے لیے محفوظ اور خفیہ کاری شدہ چینل",
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
    }
}


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

def check_agency_in_sqlite(agency_name: str, db_manager) -> Tuple[bool, Dict]:
    """
    Check if agency exists in SQLite agencies table
    Checks both Arabic and English names
    """
    try:
        normalized_name = agency_name.strip().lower()
        
        query = """
        SELECT hajj_company_en, hajj_company_ar, city, country, 
               email, contact_Info, rating_reviews, is_authorized,
               google_maps_link, formatted_address
        FROM agencies 
        WHERE LOWER(hajj_company_en) = ? OR LOWER(hajj_company_ar) = ?
        """
        
        result = db_manager.execute_query(query, (normalized_name, normalized_name))
        
        if result and len(result) > 0:
            agency = result[0]
            return True, {
                "name_en": agency[0],
                "name_ar": agency[1],
                "city": agency[2],
                "country": agency[3],
                "email": agency[4],
                "contact_info": agency[5],
                "rating": agency[6],
                "is_authorized": agency[7],
                "maps_link": agency[8],
                "address": agency[9]
            }
        
        fuzzy_query = """
        SELECT hajj_company_en, hajj_company_ar, city, country, 
               email, contact_Info, rating_reviews, is_authorized,
               google_maps_link, formatted_address
        FROM agencies 
        WHERE LOWER(hajj_company_en) LIKE ? OR LOWER(hajj_company_ar) LIKE ?
        LIMIT 1
        """
        
        result = db_manager.execute_query(fuzzy_query, (f"%{normalized_name}%", f"%{normalized_name}%"))
        
        if result and len(result) > 0:
            agency = result[0]
            return True, {
                "name_en": agency[0],
                "name_ar": agency[1],
                "city": agency[2],
                "country": agency[3],
                "email": agency[4],
                "contact_info": agency[5],
                "rating": agency[6],
                "is_authorized": agency[7],
                "maps_link": agency[8],
                "address": agency[9]
            }
        
        return False, {}
        
    except Exception as e:
        logger.error(f"Error checking agency in SQLite: {e}")
        return False, {}


def check_agency_exists_in_supabase(
    agency_name: str, 
    city: str, 
    supabase_client: Client
) -> bool:
    """Check if agency+city combination already exists in Supabase complaints table"""
    try:
        response = supabase_client.table('complaints').select('id').ilike(
            'agency_name', agency_name
        ).ilike('city', city).limit(1).execute()
        
        exists = response.data and len(response.data) > 0
        
        if exists:
            logger.info(f"Agency '{agency_name}' in '{city}' already exists in Supabase complaints")
        
        return exists
        
    except Exception as e:
        logger.error(f"Error checking Supabase for agency: {e}")
        return False


def submit_complaint_to_db(
    data: Dict, 
    contact: str, 
    supabase_client: Client,
    db_manager = None,
    lang: str = "العربية"
) -> Tuple[bool, str]:
    """Submit complaint to database with proper error handling and duplicate prevention"""
    try:
        agency_name = data["agency_name"]
        city = data["city"]
        agency_found_in_sqlite = False
        
        if db_manager:
            exists, agency_info = check_agency_in_sqlite(agency_name, db_manager)
            
            if exists:
                agency_found_in_sqlite = True
                logger.info(f"Agency found in SQLite: {agency_info.get('name_en', agency_name)}")
                
                agency_name_official = agency_info.get('name_en') or agency_info.get('name_ar') or agency_name
                
                is_authorized = agency_info.get('is_authorized', 'No')
                if is_authorized == 'Yes':
                    logger.warning(f"Report filed against AUTHORIZED agency: {agency_name_official}")
                
                if agency_info.get('city'):
                    city = agency_info['city']
                
                agency_name = agency_name_official
                
                logger.info(f"Using official name: {agency_name}, City: {city}")
            else:
                logger.info(f"Agency NOT found in SQLite: {agency_name}")
        
        already_exists = check_agency_exists_in_supabase(agency_name, city, supabase_client)
        
        if already_exists:
            logger.warning(f"Duplicate prevented: '{agency_name}' in '{city}' already in complaints")
            duplicate_msg = {
                "English": "This agency in this city has already been reported. Duplicate entry prevented.",
                "العربية": "تم الإبلاغ عن هذه الوكالة في هذه المدينة بالفعل. تم منع الإدخال المكرر.",
                "اردو": "اس شہر میں اس ایجنسی کی پہلے ہی اطلاع دی جا چکی ہے۔ نقل اندراج کو روک دیا گیا۔"
            }
            return False, duplicate_msg.get(lang, duplicate_msg["العربية"])
        
        insert_data = {
            "agency_name": agency_name,
            "city": city,
            "complaint_text": data["complaint_text"],
            "user_contact": contact if contact else None,
            "submission_date": datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S'),
            "status": "pending"
        }

        response = supabase_client.table('complaints').insert(insert_data).execute()
        
        if response.data and len(response.data) > 0:
            report_id = response.data[0].get('id', 'N/A')
            
            if contact:
                contact_status = {
                    "English": f"with secure contact",
                    "العربية": f"مع معلومات اتصال آمنة",
                    "اردو": f"محفوظ رابطے کے ساتھ"
                }
            else:
                contact_status = {
                    "English": f"anonymously",
                    "العربية": f"بشكل مجهول",
                    "اردو": f"گمنام طور پر"
                }
            
            if agency_found_in_sqlite:
                success_msg = {
                    "English": f"Report #{report_id} filed {contact_status['English']} (Agency verified in database)",
                    "العربية": f"تم تقديم التقرير #{report_id} {contact_status['العربية']} (تم التحقق من الوكالة في قاعدة البيانات)",
                    "اردو": f"رپورٹ #{report_id} {contact_status['اردو']} درج کی گئی (ایجنسی ڈیٹا بیس میں تصدیق شدہ)"
                }
            else:
                success_msg = {
                    "English": f"Report #{report_id} filed {contact_status['English']} (New agency - under review)",
                    "العربية": f"تم تقديم التقرير #{report_id} {contact_status['العربية']} (وكالة جديدة - قيد المراجعة)",
                    "اردو": f"رپورٹ #{report_id} {contact_status['اردو']} درج کی گئی (نئی ایجنسی - زیر نظرثانی)"
                }
            
            return True, success_msg.get(lang, success_msg["العربية"])
        else:
            logger.error("Supabase insert returned no data")
            error_msg = {
                "English": "Database insert failed - no data returned",
                "العربية": "فشل إدراج قاعدة البيانات - لم يتم إرجاع بيانات",
                "اردو": "ڈیٹا بیس داخلہ ناکام - کوئی ڈیٹا واپس نہیں آیا"
            }
            return False, error_msg.get(lang, error_msg["العربية"])
            
    except Exception as e:
        logger.error(f"Database submission error: {e}")
        error_msg = {
            "English": f"Database error: {str(e)}",
            "العربية": f"خطأ في قاعدة البيانات: {str(e)}",
            "اردو": f"ڈیٹا بیس کی خرابی: {str(e)}"
        }
        return False, error_msg.get(lang, error_msg["العربية"])


def save_draft_to_session(data: Dict, step: int):
    """Save partial report as draft in session state"""
    st.session_state.draft_report = {
        "data": data.copy(),
        "step": step,
        "timestamp": datetime.now(pytz.utc).isoformat()
    }
    logger.info(f"Draft saved at step {step}")


def load_draft_from_session() -> Optional[Dict]:
    """Load draft report from session state"""
    return st.session_state.get("draft_report", None)


def clear_draft():
    """Clear saved draft"""
    if "draft_report" in st.session_state:
        del st.session_state.draft_report
        logger.info("Draft cleared")


# =============================================================================
# UI COMPONENTS
# =============================================================================

def show_progress_bar(step: int, total_steps: int = 4, lang: str = "العربية"):
    """Display elegant progress indicator"""
    progress = (step / total_steps) * 100
    
    step_text = {
        "English": f"Step {step} of {total_steps}",
        "العربية": f"الخطوة {step} من {total_steps}",
        "اردو": f"مرحلہ {step} از {total_steps}"
    }
    
    complete_text = t("progress_complete", lang, pct=int(progress))
    
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress}%"></div>
        </div>
        <div class="progress-text">
            <span>{step_text.get(lang, step_text['العربية'])}</span>
            <span>{complete_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def get_exit_context() -> Dict[str, any]:
    """Analyze current state to determine exit context"""
    step = st.session_state.get("report_step", 0)
    data = st.session_state.get("complaint_data", {})
    
    if step == 0 or step == 1 and len(st.session_state.get("report_messages", [])) <= 2:
        return {
            "status": "not_started",
            "show_save": False,
            "urgency": "low"
        }
    elif step == 1 or (step == 2 and "agency_name" in data and "city" not in data):
        return {
            "status": "just_started",
            "show_save": True,
            "urgency": "low",
            "progress_pct": 25
        }
    elif step == 2 or (step == 3 and "city" in data and "complaint_text" not in data):
        return {
            "status": "partial",
            "show_save": True,
            "urgency": "medium",
            "progress_pct": 50
        }
    elif step == 3 or (step == 4 and "complaint_text" in data):
        return {
            "status": "almost_complete",
            "show_save": True,
            "urgency": "high",
            "progress_pct": 75
        }
    else:
        return {
            "status": "unknown",
            "show_save": True,
            "urgency": "medium"
        }


def render_exit_modal(lang: str = "العربية"):
    """Render intelligent exit confirmation modal"""
    
    context = get_exit_context()
    status = context["status"]
    
    st.markdown("""
    <style>
    .modal-overlay-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.75);
        z-index: 999998;
        backdrop-filter: blur(4px);
        animation: fadeIn 0.3s ease-out;
    }
    
    .modal-popup {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 999999;
        background: white;
        border-radius: 20px;
        padding: 2.5rem;
        max-width: 550px;
        width: 90%;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
        animation: slideInScale 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideInScale {
        from {
            opacity: 0;
            transform: translate(-50%, -48%) scale(0.9);
        }
        to {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="modal-overlay-backdrop"></div>', unsafe_allow_html=True)
    
    if status == "not_started":
        st.markdown(f"""
        <div class="modal-popup">
            <div class="modal-popup-icon">👋</div>
            <div class="modal-popup-title">{t("modal_return_chat", lang)}</div>
            <div class="modal-popup-text">
                {t("modal_not_started_desc", lang)}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(t("modal_yes_return", lang), use_container_width=True, key="modal_yes"):
                st.session_state.app_mode = "chat"
                st.session_state.report_messages = []
                st.session_state.report_step = 0
                st.session_state.complaint_data = {}
                st.session_state.show_exit_modal = False
                clear_draft()
                st.rerun()
        with col2:
            if st.button(t("modal_stay_file", lang), use_container_width=True, type="primary", key="modal_no"):
                st.session_state.show_exit_modal = False
                st.rerun()
    
    elif status == "just_started":
        st.markdown(f"""
        <div class="modal-popup">
            <div class="modal-popup-icon">⚠️</div>
            <div class="modal-popup-title">{t("modal_exit_title", lang)}</div>
            <div class="modal-popup-text">
                {t("exit_just_started", lang)}
            </div>
            <div class="modal-progress-box">
                <strong>{t("current_progress", lang)}: {context['progress_pct']}%</strong>
                <div class="modal-progress-bar-container">
                    <div class="modal-progress-bar-fill" style="width: {context['progress_pct']}%; background: #3b82f6;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button(t("modal_save_draft", lang), use_container_width=True, key="modal_save"):
                save_draft_to_session(st.session_state.complaint_data, st.session_state.report_step)
                st.session_state.app_mode = "chat"
                st.session_state.report_messages = []
                st.session_state.report_step = 0
                st.session_state.complaint_data = {}
                st.session_state.show_exit_modal = False
                st.success(t("draft_saved_success", lang))
                time.sleep(1.5)
                st.rerun()
        with col2:
            if st.button(t("modal_discard_exit", lang), use_container_width=True, type="secondary", key="modal_discard"):
                st.session_state.app_mode = "chat"
                st.session_state.report_messages = []
                st.session_state.report_step = 0
                st.session_state.complaint_data = {}
                st.session_state.show_exit_modal = False
                clear_draft()
                st.rerun()
        with col3:
            if st.button(t("modal_continue", lang), use_container_width=True, type="primary", key="modal_no"):
                st.session_state.show_exit_modal = False
                st.rerun()
    
    elif status in ["partial", "almost_complete"]:
        urgency_emoji = "🚨" if status == "almost_complete" else "⚠️"
        urgency_color = "#dc2626" if status == "almost_complete" else "#f59e0b"
        
        exit_message = t("exit_partial" if status == "partial" else "exit_almost_complete", lang)
        
        st.markdown(f"""
        <div class="modal-popup" style="border: 3px solid {urgency_color};">
            <div class="modal-popup-icon">{urgency_emoji}</div>
            <div class="modal-popup-title">{t("modal_significant_progress", lang)}</div>
            <div class="modal-popup-text">
                {exit_message}
            </div>
            <div class="modal-progress-box">
                <strong>{t("current_progress", lang)}: {context['progress_pct']}%</strong>
                <div class="modal-progress-bar-container">
                    <div class="modal-progress-bar-fill" style="width: {context['progress_pct']}%; background: {urgency_color};"></div>
                </div>
            </div>
            <div class="modal-popup-text" style="color: {urgency_color}; font-weight: 700; margin-top: 1rem;">
                {t("modal_important", lang)}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button(t("modal_save_and_exit", lang), use_container_width=True, type="primary", key="modal_save"):
                save_draft_to_session(st.session_state.complaint_data, st.session_state.report_step)
                st.session_state.app_mode = "chat"
                st.session_state.report_messages = []
                st.session_state.report_step = 0
                st.session_state.complaint_data = {}
                st.session_state.show_exit_modal = False
                st.success(t("draft_saved_resume", lang))
                time.sleep(1.5)
                st.rerun()
        with col2:
            if st.button(t("modal_discard_progress", lang), use_container_width=True, type="secondary", key="modal_discard"):
                if st.session_state.get("confirm_discard_modal", False):
                    st.session_state.app_mode = "chat"
                    st.session_state.report_messages = []
                    st.session_state.report_step = 0
                    st.session_state.complaint_data = {}
                    st.session_state.show_exit_modal = False
                    st.session_state.confirm_discard_modal = False
                    clear_draft()
                    st.info(t("progress_discarded", lang))
                    time.sleep(1)
                    st.rerun()
                else:
                    st.session_state.confirm_discard_modal = True
                    st.rerun()
        with col3:
            if st.button(t("modal_continue_filing", lang), use_container_width=True, type="primary", key="modal_no"):
                st.session_state.show_exit_modal = False
                st.rerun()
        
        if st.session_state.get("confirm_discard_modal", False):
            st.warning(t("modal_confirm_discard", lang))


def render_draft_resume_prompt(lang: str = "العربية"):
    """Show prompt to resume from saved draft"""
    draft = load_draft_from_session()
    if not draft:
        return
    
    step = draft.get("step", 0)
    data = draft.get("data", {})
    
    progress_items = []
    if "agency_name" in data:
        progress_items.append(t("draft_agency", lang, name=data['agency_name']))
    if "city" in data:
        progress_items.append(t("draft_city", lang, city=data['city']))
    if "complaint_text" in data:
        preview = data['complaint_text'][:80] + "..." if len(data['complaint_text']) > 80 else data['complaint_text']
        progress_items.append(t("draft_details", lang, preview=preview))
    
    progress_text = "<br>".join(progress_items)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                border-left: 4px solid #f59e0b; 
                border-radius: 12px; 
                padding: 1.5rem; 
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);">
        <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
            <span style="font-size: 2rem; margin-right: 0.5rem;">💾</span>
            <h3 style="margin: 0; color: #92400e;">{t("draft_found_title", lang)}</h3>
        </div>
        <p style="color: #78350f; margin-bottom: 1rem;">
            {t("draft_found_desc", lang)}
        </p>
        <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            {progress_text}
        </div>
        <p style="color: #92400e; font-size: 0.9rem; margin: 0;">
            {t("draft_saved_at", lang, step=step)}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button(t("resume_draft", lang), use_container_width=True, type="primary", key="resume_draft"):
            st.session_state.complaint_data = data.copy()
            st.session_state.report_step = step
            
            st.session_state.report_messages = [
                {"role": "assistant", "content": t("resuming_draft", lang)}
            ]
            
            if "agency_name" in data:
                st.session_state.report_messages.append({
                    "role": "assistant", 
                    "content": t("report_agency_recorded", lang, name=data['agency_name'])
                })
            if "city" in data:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": t("report_location_recorded", lang, city=data['city'])
                })
            if "complaint_text" in data:
                preview = data['complaint_text'][:150] + "..." if len(data['complaint_text']) > 150 else data['complaint_text']
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": f"✅ <strong>{t('draft_details', lang, preview=preview)}</strong>"
                })
            
            if step == 1:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": t("report_step_1", lang)
                })
            elif step == 2:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": t("report_step_2", lang)
                })
            elif step == 3:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": t("report_step_3", lang)
                })
            elif step == 4:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": t("report_step_4", lang)
                })
            
            clear_draft()
            st.success(t("draft_restored", lang))
            time.sleep(1)
            st.rerun()
    
    with col2:
        if st.button(t("start_fresh", lang), use_container_width=True, type="secondary", key="discard_draft"):
            clear_draft()
            st.info(t("draft_discarded", lang))
            time.sleep(1)
            st.rerun()


# =============================================================================
# MAIN REPORT BOT INTERFACE
# =============================================================================

def render_report_bot():
    """Render the enhanced secure report bot interface with multi-language support"""
    
    # Get current language from session state (default to Arabic)
    lang = st.session_state.get("language", "العربية")
    
    # Check for saved draft first
    draft = load_draft_from_session()
    if draft and st.session_state.get("report_step", 0) == 0:
        render_draft_resume_prompt(lang)
        return
    
    # Initialize session state for report flow
    if "report_messages" not in st.session_state:
        st.session_state.report_messages = []
        st.session_state.report_step = 0
        st.session_state.complaint_data = {}
        st.session_state.report_last_lang = None
    
    # Initialize LLM manager
    if "llm_manager" not in st.session_state:
        st.session_state.llm_manager = RLLMManager()

    # Get database clients
    supabase_client = get_supabase_client()
    db_manager = st.session_state.get("db_manager", None)
    
    # Initial welcome messages
    if st.session_state.report_step == 0 or st.session_state.get("report_last_lang") != lang:
        st.session_state.report_messages = [
            {
                "role": "assistant",
                "content": t("report_welcome", lang)
            },
            {
                "role": "assistant",
                "content": t("report_step_1", lang)
            }
        ]
        st.session_state.report_step = 1
        st.session_state.report_last_lang = lang
    # Handle language change during active session
    elif st.session_state.get("report_last_lang") != lang and len(st.session_state.report_messages) <= 2:
        st.session_state.report_messages = [
            {
                "role": "assistant",
                "content": t("report_welcome", lang)
            },
            {
                "role": "assistant",
                "content": t("report_step_1", lang)
            }
        ]
        st.session_state.report_last_lang = lang
    
    # Show progress bar
    if st.session_state.report_step > 0:
        show_progress_bar(st.session_state.report_step, lang=lang)
    
    # Display chat history
    for message in st.session_state.report_messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(
                    f'<div class="bot-message">{message["content"]}</div>', 
                    unsafe_allow_html=True
                )
            else:
                st.markdown(message["content"])
    
    # Chat input with validation flow
    if prompt := st.chat_input(t("chat_input_placeholder", lang), key="report_chat_input"):
        step = st.session_state.report_step
        
        # Add user message to chat
        st.session_state.report_messages.append({
            "role": "user", 
            "content": prompt
        })
        
        # Show typing indicator
        with st.chat_message("assistant"):
            typing_placeholder = st.empty()
            typing_placeholder.markdown("🤔 ...", unsafe_allow_html=True)
            time.sleep(0.3)
            
            # Validate input with LLM
            validation = st.session_state.llm_manager.validate_user_input_llm(step, prompt)
            typing_placeholder.empty()
        
        # Handle validation failure
        if not validation.get("is_valid", False):
            feedback = validation.get('feedback', 'Invalid input. Please try again.')
            st.session_state.report_messages.append({
                "role": "assistant",
                "content": t("report_validation_error", lang, feedback=feedback)
            })
            st.rerun()
            return
        
        # Process valid input based on current step
        data = st.session_state.complaint_data
        
        if step == 1:  # Agency name
            data["agency_name"] = prompt
            st.session_state.report_messages.append({
                "role": "assistant",
                "content": t("report_agency_recorded", lang, name=prompt) + "<br><br>" + t("report_step_2", lang)
            })
            st.session_state.report_step = 2
            
        elif step == 2:  # City location
            data["city"] = prompt
            st.session_state.report_messages.append({
                "role": "assistant",
                "content": t("report_location_recorded", lang, city=prompt) + "<br><br>" + t("report_step_3", lang)
            })
            st.session_state.report_step = 3
            
        elif step == 3:  # Complaint details
            data["complaint_text"] = prompt
            preview = prompt[:150] + "..." if len(prompt) > 150 else prompt
            
            summary = t("report_summary", lang, 
                       agency=data['agency_name'],
                       city=data['city'],
                       details=preview)
            
            st.session_state.report_messages.append({
                "role": "assistant",
                "content": t("report_details_recorded", lang) + "<br><br>" + summary + "<br><br>" + t("report_step_4", lang)
            })
            st.session_state.report_step = 4
            
        elif step == 4:  # Final submission
            skip_words = ["skip", "تخطي", "تخطى", "چھوڑیں", "anonymous", "مجهول", "گمنام"]
            contact = "" if any(word in prompt.lower() for word in skip_words) else prompt
            
            # Submit with SQLite check and insert
            success, message = submit_complaint_to_db(
                data, 
                contact, 
                supabase_client,
                db_manager,
                lang
            )
            
            if success:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": t("report_success", lang, message=message)
                })
                st.success(t("report_submitted", lang))
                clear_draft()
                time.sleep(2)
                
                st.session_state.report_messages.clear()
                st.session_state.report_step = 0
                st.session_state.complaint_data.clear()
                st.session_state.app_mode = "chat"
            else:
                st.error(f"❌ {message}")
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": t("report_failed", lang, message=message)
                })
                st.rerun()
                return
        
        st.rerun()
    
    # Enhanced Sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"### {t('secure_reporting', lang)}")
        st.markdown(t("all_encrypted", lang))
        
        # Show current progress
        context = get_exit_context()
        if context["status"] != "not_started":
            progress_pct = context.get("progress_pct", 0)
            st.markdown(f"""
            <div style="background: #f3f4f6; padding: 0.75rem; border-radius: 8px; margin: 1rem 0;">
                <strong>{t("current_progress", lang)}</strong>
                <div style="background: #e5e7eb; height: 6px; border-radius: 3px; margin-top: 0.5rem;">
                    <div style="background: #3b82f6; height: 100%; width: {progress_pct}%; border-radius: 3px;"></div>
                </div>
                <small style="color: #6b7280;">{t("progress_complete", lang, pct=progress_pct)}</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        if st.button(t("exit_reporting", lang), use_container_width=True, type="secondary"):
            st.session_state.show_exit_modal = True
            st.rerun()
        
        # Quick save draft button
        if context.get("show_save", False) and context["status"] not in ["not_started"]:
            if st.button(t("quick_save", lang), use_container_width=True, key="quick_save"):
                save_draft_to_session(st.session_state.complaint_data, st.session_state.report_step)
                st.success(t("draft_saved", lang))
                time.sleep(1)


# =============================================================================
# MAIN APPLICATION ENTRY POINT
# =============================================================================

def main():
    """Main application controller"""
    
    # Initialize app mode
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "chat"
    if "show_exit_modal" not in st.session_state:
        st.session_state.show_exit_modal = False
    
    # Get current language
    lang = st.session_state.get("language", "العربية")
    
    # Set page config
    st.set_page_config(
        page_title=t("report_page_title", lang),
        page_icon="🛡️",
        layout="wide"
    )

    # Inject CSS with RTL support
    st.markdown(get_css_styles(lang), unsafe_allow_html=True)
    
    # Ensure Supabase is initialized
    get_supabase_client()
    
    # Render elegant header
    st.markdown(f"""
    <div class="header-container">
        <h1 class="main-title">
            🛡️ <span class="title-highlight">{t("report_main_title", lang)}</span>
        </h1>
        <p class="subtitle">{t("report_subtitle", lang)}</p>
        <div class="header-badge">
            {t("report_badge", lang)}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show exit modal if triggered
    if st.session_state.get("show_exit_modal", False):
        render_exit_modal(lang)
    
    # Route to appropriate mode
    if st.session_state.app_mode == "report":
        render_report_bot()
    elif st.session_state.app_mode == "chat":
        st.switch_page("app.py")


if __name__ == "__main__":
    main()
