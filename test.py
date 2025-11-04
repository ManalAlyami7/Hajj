import ast
from core.llm import LLMManager

from openai import OpenAI
import json
import logging

logger = logging.getLogger(__name__)

class LLMJudge:
    """Judge chatbot responses using OpenAI GPT for semantic evaluation."""

    def __init__(self):
        api_key = "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"

        self.client = OpenAI(api_key=api_key)

    def judge(self, user_input: str, expected: str, actual_output: str) -> dict:
        """Use GPT model to judge correctness."""

        system_prompt = (
            "You are an expert evaluator for chatbot responses. "
            "Your task is to determine if the chatbot's answer correctly and semantically matches "
            "the expected answer based on the user's input.\n\n"
            "Respond STRICTLY in JSON format with double quotes if possible:\n"
            "{\n"
            '  "judgment": "✅ MATCH" or "❌ MISMATCH",\n'
            '  "reasoning": "<brief explanation>",\n'
            '  "score": <float between 0 and 1>\n'
            "}\n"
        )

        user_prompt = (
            f"User Input: {user_input}\n"
            f"Expected Answer: {expected}\n"
            f"Chatbot Answer: {actual_output}\n\n"
            "Evaluate how well the chatbot's answer matches the expected answer."
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
            )

            content = response.choices[0].message.content.strip()
            logger.info(f"LLMJudge raw output: {content}")

            # Try JSON parsing
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Handle single quotes or Python dict style
                try:
                    result = ast.literal_eval(content)
                except Exception:
                    result = {
                        "judgment": "❌ MISMATCH",
                        "reasoning": f"Invalid JSON from model: {content}",
                        "score": 0.0
                    }

            # Ensure all required keys exist
            for key in ["judgment", "reasoning", "score"]:
                if key not in result:
                    result[key] = "N/A" if key != "score" else 0.0

            return result

        except Exception as e:
            logger.error(f"LLMJudge failed: {e}")
            return {
                "judgment": "❌ MISMATCH",
                "reasoning": str(e),
                "score": 0.0
            }
import json
from core.graph import ChatGraph
from core.llm import LLMManager
from core.database import DatabaseManager

llm = LLMManager()
db_manager = DatabaseManager()
chat_graph = ChatGraph(db_manager, llm)
judge = LLMJudge()

def load_test_cases(file_path="hajj_agency_qa.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
def run_llm_tests():
    test_cases = load_test_cases()
    results = []
    total = len(test_cases)
    passed = 0

    for idx, case in enumerate(test_cases, start=1):
        user_input_en = case["question_en"]
        expected_answer_en = case["expected_answer_en"]

        print(f"\n🧪 Test {idx}: {user_input_en}")

        # Get chatbot result
        actual_output = chat_graph.process(user_input=user_input_en, language="English")

        if actual_output:
            intent = actual_output.get("intent", "N/A")
            if intent == "DATABASE":
                answer = actual_output.get("summary", "N/A")
            elif intent == "GREETING":
                answer = actual_output.get("greeting_text", "N/A")
            elif intent == "NEEDS_INFO":
                answer = actual_output.get("needs_info", "N/A")
            else:
                answer = actual_output.get("general_answer", "N/A")
        else:
            answer = "No response"

        # LLM judge evaluation
        evaluation = judge.judge(user_input_en, expected_answer_en, answer)
        judgment = evaluation.get("judgment", "❌ MISMATCH")

        if "✅" in judgment:
            passed += 1

        results.append({
            "id": idx,
            "input_en": user_input_en,
            "expected_en": expected_answer_en,
            "chatbot_output": answer,
            "intent": intent,
            "evaluation": evaluation
        })

        print(f" → {judgment}: {evaluation.get('reasoning')}")

    accuracy = round((passed / total) * 100, 2)
    print(f"\n✅ All tests done. Accuracy: {accuracy}%")

    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    


if __name__ == "__main__":
    run_llm_tests()

