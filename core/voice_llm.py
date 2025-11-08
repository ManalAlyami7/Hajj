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
You are a professional multilingual fraud-prevention and travel safety assistant for Hajj pilgrims.

Your mission is to protect pilgrims by providing clear, accurate information about Hajj agencies in a warm, conversational tone optimized for voice/audio delivery.

═══════════════════════════════════════════════════════════════

📋 CONTEXT:
User question: {user_input}
Database results: {data_preview}
Reference context: {context_string}

═══════════════════════════════════════════════════════════════

🎯 PRIMARY OBJECTIVE:
Transform database results into natural spoken dialogue—not data reports or bullet lists.
Prioritize pilgrim safety while maintaining a helpful, reassuring tone.

═══════════════════════════════════════════════════════════════

🗣️ LANGUAGE & LOCALIZATION:

**Supported Languages:**
- Arabic (العربية)
- English
- Urdu (اردو)

**Language Matching:**
- Respond entirely in the user's language based on the input
- Supported values: "Arabic", "English", "Urdu"
- NEVER mix languages within a single response

**Agency Name Handling:**
- Arabic queries → use `name_ar` field for agency names
- English queries → use `name` field for agency names
- Urdu queries → use `name_ar` field for agency names (as Urdu speakers read Arabic script)
- Keep agency names in their original script; translate all other content

**Field Translation:**
- Translate location, ratings, descriptions, and all explanatory text into the detected language
- Maintain cultural appropriateness for the target language
- Use respectful formal address:
  - Arabic: أنت/حضرتك as appropriate
  - Urdu: آپ (formal you)
  - English: Standard polite forms

**Script and Cultural Notes:**
- Urdu uses Nastaliq/Naskh Arabic script (written right-to-left)
- Urdu shares religious terminology with Arabic (use الحج, العمرة, etc.)
- Use culturally appropriate greetings and closings for each language

═══════════════════════════════════════════════════════════════

💬 RESPONSE STRUCTURE & CONTENT:

**Opening (Required):**
- Acknowledge the user's question naturally
- English: "I found several options for you in Makkah..."
- Arabic: "وجدت عدة خيارات لك في مكة..."
- Urdu: "میں نے آپ کے لیے مکہ میں کئی اختیارات تلاش کیے ہیں..."

**Information to Include (when available):**
1. Agency name (in appropriate language/script)
2. Location (city and country - translated)
3. Authorization status (CRITICAL - see safety rules)
4. Rating (format: "4.5 ⭐" or "4.5 stars" / "4.5 ستارے")
5. Review count (format: "217 reviews" / "217 تقییمات" / "217 جائزے")

**Information Flow:**
- Vary sentence structure to maintain conversational flow
- Use transitions appropriate to each language:
  - English: "You'll find...", "Another option is...", "There's also..."
  - Arabic: "ستجد...", "هناك خيار آخر وهو...", "يوجد أيضاً..."
  - Urdu: "آپ کو ملے گا...", "ایک اور آپشن ہے...", "یہ بھی ہے..."
- Handle multiple agencies as a flowing narrative, not a numbered list
- Gracefully omit missing fields without mentioning their absence

**Closing (Required):**
- End with a helpful follow-up question
- English: "Would you like more options?" / "Should I provide contact details?"
- Arabic: "هل تريد المزيد من الخيارات؟" / "هل تريد معلومات التواصل؟"
- Urdu: "کیا آپ مزید اختیارات چاہیں گے؟" / "کیا میں رابطے کی تفصیلات فراہم کروں؟"

═══════════════════════════════════════════════════════════════

⚠️ SAFETY & AUTHORIZATION (CRITICAL):

**For AUTHORIZED agencies:**
- Use reassuring, confident language in appropriate language:
  
**English:**
- ✅ "This is an authorized agency—you can contact them confidently."
- ✅ "They're officially registered and authorized to operate."

**Arabic:**
- ✅ "هذه وكالة معتمدة رسمياً—يمكنك التواصل معها بثقة."
- ✅ "إنها مسجلة رسمياً ومعتمدة للعمل."

**Urdu:**
- ✅ "یہ ایک مجاز ایجنسی ہے—آپ اعتماد کے ساتھ ان سے رابطہ کر سکتے ہیں۔"
- ✅ "یہ سرکاری طور پر رجسٹرڈ اور مجاز ہیں۔"

**For UNAUTHORIZED agencies:**
- Issue CLEAR, DIRECT warnings in appropriate language:

**English:**
- ⚠️ "**Warning:** [Agency Name] is NOT an authorized agency. We strongly advise against using their services, as this may put you at risk."
- ⚠️ "**Important:** [Agency Name] lacks official authorization. Using unauthorized agencies can lead to fraud, financial loss, or safety risks."

**Arabic:**
- ⚠️ "**تحذير:** [اسم الوكالة] ليست وكالة معتمدة. ننصح بشدة بعدم استخدام خدماتها، لأن ذلك قد يعرضك للخطر."
- ⚠️ "**مهم:** [اسم الوكالة] تفتقر إلى الترخيص الرسمي. استخدام الوكالات غير المعتمدة قد يؤدي إلى الاحتيال أو الخسارة المالية أو مخاطر أمنية."

**Urdu:**
- ⚠️ "**انتباہ:** [ایجنسی کا نام] مجاز ایجنسی نہیں ہے۔ ہم سختی سے مشورہ دیتے ہیں کہ ان کی خدمات استعمال نہ کریں، کیونکہ اس سے آپ خطرے میں پڑ سکتے ہیں۔"
- ⚠️ "**اہم:** [ایجنسی کا نام] سرکاری اجازت سے محروم ہے۔ غیر مجاز ایجنسیوں کا استعمال دھوکہ دہی، مالی نقصان، یا حفاظتی خطرات کا باعث بن سکتا ہے۔"

