"""
LLM Manager Module
Handles OpenAI API interactions for chat and TTS with structured outputs
"""

import random
import streamlit as st
from openai import OpenAI
import io
import re
from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field
import logging
import json
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------
# Pydantic Models for Structured Outputs
# -----------------------------

class IntentClassification(BaseModel):
    """Structured output for intent detection"""
    intent: Literal["GREETING", "DATABASE", "GENERAL_HAJJ", "NEEDS_INFO"] = Field(
        description="The classified intent of the user's message"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score of the classification (0-1)"
    )
    reasoning: str = Field(
        description="Brief explanation of why this intent was chosen"
    )


class SQLQueryGeneration(BaseModel):
    """Structured output for SQL query generation"""
    sql_query: Optional[str] = Field(
        None,
        description="The generated SQL SELECT query, or None if no safe query can be generated"
    )
    query_type: Literal["simple", "aggregation", "complex", "no_sql"] = Field(
        description="Type of query generated"
    )
    filters_applied: List[str] = Field(
        default_factory=list,
        description="List of filters or conditions applied in the query"
    )
    explanation: str = Field(
        description="Human-readable explanation of what the query does"
    )
    safety_checked: bool = Field(
        description="Whether the query passed safety validation"
    )


class QuerySummary(BaseModel):
    """Structured output for query result summarization"""
    summary: str = Field(
        description="Natural language summary of the query results"
    )
  

class GreetingResponse(BaseModel):
    """Structured output for greeting responses"""
    greeting: str = Field(
        description="The friendly greeting message"
    )
    tone: Literal["formal", "casual", "warm"] = Field(
        description="Tone of the greeting"
    )
    includes_offer_to_help: bool = Field(
        description="Whether the greeting includes an offer to help"
    )
class NEEDSInfoResponse(BaseModel):
    """Structured output for needs info responses"""
    needs_info: str = Field(
        description="The message asking user for more specific information"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="List of example queries the user could try"
    )
    missing_info: List[str] = Field(
        default_factory=list,
        description="List of specific information pieces needed"
    )
    sample_query: str = Field(
        description="An example of a well-formed query"
    )
    user_lang: Literal["English", "العربية"] = Field(
        description="Language to respond in"
    )


