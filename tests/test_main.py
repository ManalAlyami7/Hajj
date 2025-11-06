import sys
from pathlib import Path

# أضف مجلد المشروع الرئيسي (حيث يوجد app.py) إلى sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import main
import pytest
import streamlit as st

def test_main_runs_without_error(monkeypatch):
    # تجاوز مكونات Streamlit
    monkeypatch.setattr(st, "radio", lambda label, options, *args, **kwargs: options[0])
    monkeypatch.setattr(st, "selectbox", lambda label, options, *args, **kwargs: options[0])
    monkeypatch.setattr(st, "text_input", lambda label, *args, **kwargs: "Test User")
    monkeypatch.setattr(st, "button", lambda label, *args, **kwargs: True)

    try:
        main()
    except Exception as e:
        pytest.fail(f"main() raised an exception: {e}")
