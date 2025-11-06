import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app import main  # أو أي دالة تريد اختبارها

import pytest
import streamlit as st

def test_full_runs_without_error(monkeypatch):
    monkeypatch.setattr(st, "radio", lambda label, options, *args, **kwargs: options[0])
    monkeypatch.setattr(st, "selectbox", lambda label, options, *args, **kwargs: options[0])
    monkeypatch.setattr(st, "text_input", lambda label, *args, **kwargs: "Test User")
    monkeypatch.setattr(st, "button", lambda label, *args, **kwargs: True)

    try:
        main()
    except Exception as e:
        pytest.fail(f"main() raised an exception: {e}")