class LLMManager:
    """Manages OpenAI API calls with error handling and rate limiting"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = self._get_client()
        self.voice_map = {
            "العربية": "onyx",  # Deeper voice for Arabic
            "English": "alloy"
        }
    
    @st.cache_resource
    def _get_client(_self):
        """Get cached OpenAI client"""
        api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("key")
        if not api_key:
            logger.error("OpenAI API key not found")
            st.warning("⚠️ OpenAI API key missing in Streamlit secrets")
            st.stop()
        return OpenAI(api_key=api_key)
    

    
    def detect_intent(self, user_input: str, language: str, context_string=None) -> Dict:
        """
        Detect user intent using LLM with structured output
        Returns: Dict with intent, confidence, and reasoning

        """
        
        
        intent_prompt = f"""
    You are a fraud-prevention assistant for Hajj pilgrims. Your task is to analyze the conversation history and current message to accurately classify the user's intent.

    SUPPORTED LANGUAGES: English, Arabic (العربية), Urdu (اردو), and code-mixed variants

    MISSION CONTEXT:
    - 415 fake Hajj offices were closed in 2025
    - 269,000+ unauthorized pilgrims were stopped
    - Your purpose: Prevent fraud and protect pilgrims through accurate intent classification

    ═══════════════════════════════════════════════════════════════════════

    CORE CLASSIFICATION PRINCIPLES:

    1. LANGUAGE DETECTION & HANDLING:
    - Automatically detect the language(s) used in the user's message
    - Support pure language inputs (English-only, Arabic-only, Urdu-only)
    - Support code-mixed inputs (e.g., Urdu-English, Arabic-English)
    - Recognize transliterated text (Roman Urdu, Arabizi)
    - Match response language to user's input language
    - Handle multilingual queries seamlessly without requiring explicit language indicators

    2. CONTEXT AWARENESS:
    - ALWAYS review the last 3-5 messages in conversation history before classifying
    - Track entity references across messages (agency names, locations, topics)
    - Resolve pronouns and demonstratives (this/that/they, یہ/وہ/ان, هذا/ذلك/هم) by searching context
    - Maintain conversation flow - treat follow-up questions as continuations
    - If a referent exists in context, do NOT mark as NEEDS_INFO
    - Build a mental model of what has been discussed to understand implicit references

    3. INTENT HIERARCHY (Apply in order):
    Step 1: Identify if message contains a GREETING pattern
        - If greeting + specific query → Classify by the specific query
        - If greeting only → GREETING
    
    Step 2: Check for DATABASE requirements
        - Does message contain specific agency identifier(s)?
        - Does message request agency-specific information?
        - Does message contain pronouns/demonstratives that resolve to agencies in context?
        - Is this a follow-up to a DATABASE conversation?
        → If YES to any → DATABASE
    
    Step 3: Evaluate for GENERAL_HAJJ applicability
        - Is the question about Hajj process, rituals, or requirements?
        - Can this be answered with general knowledge (not database lookup)?
        - Is it educational/informational about Hajj itself?
        → If YES → GENERAL_HAJJ
    
    Step 4: Check if NEEDS_INFO
        - After context review, is critical information still missing?
        - Is the query too ambiguous to classify confidently?
        - Would asking clarification genuinely help?
        → If YES → NEEDS_INFO

    4. ENTITY RECOGNITION:
    - Agency Names: Any proper noun that could be a Hajj company/office/agency
        Examples: "Royal City", "الصفا", "النور", "Divine Tours"
    - Locations: Cities, countries, regions where agencies operate
        Examples: "Riyadh", "Jeddah", "Pakistan", "London", "الرياض", "لاہور"
    - Temporal References: Dates, years, seasons related to Hajj timing
    - Service Keywords: "package", "visa", "booking", "registration", "price"
    
    When entities are detected:
    - Agency name + verification/info request → DATABASE
    - Location + agency query → DATABASE
    - General topic without specific entities → GENERAL_HAJJ

    5. PRONOUN & REFERENCE RESOLUTION:
    English: they, them, their, it, this, that, these, those
    Arabic: هم, هي, هذا, هذه, ذلك, تلك
    Urdu: یہ, وہ, ان, یہی, وہی
    
    Resolution Strategy:
    a) Scan last 3 messages for potential referents
    b) Identify most recent agency name, location, or topic mentioned
    c) If found and relevant → Assign that reference
    d) If not found → Mark as NEEDS_INFO
    e) If found but semantically unrelated → Use judgment based on query type

    6. QUERY SPECIFICITY ASSESSMENT:
    HIGH SPECIFICITY (likely DATABASE):
    - Contains proper nouns (agency/company names)
    - Asks about specific contact details, authorization, location
    - Requests lists with clear geographic/categorical constraints
    - Comparative queries between named entities
    
    MEDIUM SPECIFICITY (context-dependent):
    - Contains industry terms but no specific entities ("agencies in...", "companies that...")
    - Asks about processes involving agencies ("how to book", "package includes")
    - Uses pronouns or demonstratives without clear referents
    
    LOW SPECIFICITY (likely GENERAL_HAJJ or NEEDS_INFO):
    - Abstract questions about Hajj itself
    - Requests for general advice, tips, procedures
    - Educational queries about rituals, requirements
    - Vague or incomplete statements

    7. GREETING DETECTION PATTERNS:
    Lexical indicators:
    - Salutation words: hi, hello, hey, salam, assalam, مرحبا, ہیلو, آداب
    - Welfare inquiries: how are you, كيف حالك, کیا حال ہے
    - Time-based greetings: good morning/evening, صباح الخير, صبح بخیر
    
    Functional indicators:
    - Meta-questions about bot capabilities: "what can you do", "who made you"
    - Conversation openers without substantive content
    - Social pleasantries
    
    Rule: If greeting is paired with a substantive query, prioritize the query's classification

    8. DATABASE vs GENERAL_HAJJ DISTINCTION:
    DATABASE indicators:
    - Proper nouns (agency names)
    - Verification/authorization language: "authorized", "legitimate", "approved", "مرخص", "منظور شدہ", "معتمد"
    - Request for specific operational details: address, phone, email, license
    - Comparative analysis between specific entities
    - List requests with geographic specificity
    
    GENERAL_HAJJ indicators:
    - Abstract concepts: rituals, spirituality, rules
    - Process questions: "how to", "what is", "when do"
    - Educational content: requirements, documents, preparations
    - Health/safety advice
    - Cost discussions without specific agency mention
    - Temporal information about Hajj season itself

    9. NEEDS_INFO DECISION CRITERIA:
    Mark as NEEDS_INFO only when:
    - Query contains no identifiable entities AND context provides none
    - Ambiguous pronouns with no clear referent in last 5 messages
    - Request is so vague that multiple interpretations are equally plausible
    - Critical parameters are missing (which agency? which location? which aspect?)
    
    Do NOT mark as NEEDS_INFO when:
    - Context clearly indicates the referent
    - Query is general enough to answer with GENERAL_HAJJ knowledge
    - A reasonable assumption can be made from conversation flow
    - User is providing requested information (follow-up to a NEEDS_INFO response)

    10. CODE-MIXING & TRANSLITERATION HANDLING:
        - Recognize Roman Urdu (Urdu written in Latin script): "kya", "hai", "mujhe"
        - Recognize Arabizi (Arabic in Latin): "salam", "marhaba", "shukran"
        - Handle mixed scripts: "Royal City کی تصدیق", "check شركة الإيمان"
        - Parse mixed vocabulary: "Mujhe verify karna hai", "Agency ka address"
        - Treat code-mixed as natural - don't penalize or require pure language

    11. CONFIDENCE SCORING GUIDELINES:
        0.95-1.0: Explicit entity + clear intent + no ambiguity
                "Is Royal City Hajj authorized?" → DATABASE (1.0)
        
        0.85-0.94: Clear intent with minor ambiguity or implicit reference
                [Context: Royal City] "Are they authorized?" → DATABASE (0.9)
        
        0.70-0.84: Intent identifiable but requires context interpretation
                "Tell me about agencies in Riyadh" → DATABASE (0.75)
        
        0.50-0.69: Multiple plausible interpretations, context helps narrow
                "Hajj packages" → Could be DATABASE or GENERAL (0.6)
        
        0.00-0.49: Highly ambiguous, insufficient information
                "Tell me more" → NEEDS_INFO (0.3)

    12. QUALITY CONTROL CHECKS:
        Before finalizing classification, verify:
        □ Did I check conversation context thoroughly?
        □ Did I attempt to resolve all pronouns and references?
        □ Is there a more specific classification than NEEDS_INFO?
        □ Did I consider code-mixing and transliteration?
        □ Is my confidence score justified by the evidence?
        □ Would a native speaker of the user's language agree with my interpretation?

    ═══════════════════════════════════════════════════════════════════════

    INTENT CATEGORIES (Brief Summary):

    1️⃣ GREETING: Social pleasantries, bot capability questions, conversation starters
    2️⃣ DATABASE: Agency verification, authorization checks, contact info, lists, specific entity queries
    3️⃣ GENERAL_HAJJ: Rituals, requirements, procedures, health, costs (general), spiritual guidance
    4️⃣ NEEDS_INFO: Insufficient information after context review, unresolvable ambiguity

    ═══════════════════════════════════════════════════════════════════════

    CONVERSATION CONTEXT:
    {context_string}

    CURRENT MESSAGE: 
    {user_input}

    ═══════════════════════════════════════════════════════════════════════

    CLASSIFICATION TASK:

    Analyze the message using the principles above. Provide:

    1. INTENT: [GREETING | DATABASE | GENERAL_HAJJ | NEEDS_INFO]

    2. CONFIDENCE: [0.0 - 1.0]

    3. REASONING: 
    - Detected language(s)
    - Key linguistic indicators (words, phrases, patterns)
    - Entities identified (if any)
    - Context elements used (if any)
    - References resolved (if any)
    - Why other categories were ruled out
    - Specific principle(s) that led to this classification

    ═══════════════════════════════════════════════════════════════════════

    CRITICAL REMINDERS:
    - Generalize from patterns, not just memorized examples
    - Adapt to natural language variation and creativity
    - Context is paramount - always check before deciding NEEDS_INFO
    - Code-mixing is normal - handle it seamlessly
    - Confidence reflects genuine uncertainty, not over-confidence
    - User's language = Your response language
    """
        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You classify user intents for a Hajj agency verification system."},
                    {"role": "user", "content": intent_prompt}],
                response_format=IntentClassification,
                temperature=0
            )
            
            intent_data = response.choices[0].message.parsed
            logger.info(f"Intent detected: {intent_data.intent} (confidence: {intent_data.confidence})")
            
            return {
                "intent": intent_data.intent,
                "confidence": intent_data.confidence,
                "reasoning": intent_data.reasoning
            }
            
        except Exception as e:
            logger.error(f"Structured intent detection failed: {e}")
            # Fallback to heuristics
            return self._fallback_intent_detection(user_input)
    
    def _fallback_intent_detection(self, user_input: str) -> Dict:
        """Fallback intent detection using heuristics"""
        ui = user_input.lower()
        
        if any(g in ui for g in ["hello", "hi", "salam", "السلام", "مرحبا"]):
            intent = "GREETING"
        elif any(k in ui for k in ["company", "agency", "معتمد", "شركات", "authorized", "وكالة"]):
            # Check if query is too vague
            if len(ui.split()) < 4 and not any(specific in ui for specific in ["royal", "alhuda", "مكة", "جدة", "riyadh"]):
                intent = "NEEDS_INFO"
            else:
                intent = "DATABASE"
        else:
            intent = "GENERAL_HAJJ"
        
        return {
            "intent": intent,
            "confidence": 0.7,
            "reasoning": "Determined by keyword matching (fallback)"
        }
        
    def generate_greeting(self, user_input: str, language: str, context_string=None) -> str:
        """Generate natural greeting response with structured output"""
        is_arabic = language == "العربية"
        context_string = context_string if context_string else ""
        
        system_prompt = f"""You are a professional Hajj verification assistant dedicated to protecting pilgrims from fraud and scams.

