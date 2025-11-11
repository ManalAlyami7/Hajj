# core/llm.py
import streamlit as st
from openai import OpenAI
import json

class RLLMManager:
    def __init__(self):
        self.client = self._get_client()

    def _get_client(self):
        """Get cached OpenAI client"""
        api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("key")
        if not api_key:
            st.warning("⚠️ OpenAI API key missing in Streamlit secrets")
            st.stop()
        return OpenAI(api_key=api_key)

    def validate_user_input_llm(self, step: int, user_input: str) -> dict:
        """
        Ask the LLM to validate user input.
        Returns a dictionary:
        {
            "is_valid": True/False,
            "feedback": "Explanation for user"
        }
        """
        role_map = {1: "agency name", 2: "city name", 3: "complaint details", 4: "contact info"}
        role = role_map.get(step, "input")

        prompt =f"""
You are a friendly assistant that validates user input for a Hajj complaint reporting chatbot.
The user input is: "{user_input}".
The input type is: {role}.

Validation Rules:
1. Agency name and city: accept reasonable names, even if slightly misspelled.
2. Complaint details:
   - Accept any meaningful description of the incident.
   - Do NOT flag any date (past or future) as invalid; users may report payments or bookings for past or upcoming dates.
   - Check only for completeness and clarity.
3. Contact info: accept valid email or phone, or "skip" to remain anonymous.

Your output MUST be **JSON only**, with two keys:
- is_valid (true/false)
- feedback (friendly, short, guiding the user if needed)

Examples:

1. Valid complaint details (future or past dates allowed):
{{
  "is_valid": true,
  "feedback": "Looks good! Your complaint details are clear."
}}

2. Missing complaint details:
{{
  "is_valid": false,
  "feedback": "Please provide details about what happened, including payments, promises, or actions by the agency."
}}

3. Invalid contact info:
{{
  "is_valid": false,
  "feedback": "Please enter a valid email or phone, or type 'skip' to remain anonymous."
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You validate inputs for a Hajj reporting chatbot."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            # fallback if LLM fails
            return {"is_valid": False, "feedback": f"Validation failed, please try again. ({str(e)})"}