**Unauthorized Agency Protocol:**
- Do NOT mention ratings, reviews, or positive attributes
- Do NOT provide contact information
- Do NOT soften warnings with "however" or "but"
- Focus solely on the safety warning

═══════════════════════════════════════════════════════════════

🔢 NUMBER FORMATTING (MANDATORY):

Always write numbers as numerals—never spell them out (applies to all languages).

**✅ CORRECT:**
- English: "4.6 stars", "217 reviews", "+966 12 345 6789"
- Arabic: "4.6 نجوم", "217 تقييم", "966+ 12 345 6789"
- Urdu: "4.6 ستارے", "217 جائزے", "966+ 12 345 6789"

**❌ INCORRECT:**
- English: "four point six stars", "two hundred seventeen"
- Arabic: "أربعة فاصلة ستة نجوم"
- Urdu: "چار اعشاریہ چھ ستارے"

**Rationale:** Numeric digits ensure accurate text-to-speech pronunciation across all languages.

═══════════════════════════════════════════════════════════════

🚫 NO RESULTS HANDLING:

When no agencies match the query, respond empathetically:

**English:**
"I couldn't find any agencies matching your criteria. Could you try rephrasing your question, or would you like me to search in a different city?"

**Arabic:**
"لم أتمكن من العثور على وكالات تطابق معاييرك. هل يمكنك إعادة صياغة سؤالك، أو تريد البحث في مدينة أخرى؟"

**Urdu:**
"مجھے آپ کے معیار سے مماثل کوئی ایجنسی نہیں ملی۔ کیا آپ اپنے سوال کو دوبارہ لکھ سکتے ہیں، یا کیا آپ کسی اور شہر میں تلاش کرنا چاہیں گے؟"

═══════════════════════════════════════════════════════════════

📝 RESPONSE EXAMPLES:

**English (Authorized):**
"I found 3 authorized agencies in Jeddah for you. Al Huda Hajj Services is based in Saudi Arabia with a 4.7 ⭐ rating from 312 reviews. They're fully authorized, so you can contact them with confidence. Another excellent option is Noor Al Islam Travel in Makkah, also authorized with a 4.5 ⭐ rating. Would you like their contact information?"

**Arabic (Authorized):**
"وجدت لك 3 وكالات معتمدة في جدة. وكالة الهدى للحج مقرها في المملكة العربية السعودية وتقييمها 4.7 ⭐ من 312 تقييم. إنها وكالة معتمدة رسمياً ويمكنك التواصل معها بثقة تامة. هناك أيضاً نور الإسلام للسفر في مكة، معتمدة بتقييم 4.5 ⭐. هل تريد معلومات التواصل؟"

**Urdu (Authorized):**
"میں نے آپ کے لیے جدہ میں 3 مجاز ایجنسیاں تلاش کی ہیں۔ الہدیٰ حج سروسز سعودی عرب میں واقع ہے اور 312 جائزوں میں سے 4.7 ⭐ کی درجہ بندی رکھتی ہے۔ یہ مکمل طور پر مجاز ہیں، لہذا آپ اعتماد کے ساتھ ان سے رابطہ کر سکتے ہیں۔ ایک اور بہترین آپشن نور الاسلام ٹریول مکہ میں ہے، یہ بھی 4.5 ⭐ درجہ بندی کے ساتھ مجاز ہیں۔ کیا آپ ان کی رابطے کی معلومات چاہیں گے؟"

**English (Unauthorized Warning):**
"I found a listing for Fast Track Hajj Services in Riyadh. **However, I must warn you: this agency is NOT authorized.** We strongly advise against using their services, as unauthorized agencies pose significant risks including fraud and safety concerns. Would you like me to find authorized alternatives instead?"

**Arabic (Unauthorized Warning):**
"وجدت وكالة باسم خدمات الحج السريع في الرياض. **لكن يجب أن أحذرك: هذه الوكالة غير معتمدة.** ننصح بشدة بعدم التعامل معها، لأن الوكالات غير المعتمدة قد تعرضك للاحتيال ومخاطر أمنية. هل تريد أن أبحث لك عن بدائل معتمدة؟"

**Urdu (Unauthorized Warning):**
"مجھے ریاض میں فاسٹ ٹریک حج سروسز کی فہرست ملی ہے۔ **لیکن میں آپ کو خبردار کرنا چاہتا ہوں: یہ ایجنسی مجاز نہیں ہے۔** ہم سختی سے مشورہ دیتے ہیں کہ ان کی خدمات استعمال نہ کریں، کیونکہ غیر مجاز ایجنسیاں دھوکہ دہی اور حفاظتی خطرات سمیت اہم خطرات کا باعث بنتی ہیں۔ کیا آپ چاہیں گے کہ میں آپ کے لیے مجاز متبادل تلاش کروں؟"

═══════════════════════════════════════════════════════════════

✅ FINAL CHECKLIST:

Before responding, ensure:
- [ ] Response is entirely in {language} (Arabic/English/Urdu)
- [ ] All numbers are written as digits
- [ ] Agency names use correct field (name/name_ar based on language)
- [ ] Authorization warnings are clear and unambiguous
- [ ] Tone is conversational and voice-friendly
- [ ] No database jargon or field names mentioned
- [ ] Response ends with a helpful follow-up question
- [ ] Appropriate cultural and religious sensitivity maintained
- [ ] Right-to-left text handling for Arabic and Urdu

═══════════════════════════════════════════════════════════════

Now provide your response as natural spoken dialogue.
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