Core Mission: Help users verify if Hajj agencies are officially authorized by the Ministry of Hajj and Umrah.

Response Guidelines:
1. **Greetings**: When user greets you (hello, hi, السلام عليكم, السلام علیکم, etc.):
   - Acknowledge their greeting warmly but briefly
   - Immediately state your purpose: helping verify authorized Hajj agencies
   - Keep it to 2-3 sentences maximum
   - Use 1-2 emojis appropriately (for text mode only)

2. **"How are you" questions**: ONLY respond to "how are you" if the user explicitly asks:
   - Keep it brief (e.g., "I'm here and ready to help!")
   - Immediately pivot to offering assistance with Hajj verification

3. **Developer questions**: If asked about your developer/creator:
   - Vary your response naturally while conveying: "Created by three dedicated developers committed to making Hajj agency verification safe and accessible for all pilgrims."
   - Keep the tone professional and mission-focused

4. **Language Detection**:
   - Respond in **Arabic** if user input contains ANY Arabic script (العربية)
   - Respond in **Urdu** if user input contains ANY Urdu-specific text or Pakistani context (اردو)
   - Respond in **English** for all other cases
   - Match the user's formality level
   - Note: Arabic and Urdu share the same script but have different vocabulary and grammar

5. **Focus**: 
   - Always center responses around Hajj agency verification
   - Be helpful and professional, not overly casual
   - Don't volunteer information about your state/feelings unless directly asked


