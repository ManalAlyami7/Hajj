# core/report_llm.py - IMPROVED VERSION
<<<<<<< HEAD
"""
Enhanced LLM Manager for Report Validation
Provides robust validation with better error handling and structured prompts
"""
=======

“””
Enhanced LLM Manager for Report Validation
Provides robust validation with better error handling and structured prompts
“””
>>>>>>> 811a0bbcb131767a25cbefbfacdf655bb0dac92d

import streamlit as st
from openai import OpenAI
import json
from typing import Dict
import logging

# Configure logging
<<<<<<< HEAD
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RLLMManager:
    """Manages LLM interactions for report validation with enhanced error handling"""
    
    def __init__(self):
        self.client = self._get_client()
        self.model = "gpt-4o-mini"
        
    def _get_client(self) -> OpenAI:
        """Get cached OpenAI client with proper error handling"""
        try:
            api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("key")
            if not api_key:
                logger.error("OpenAI API key missing")
                st.error("⚠️ Configuration error: OpenAI API key not found")
                st.stop()
            return OpenAI(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            st.error("⚠️ Failed to initialize AI service")
            st.stop()

    def validate_user_input_llm(self, step: int, user_input: str) -> Dict[str, any]:
        """
        Validate user input using LLM with enhanced error handling
        
        Args:
            step: Current step in the reporting flow (1-4)
            user_input: User's input to validate
            
        Returns:
            dict: {"is_valid": bool, "feedback": str}
        """
        # Early validation for empty input
        if not user_input or not user_input.strip():
            return {
                "is_valid": False,
                "feedback": "Input cannot be empty. Please provide information."
            }
        
        role_map = {
            1: "agency name",
            2: "city name", 
            3: "complaint details",
            4: "contact info"
        }
        role = role_map.get(step, "input")

        # Enhanced prompt with clearer structure and examples
        prompt = f"""You are validating user input for a secure complaint reporting system.

INPUT TYPE: {role}
USER INPUT: "{user_input}"

VALIDATION RULES:
1. Agency name (step 1): Accept any reasonable business name, allow minor spelling variations
2. City name (step 2): Accept any valid city/location name globally
3. Complaint details (step 3):
   - Must contain meaningful description of the incident
   - Accept ALL dates (past, present, future) - users may report future bookings or past payments
   - Minimum 20 characters for substance
   - Check for clarity and completeness only
4. Contact info (step 4): 
   - Accept valid email format (contains @ and domain)
   - Accept phone with 7+ digits
   - Accept "skip" or "anonymous" to proceed without contact

RESPONSE FORMAT (JSON only, no markdown):
{{
  "is_valid": true/false,
  "feedback": "Brief, friendly message (max 100 chars)"
=======

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(**name**)

class RLLMManager:
“”“Manages LLM interactions for report validation with enhanced error handling”””

```
def __init__(self):
    self.client = self._get_client()
    self.model = "gpt-4o-mini"
    
def _get_client(self) -> OpenAI:
    """Get cached OpenAI client with proper error handling"""
    try:
        api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("key")
        if not api_key:
            logger.error("OpenAI API key missing")
            st.error("⚠️ Configuration error: OpenAI API key not found")
            st.stop()
        return OpenAI(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        st.error("⚠️ Failed to initialize AI service")
        st.stop()

def validate_user_input_llm(self, step: int, user_input: str) -> Dict[str, any]:
    """
    Validate user input using LLM with enhanced error handling
    
    Args:
        step: Current step in the reporting flow (1-4)
        user_input: User's input to validate
        
    Returns:
        dict: {"is_valid": bool, "feedback": str}
    """
    # Early validation for empty input
    if not user_input or not user_input.strip():
        return {
            "is_valid": False,
            "feedback": "Input cannot be empty. Please provide information."
        }
    
    role_map = {
        1: "agency name",
        2: "city name", 
        3: "complaint details",
        4: "contact info"
    }
    role = role_map.get(step, "input")

    # Enhanced prompt with clearer structure and examples
    prompt = f"""You are validating user input for a secure complaint reporting system.
```

INPUT TYPE: {role}
USER INPUT: “{user_input}”

VALIDATION RULES:

1. Agency name (step 1): Accept any reasonable business name, allow minor spelling variations
1. City name (step 2): Accept any valid city/location name globally
1. Complaint details (step 3):
- Must contain meaningful description of the incident
- Accept ALL dates (past, present, future) - users may report future bookings or past payments
- Minimum 20 characters for substance
- Check for clarity and completeness only
1. Contact info (step 4):
- Accept valid email format (contains @ and domain)
- Accept phone with 7+ digits
- Accept “skip” or “anonymous” to proceed without contact

RESPONSE FORMAT (JSON only, no markdown):
{{
“is_valid”: true/false,
“feedback”: “Brief, friendly message (max 100 chars)”
>>>>>>> 811a0bbcb131767a25cbefbfacdf655bb0dac92d
}}

EXAMPLES:

<<<<<<< HEAD
Valid agency: {{"is_valid": true, "feedback": "Agency name recorded successfully."}}
Invalid agency: {{"is_valid": false, "feedback": "Please enter the full agency name."}}

Valid city: {{"is_valid": true, "feedback": "Location recorded."}}
Invalid city: {{"is_valid": false, "feedback": "Please enter a valid city name."}}

Valid complaint: {{"is_valid": true, "feedback": "Complaint details are clear and complete."}}
Invalid complaint: {{"is_valid": false, "feedback": "Please provide more details about the incident (date, amount, what happened)."}}

Valid contact: {{"is_valid": true, "feedback": "Contact information recorded."}}
Invalid contact: {{"is_valid": false, "feedback": "Please enter a valid email/phone or type 'skip'."}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You validate inputs for a secure reporting system. Respond ONLY with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=150  # Limit response size for efficiency
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:].strip()
            
            result = json.loads(content)
            
            # Validate response structure
            if not isinstance(result, dict) or "is_valid" not in result:
                raise ValueError("Invalid response structure from LLM")
                
            # Return validated structure with truncated feedback
            return {
                "is_valid": bool(result.get("is_valid", False)),
                "feedback": str(result.get("feedback", "Validation completed"))[:200]
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in LLM response: {e}")
            return {
                "is_valid": False,
                "feedback": "System error during validation. Please try rephrasing your input."
            }
        except Exception as e:
            logger.error(f"LLM validation error: {e}")
            return {
                "is_valid": False,
                "feedback": "Validation service temporarily unavailable. Please try again."
            }
=======
Valid agency: {{“is_valid”: true, “feedback”: “Agency name recorded successfully.”}}
Invalid agency: {{“is_valid”: false, “feedback”: “Please enter the full agency name.”}}

Valid city: {{“is_valid”: true, “feedback”: “Location recorded.”}}
Invalid city: {{“is_valid”: false, “feedback”: “Please enter a valid city name.”}}

Valid complaint: {{“is_valid”: true, “feedback”: “Complaint details are clear and complete.”}}
Invalid complaint: {{“is_valid”: false, “feedback”: “Please provide more details about the incident (date, amount, what happened).”}}

Valid contact: {{“is_valid”: true, “feedback”: “Contact information recorded.”}}
Invalid contact: {{“is_valid”: false, “feedback”: “Please enter a valid email/phone or type ‘skip’.”}}
“””

```
    try:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You validate inputs for a secure reporting system. Respond ONLY with valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=150  # Limit response size for efficiency
        )
        
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:].strip()
        
        result = json.loads(content)
        
        # Validate response structure
        if not isinstance(result, dict) or "is_valid" not in result:
            raise ValueError("Invalid response structure from LLM")
            
        # Return validated structure with truncated feedback
        return {
            "is_valid": bool(result.get("is_valid", False)),
            "feedback": str(result.get("feedback", "Validation completed"))[:200]
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in LLM response: {e}")
        return {
            "is_valid": False,
            "feedback": "System error during validation. Please try rephrasing your input."
        }
    except Exception as e:
        logger.error(f"LLM validation error: {e}")
        return {
            "is_valid": False,
            "feedback": "Validation service temporarily unavailable. Please try again."
        }
```
>>>>>>> 811a0bbcb131767a25cbefbfacdf655bb0dac92d
