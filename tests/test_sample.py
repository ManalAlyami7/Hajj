import pytest
import streamlit as st
from app import _trim_session_memory, main

# ------------------------------
# Test for _trim_session_memory
# ------------------------------
def test_trim_session_memory():
    # إعداد حالة جلسة فيها رسائل كثيرة وطويلة
    st.session_state.chat_memory = [
        {"content": "x" * 2000},  # رسالة طويلة جدًا
        {"content": "Hello"},
    ]
    
    _trim_session_memory(max_messages=1, max_message_chars=100)

    # نتأكد إن الرسالة الطويلة انقصت
    assert len(st.session_state.chat_memory) == 1
    assert len(st.session_state.chat_memory[0]["content"]) <= 100

# ------------------------------
# Test for main() function
# ------------------------------
def test_main_runs_without_error(monkeypatch):
    """يتأكد إن التطبيق يشتغل بدون أخطاء"""
    # نحاكي اللغة في الـsession
    st.session_state.language = "English"

    # نحاكي واجهات الـUI والدوال اللي ممكن تسبب مشاكل بالاختبار