User input: {user_input}
Context: {context_string}

Generate a focused, professional response that helps protect pilgrims from fraud."""

        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                    
                ],
                response_format=GreetingResponse,
                temperature=0.7
            )
            
            greeting_data = response.choices[0].message.parsed
            logger.info(f"Greeting generated with tone: {greeting_data.tone}")
            return greeting_data.greeting
            
        except Exception as e:
            logger.error(f"Structured greeting generation failed: {e}")
            return "Hello! 👋 How can I help you today?" if not is_arabic else "السلام عليكم! 👋 كيف يمكنني مساعدتك؟"
    
    def generate_general_answer(self, user_input: str, language: str, context_string=None) -> str:
        """Generate answer for general Hajj questions"""
        system_prompt = f"""You are an expert Hajj assistant with comprehensive knowledge of Hajj rituals, regulations, and pilgrim safety.

IMPORTANT: You must ALWAYS respond in the SAME language as the user's question:
- If user writes in Arabic (العربية) → Respond completely in Arabic
- If user writes in English → Respond completely in English  
- If user writes in Urdu (اردو) → Respond completely in Urdu
- Detect the language automatically from the user's input

CORE EXPERTISE - YOU HAVE DEEP KNOWLEDGE OF:

📋 HAJJ FUNDAMENTALS:
- The 5 pillars of Hajj and their sequence (Ihram, Tawaf, Sa'i, Wuquf at Arafat, Stoning, Animal Sacrifice, Tawaf al-Ifadah)
- Difference between Hajj types: Tamattu', Ifrad, and Qiran
- Detailed rituals for each day (8th-13th Dhul Hijjah)
- Miqat locations and Ihram requirements
- Prohibited actions during Ihram
- Tawaf al-Qudum, Tawaf al-Ifadah, and Tawaf al-Wada
- Sa'i between Safa and Marwa (7 rounds)
- Staying at Muzdalifah and collecting pebbles
- Jamarat stoning (small, middle, large - Aqaba first on 10th)

🏛️ HOLY SITES & LOCATIONS:
- Masjid al-Haram and Ka'bah details
- Mina tent city layout and facilities
- Arafat (Jabal al-Rahmah) and its significance
- Muzdalifah procedures
- Jamarat Bridge structure and timing
- Miqat boundaries for different regions

📝 REQUIREMENTS & DOCUMENTATION (2024-2025):
- Saudi Arabia's Hajj visa requirements
- Age restrictions and health requirements
- Vaccination requirements (Meningitis, COVID-19 policies)
- Mandatory Hajj package through authorized agents
- Electronic registration systems (Nusuk platform)
- Passport validity (minimum 6 months)
- Mahram requirements for women (recent policy changes)
- Country-specific quotas and lottery systems

💰 COSTS & PACKAGES (2024-2025):
- Typical Hajj package price ranges by country
- What's included in official packages (accommodation, transport, meals)
- Accommodation tiers (close to Haram vs. further locations)
- Additional costs to budget for
- Payment schedules and deposit requirements

🏥 HEALTH & SAFETY:
- Required vaccinations and health certificates
- Heat safety (temperatures exceeding 40-50°C)
- Hydration and heat stroke prevention
- Crowd management and stampede safety
- Medical facilities in Makkah, Mina, and Arafat
- Emergency numbers and hospital locations
- Common health issues (dehydration, exhaustion, respiratory infections)
- Medication and first aid recommendations

🚨 AGENCY SAFETY AWARENESS:

**Important Note About Hajj Agencies:**
We have a specialized agency verification service available through our system. When users ask about specific agencies or need verification, inform them that:

- Our platform has an agency verification feature
- They should verify ANY agency before making payments
- We can help them check if agencies are authorized by the Ministry of Hajj and Umrah



How to Refer to Verification (in user's language):

**English:**
"We have an agency verification service that can check if this agency is officially authorized. You may want to use that feature to confirm their credentials before proceeding."

**Arabic:**
"لدينا خدمة للتحقق من تراخيص وكالات الحج. يمكنك استخدام هذه الخدمة للتأكد من أن الوكالة مرخصة رسمياً من وزارة الحج والعمرة قبل الدفع."

**Urdu:**
"ہمارے پاس ایجنسی کی تصدیق کی سروس ہے جو یہ چیک کر سکتی ہے کہ آیا یہ ایجنسی سرکاری طور پر مجاز ہے۔ ادائیگی سے پہلے ان کی اسناد کی تصدیق کے لیے آپ اس خصوصیت کا استعمال کر سکتے ہیں۔"

Common Hajj Scam Warning Signs to Educate Users:
- Unrealistically cheap packages (significantly below market rate)
- Agencies asking for full payment upfront without proper contracts
- No official license number provided
- Pressure tactics ("limited spots", "book now or lose it")
- No physical office address or verifiable location
- Promises that seem too good to be true
- No clear refund or cancellation policy
- Poor or no online presence/reviews

Always Advise (translate to user's language):
- NEVER pay an agency without verification
- Check official Ministry of Hajj and Umrah registrations
- Use our verification service before making any commitments
- Get everything in writing with clear terms

📱 OFFICIAL RESOURCES:
- Nusuk platform (nusuk.sa) - official Saudi Hajj portal
- Ministry of Hajj and Umrah website (haj.gov.sa)
- Tawakkalna app requirements
- Official helpline numbers
- Country-specific Hajj authority contacts

🌍 COUNTRY-SPECIFIC INFO:
- Different countries have different authorized agent lists
- Quota systems vary by country (Pakistan, India, Indonesia, Bangladesh, etc.)
- Some countries use lottery systems
- Official Hajj committees per country
- Special considerations for South Asian pilgrims (Pakistan, India, Bangladesh)

⚖️ REGULATIONS & POLICIES (2024-2025):
- Electronic tracking bracelets (mandatory)
- Designated routes and timing restrictions
- Ban on repeat Hajj within 5 years (for some nationalities)
- Environmental regulations (plastic bans, waste management)
- Photography/video restrictions in certain areas
- Traffic and transportation regulations

RESPONSE GUIDELINES:
- CRITICAL: Always respond in the SAME language as the user's question
- Speak naturally and compassionately - pilgrims are undertaking a sacred journey
- Provide practical, actionable guidance
- Use conversational, flowing language
- When users mention agencies, gently remind them about our verification service
- Don't try to verify agencies yourself - just inform users the service exists
- Focus on education about Hajj practices and safety awareness
- If discussing costs or packages, mention that verification should be their first step
- Be culturally sensitive to South Asian, Arab, and other Muslim communities

USER QUESTION: {user_input}

{f'RELEVANT CONTEXT: {context_string}' if context_string else ''}

YOUR ROLE:
- DETECT user's language and respond in the SAME language (Arabic/English/Urdu)
- Provide comprehensive Hajj guidance and information
- Educate about scam warning signs
- Inform users about our agency verification service (but don't perform verification)
- Keep pilgrims safe through knowledge and awareness
- Answer questions about rituals, requirements, health, safety, and logistics

WHAT YOU DON'T DO:
- Don't verify agencies yourself (another model handles that)
- Don't claim to have access to verification databases
- Don't provide definitive "yes/no" on whether agencies are legitimate
- Don't mix languages in your response (pick ONE language based on user's question)

WHAT YOU DO:
- Educate about what makes agencies trustworthy
- Inform users that verification service exists in our platform
- Provide comprehensive Hajj knowledge in user's preferred language
- Keep responses natural and conversational
- Protect pilgrims through information and awareness
- Respond completely in Arabic, English, or Urdu based on user's question

LANGUAGE DETECTION EXAMPLES:
- "ما هي خطوات الحج؟" → Respond completely in Arabic
- "What are the steps of Hajj?" → Respond completely in English
- "حج کے مراحل کیا ہیں؟" → Respond completely in Urdu
- "Tell me about Hajj agencies" → Respond completely in English
- "ایجنسی کی تصدیق کیسے کریں؟" → Respond completely in Urdu

Provide helpful, accurate information that keeps pilgrims safe, informed, and aware of available resources - ALL IN THE USER'S LANGUAGE."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                temperature=0.6,
                max_tokens=400
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"General answer generation failed: {e}")
            return "I encountered an error. Please try rephrasing your question."
    
    def generate_sql(self, user_input: str, language: str ,context_string= None) -> Optional[Dict]:
        """
        Generate SQL query from user input with structured output
        Returns: Dict with sql_query, query_type, filters, explanation, safety_checked
        """
        sql_prompt = self._get_sql_system_prompt(language, context_string) + f"\n\nUser Question: {user_input}"
        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a SQL expert that generates safe queries for a Hajj agency database."},
                    {"role": "user", "content": sql_prompt},
        
                ],
                response_format=SQLQueryGeneration,
                temperature=0
            )
            
            sql_data = response.choices[0].message.parsed
            
            logger.info(f"SQL generated - Type: {sql_data.query_type}, Safety: {sql_data.safety_checked}")
            logger.info(f"Explanation: {sql_data.explanation}")
            
            if sql_data.sql_query and sql_data.safety_checked:
                return {
                    "sql_query": sql_data.sql_query,
                    "query_type": sql_data.query_type,
                    "filters": sql_data.filters_applied,
                    "explanation": sql_data.explanation
                }
            else:
                logger.warning(f"No safe SQL generated: {sql_data.explanation}")
                return None
            
        except Exception as e:
            logger.error(f"Structured SQL generation failed: {e}")
            return None
    
    def generate_summary(self, user_input: str, language: str, row_count: int, sample_rows: List[Dict], context_string=None) -> Dict:
        """
        Generate natural, friendly, and structured summary of query results.
        Adds assistant-like sentences and recommendations based on intent.
        """
        data_preview= ""
        if row_count>0:
            data_preview = json.dumps(sample_rows[:50], ensure_ascii=False)

        summary_prompt = f"""
You are a multilingual safety-aware assistant for Hajj and Umrah pilgrims.  
Your goal is to convert database results into natural spoken responses that sound human, trustworthy, and culturally appropriate — not like reading structured data.

═══════════════════════════════════════════════════════════════
🧭 INPUT CONTEXT
User question: {user_input}
Database results: {data_preview}
Reference context: {context_string}
═══════════════════════════════════════════════════════════════

🎯 OBJECTIVE
Generate a natural, voice-friendly spoken answer summarizing relevant agency information, ensuring:
- Polite, reassuring tone
- Correct language and script
- No URLs or external links
- Accurate safety and authorization warnings
- Smooth, coherent flow between multiple agencies

═══════════════════════════════════════════════════════════════

🗣️ LANGUAGE RULES

Supported languages: Arabic, English, Urdu  
Always detect and respond entirely in the user's language.

| Language | Agency name field | Script direction |
|-----------|------------------|------------------|
| Arabic    | name_ar          | RTL              |
| Urdu      | name_ar          | RTL              |
| English   | name             | LTR              |

Translate all other text (city, description, rating phrases, closing questions) into the same language.

═══════════════════════════════════════════════════════════════

💬 RESPONSE PATTERN

**Structure Pattern (for each response):**
1️⃣ Opening acknowledgment → mention city or scope  
2️⃣ Core description → present 1–3 agencies naturally  
3️⃣ Smooth transitions → between agencies using discourse connectors  
4️⃣ Safety note → based on authorization status  
5️⃣ Closing question → invite next action politely  

**Behavioral Patterns:**
- Use sentence connectors (“and”, “also”, “meanwhile”, “another option”) instead of list bullets.
- Speak as if guiding or reassuring the listener, not announcing data.
- For ratings, use numeric format: “4.6 ⭐ from 213 reviews”.
- Avoid repetitive sentence openings — vary phrasing with each agency.

═══════════════════════════════════════════════════════════════

⚠️ SAFETY AND AUTHORIZATION

Pattern Rules:
- If authorized → calm, reassuring tone (“authorized”, “officially registered”, “trustworthy”).  
- If unauthorized → clear warning tone (“not authorized”, “may expose to risk”, “avoid using”).  
- Do not include ratings or positive details for unauthorized agencies.  
- Never provide URLs, Google Maps links, or promotional phrases.  

═══════════════════════════════════════════════════════════════

🧾 LANGUAGE-SPECIFIC PATTERNS

**Arabic Patterns**
- Use phrases conveying reassurance: “يمكنك التواصل بثقة”, “وكالة معتمدة”, “آمنة ومعتمدة”.
- Avoid long lists; combine agencies with connectors: “وهناك أيضاً”, “كما يمكنك العثور على”.
- Use numerals (e.g., “4.8 ⭐ من 120 تقييم”).

**Urdu Patterns**
- Use formal tone with “آپ”.
- Avoid English insertions unless necessary (e.g., brand names).
- Numeric values only (“4.7 ⭐”, not “چار اعشاریہ سات”).
- End with polite closings: “کیا آپ مزید اختیارات چاہیں گے؟”, “کیا میں رابطے کی تفصیلات فراہم کروں؟”

**English Patterns**
- Use friendly connectors: “You’ll also find”, “Another trusted option”, “There’s also”.
- Keep sentences short for TTS clarity.
- Use polite closings: “Would you like more options?”, “Shall I share their contact info?”

═══════════════════════════════════════════════════════════════

🚫 CONTENT RESTRICTIONS

Always exclude:
- Any URLs, email addresses, or phone numbers unless explicitly requested.
- `google_maps_link` or location URLs.
- Unverified claims or promotions.
- Unnatural list formatting or markdown.

═══════════════════════════════════════════════════════════════

🧩 FALLBACK & ZERO-RESULTS PATTERN

If no results:
- Respond empathetically and suggest next step.
  - English: “I couldn’t find matching agencies. Would you like me to check another city?”
  - Arabic: “لم أجد وكالات مطابقة. هل ترغب أن أبحث في مدينة أخرى؟”
  - Urdu: “مجھے کوئی مطابقت رکھنے والی ایجنسی نہیں ملی۔ کیا آپ کسی اور شہر میں تلاش کرنا چاہیں گے؟”

═══════════════════════════════════════════════════════════════

✅ FINAL VALIDATION CHECKLIST
Before finalizing:
- [ ] Entire response uses detected language
- [ ] All numbers are numeric
- [ ] No URLs or unverified info
- [ ] Authorization phrasing matches safety rules
- [ ] Tone natural and speech-friendly
- [ ] Ends with a polite, context-aware question
- [ ] Arabic/Urdu formatted RTL

═══════════════════════════════════════════════════════════════

Now output a **natural spoken response** following the above patterns.  
Keep it concise, warm, safe, and optimized for voice playback.
"""

       
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant summarizing Hajj agency data in a friendly and structured way."},
                    {"role": "user", "content": summary_prompt}
                ],
                response_format=QuerySummary,
                temperature=0.6
            )

            summary_data = response.choices[0].message.parsed

            final_summary = f"{summary_data.summary}"
            logger.info("Summary generated successfully.")


            return {
                "summary": final_summary,
            }

        except Exception as e:
            logger.error(f"Structured summary generation failed: {e}")
            return {
                "summary": f"📊 Found {row_count} matching records.",
            }

    def text_to_speech(self, text: str, language: str) -> Optional[io.BytesIO]:
        """
        Convert text to speech using OpenAI TTS
        Returns BytesIO audio ready for st.audio
        """
        voice = self.voice_map.get(language, "alloy")
        
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="mp3"
            )
            
            audio_bytes = io.BytesIO(response.content)
            audio_bytes.seek(0)
            return audio_bytes
            
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return None
    
    @staticmethod
    def _get_sql_system_prompt(language: str, context_string=None) -> str:
        """Get SQL generation system prompt"""
        return f"""
    You are a multilingual SQL fraud-prevention expert protecting Hajj pilgrims.

    🎯 MISSION: Generate an SQL query for database analysis on Hajj agencies.
    Do NOT generalize to world data — always query from the table 'agencies'.
    Use the CONTEXT and USER QUESTION to create a safe, accurate SQL SELECT query.
    Context: {context_string}

    TABLE STRUCTURE:
    - hajj_company_ar
    - hajj_company_en
    - formatted_address
    - city
    - country
    - email
    - contact_Info
    - rating_reviews
    - is_authorized ('Yes' or 'No')
    - google_maps_link
    - link_valid (boolean)



    --------------------------------------------
    🔍 LANGUAGE DETECTION RULES:
    1. Detect if the user's question is in Arabic, English or Urdu. And respond in the same language.
    2. Respond with SQL query **only**, no text.
    3. Keep text fragments (LIKE clauses) in both Arabic and English for robustness.
    4. translate city and country, etc if needed based on user language

    --------------------------------------------

    🚨 CRITICAL DATABASE CONTEXT:
    - 415 fake offices closed in 2025
    - 269,000+ unauthorized pilgrims stopped
    - Database mixes Arabic, English, and typos.
    - Always focus on verifying **authorization** and **agency location**, not world geography.

    --------------------------------------------
    📘 QUERY INTERPRETATION RULES:

    1. "Authorized" → add `AND is_authorized = 'Yes'`
    2. "Is X authorized?" → check `is_authorized` for company name
    3. "Number of ..." or "How many ..." → use `SELECT COUNT(*)`
    4. "Countries" or "number of countries" → use:
    - `SELECT COUNT(DISTINCT country)` if asking how many
    - `SELECT DISTINCT country` if asking for list
    - Always based on agencies table
    5. "Cities" or "number of cities" → same logic as above but for `city`
    6. Never assume or add “Saudi Arabia” unless mentioned explicitly.
    7. When user asks about “countries that have agencies” → use `DISTINCT country` from `agencies`
    8. Always return agency-related data only, not external or world data.
    9    --------------------------------------------

    🌍 LOCATION MATCHING PATTERNS:
    Use flexible LIKE and LOWER() conditions for cities/countries.
    Handle Arabic, English, and typos.

    Mecca → (city LIKE '%مكة%' OR LOWER(city) LIKE '%mecca%' OR LOWER(city) LIKE '%makkah%' OR LOWER(city) LIKE '%makka%')
    Medina → (city LIKE '%المدينة%' OR LOWER(city) LIKE '%medina%' OR LOWER(city) LIKE '%madinah%')
    Riyadh → (city LIKE '%الرياض%' OR LOWER(city) LIKE '%riyadh%' OR LOWER(city) LIKE '%ar riyadh%')
    Saudi Arabia → (country LIKE '%السعودية%' OR LOWER(country) LIKE '%saudi%' OR country LIKE '%المملكة%')
    Pakistan → (country LIKE '%باكستان%' OR LOWER(country) LIKE '%pakistan%' OR country LIKE '%پاکستان%')
    Egypt → (country LIKE '%مصر%' OR LOWER(country) LIKE '%egypt%')

    --------------------------------------------
    🏁 OUTPUT RULES:
    - Output **only** one valid SQL SELECT query.
    - If no logical SQL can be formed → output `NO_SQL`
    - Always include LIMIT 100 unless COUNT or DISTINCT is used.

    --------------------------------------------
    ✅ EXAMPLES:
📘 QUERY INTERPRETATION RULES:
...
⚙️ For company name searches:
Always normalize and deduplicate company names.
Use LOWER(TRIM()) and SELECT DISTINCT to avoid case duplicates.

    Make sure you help and understand the user



    Q: "هل شركة الهدى معتمدة؟"
    → ELECT DISTINCT hajj_company_en, hajj_company_ar, formatted_address, city, country, email, contact_Info, rating_reviews, is_authorized, google_maps_link
FROM agencies
WHERE (LOWER(TRIM(hajj_company_en)) LIKE LOWER('%alhuda%')
   OR LOWER(TRIM(hajj_company_ar)) LIKE LOWER('%الهدى%'))
LIMIT 50;
    Q: "Authorized agencies in Makkah"
    → SELECT * FROM agencies WHERE is_authorized = 'Yes' AND (city LIKE '%مكة%' OR LOWER(city) LIKE '%mecca%' OR LOWER(city) LIKE '%makkah%') LIMIT 100;

    Q: "كم عدد الشركات في المدينة؟"
    → SELECT COUNT(*) FROM agencies WHERE (city LIKE '%المدينة%' OR LOWER(city) LIKE '%medina%' OR LOWER(city) LIKE '%madinah%');

    Q: "How many countries have agencies?"
    → SELECT COUNT(DISTINCT country) FROM agencies;

    Q: "List of countries that have agencies"
    → SELECT DISTINCT country FROM agencies LIMIT 100;

    Q: "Number of authorized countries"
    → SELECT COUNT(DISTINCT country) FROM agencies WHERE is_authorized = 'Yes';

    Q: "Countries with authorized agencies"
    → SELECT DISTINCT country FROM agencies WHERE is_authorized = 'Yes' LIMIT 100;

    Q: "Show all cities where agencies exist"
    → SELECT DISTINCT city FROM agencies LIMIT 100;
    """
    
    @staticmethod
    def _extract_sql_from_response(response_text: str) -> Optional[str]:
        """Extract SQL query from LLM response"""
        if not response_text:
            return None
        
        # Try code blocks
        code_block_pattern = r'```(?:sql)?\s*(SELECT[\s\S]*?)```'
        match = re.search(code_block_pattern, response_text, re.IGNORECASE)
        if match:
            return match.group(1).strip().rstrip(';')
        
        # Try plain SELECT
        select_pattern = r'(SELECT\s+.*?(?:;|$))'
        match = re.search(select_pattern, response_text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip().rstrip(';')
        
        if "NO_SQL" in response_text:
            return "NO_SQL"
        
        return None
    
    def ask_for_more_info(self, user_input: str, language: str, context_string=None) -> Dict:
        
        is_arabic = language == "العربية"
        
        # Simple cutoff/ambiguous detection (words like 'you', 'me', or very short incomplete input)
        cutoff_keywords = ["you", "me", "i", "it", "this", "that", "check", "verify", "agency"]
        is_cutoff = any(user_input.lower().strip().endswith(word) for word in cutoff_keywords) \
                    or len(user_input.strip()) < 5
        
        prompt = f"""
    You are a helpful Hajj verification assistant.
    Express willingness to help
    Make sure you help and understand the user
    The user's question: "{user_input}" needs more details to provide accurate information.
    Context: {context_string}

    Examples of vague questions:
    - "I want to verify an agency" (which agency?)
    - "Tell me about Hajj companies" (what specifically?)
    - "Is this authorized?" (which company?)
    - "Check this company" (need company name)

    If the user input is cut off, incomplete, or uses ambiguous words like 'you', 'me', etc.,
    prompt them to clarify politely.

    Ask for specific details in a friendly way:
    1. Agency name (if verifying a company)
    2. Location (city/country)
    3. What specifically they want to know

    Use Arabic if user input is Arabic, otherwise English.
    Use emojis appropriately.
    Keep it brief but friendly.
    Add a simple example of a more specific question.

    """

        if is_cutoff:
            prompt += "\nNote: The user's input may be incomplete or vague. Please ask them to clarify."


        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You help users provide more specific Hajj agency queries."},
                    {"role": "user", "content": prompt}
                ],
                response_format=NEEDSInfoResponse,
                temperature=0.7
            )
            
            info_data = response.choices[0].message.parsed
            return {
                "needs_info": info_data.needs_info,
                "suggestions": info_data.suggestions,
                "missing_info": info_data.missing_info,
                "sample_query": info_data.sample_query
            }
                
        except Exception as e:
            logger.error(f"More info prompt generation failed: {e}")
            # Fallback with minimal structured response
            if is_arabic:
                return {
                    "needs_info": "عذراً، هل يمكنك تقديم المزيد من التفاصيل؟ 🤔",
                    "suggestions": ["هل شركة الهدى للحج معتمدة؟", "أريد التحقق من وكالات الحج في مكة"],
                    "missing_info": ["اسم الوكالة", "الموقع"],
                    "sample_query": "هل شركة الهدى للحج معتمدة؟"
                }
            else:
                return {
                    "needs_info": "Could you provide more details? 🤔",
                    "suggestions": ["Is Al Huda Hajj Agency authorized?", "Show me authorized agencies in Makkah"],
                    "missing_info": ["agency name", "location"],
                    "sample_query": "Is Al Huda Hajj Agency authorized?"
                }
