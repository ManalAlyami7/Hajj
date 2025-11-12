"""
Database Manager Module
Handles all database operations with proper security and error handling
"""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from typing import Optional, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and queries with security"""
    
    def __init__(self, db_path: str = "hajj_companies.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.engine = self._create_engine()
    
    @st.cache_resource
    def _create_engine(_self):
        """Create and cache database engine"""
        try:
            return create_engine(f"sqlite:///{_self.db_path}")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            st.error(f"❌ Database connection failed: {e}")
            st.stop()
    
    # ---------------- SQL Safety ----------------
    def sanitize_sql(self, sql_query: str) -> Optional[str]:
        if not sql_query:
            return None
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 
            'CREATE', 'EXEC', 'EXECUTE', 'TRUNCATE', 'GRANT',
            'REVOKE', 'REPLACE', 'MERGE'
        ]
        upper = sql_query.upper()
        for kw in dangerous_keywords:
            if kw in upper:
                logger.warning(f"Dangerous keyword detected: {kw}")
                return None
        if not upper.strip().startswith("SELECT"):
            logger.warning("Non-SELECT query attempted")
            return None
        return sql_query.strip().rstrip(';')
    
    # ---------------- Execute Query ----------------
    def execute_query(self, sql_query: str, params: Optional[Dict] = None) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        safe_query = self.sanitize_sql(sql_query)
        if not safe_query:
            return None, "Query failed security validation"
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(text(safe_query), conn, params=params) if params else pd.read_sql(text(safe_query), conn)
                logger.info(f"Query executed successfully: {len(df)} rows")
                return df, None
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return None, str(e)
    
    # ---------------- Database Stats ----------------
    @st.cache_data(ttl=300)
    def get_stats(_self) -> Dict[str, int]:
        query = """
        SELECT 
            COUNT(DISTINCT hajj_company_en) as total,
            COUNT(DISTINCT CASE WHEN is_authorized = 'Yes' THEN hajj_company_en END) as authorized,
            COUNT(DISTINCT country) as countries,
            COUNT(DISTINCT city) as cities,
            COUNT(DISTINCT "الدولة") as countries_ar,
            COUNT(DISTINCT "المدينة") as cities_ar
        FROM agencies
        """
        try:
            with _self.engine.connect() as conn:
                result = pd.read_sql(text(query), conn).iloc[0]
                return {
                    'total': int(result['total']),
                    'authorized': int(result['authorized']),
                    'countries': int(result['countries']),
                    'cities': int(result['cities']),
                    'countries_ar': int(result['countries_ar']),
                    'cities_ar': int(result['cities_ar'])
                }
        except Exception as e:
            logger.error(f"Failed to fetch stats: {e}")
            return {'total':0,'authorized':0,'countries':0,'cities':0,'countries_ar':0,'cities_ar':0}

    # ---------------- Heuristic Query ----------------
    def get_heuristic_query(self, question: str) -> Tuple[Optional[str], Optional[Dict]]:
        q = question.lower().strip()
        if len(q.split()) <= 6 and not any(w in q for w in ["all", "list", "show", "count", "how many"]):
            return (
                """
                SELECT DISTINCT 
                    hajj_company_en, hajj_company_ar, formatted_address, 
                    city, country, "المدينة", "الدولة",
                    email, contact_Info, rating_reviews, is_authorized,
                    google_maps_link
                FROM agencies
                WHERE LOWER(hajj_company_en) = :search
                   OR LOWER(hajj_company_ar) = :search
                   OR LOWER(formatted_address) = :search
                   OR LOWER(city) = :search
                   OR LOWER(country) = :search
                   OR LOWER("المدينة") = :search
                   OR LOWER("الدولة") = :search
                LIMIT 50
                """,
                {"search": q}
            )
        # Authorized agencies
        if "authorized" in q or "معتمدة" in q:
            if "not" in q or "غير" in q:
                return "SELECT * FROM agencies WHERE is_authorized = 'No' LIMIT 100", None
            return "SELECT * FROM agencies WHERE is_authorized = 'Yes' LIMIT 100", None
        # Email queries
        if "email" in q:
            return "SELECT * FROM agencies WHERE email IS NOT NULL AND email != '' LIMIT 100", None
        # Country queries
        if "country" in q or "countries" in q or "دول" in q:
            if "how many" in q or "كم" in q:
                return "SELECT COUNT(DISTINCT country) as count FROM agencies", None
            return 'SELECT DISTINCT country, "الدولة" FROM agencies ORDER BY country LIMIT 100', None
        # City queries
        if "city" in q or "cities" in q or "مدن" in q:
            if "how many" in q or "كم" in q:
                return "SELECT COUNT(DISTINCT city) as count FROM agencies", None
            return 'SELECT DISTINCT city, "المدينة" FROM agencies ORDER BY city LIMIT 25', None
        # Show all
        if any(word in q for word in ["all", "show", "list", "عرض", "قائمة"]):
            return "SELECT * FROM agencies LIMIT 100", None
        return None, None

    # ---------------- Fuzzy Search ----------------
    def search_agency_fuzzy(self, search_term: str) -> pd.DataFrame:
        original_term = search_term.strip().lower()
        if len(original_term) < 2:
            return pd.DataFrame()

        cleaned_term = (
            original_term.replace("شركة","").replace("وكالة","").replace("مؤسسة","")
            .replace("agency","").replace("travel","").strip()
        )

        def _save_last_company(row, df_source: pd.DataFrame):
            st.session_state["last_company_name_ar"] = row.get("hajj_company_ar","")
            st.session_state["last_company_name_en"] = row.get("hajj_company_en","")
            st.session_state["last_city"] = row.get("city","")
            st.session_state["last_country"] = row.get("country","")
            st.session_state["last_city_ar"] = row.get("المدينة","")
            st.session_state["last_country_ar"] = row.get("الدولة","")
            st.session_state["last_email"] = row.get("email","")
            st.session_state["last_contact"] = row.get("contact_Info","")
            st.session_state["last_rating"] = row.get("rating_reviews","")
            st.session_state["last_authorized"] = row.get("is_authorized","")
            st.session_state["last_result_rows"] = df_source.to_dict(orient="records")
            st.session_state["last_intent"] = "DATABASE"

        exact_query = """
        SELECT DISTINCT 
            hajj_company_en, hajj_company_ar, formatted_address,
            city, country, "المدينة", "الدولة",
            email, contact_Info, rating_reviews, is_authorized, google_maps_link
        FROM agencies
        WHERE LOWER(TRIM(hajj_company_en)) = LOWER(:term)
           OR LOWER(TRIM(hajj_company_ar)) = LOWER(:term)
        LIMIT 10
        """
        fuzzy_query = """
        SELECT DISTINCT 
            hajj_company_en, hajj_company_ar, formatted_address,
            city, country, "المدينة", "الدولة",
            email, contact_Info, rating_reviews, is_authorized, google_maps_link
        FROM agencies
        WHERE LOWER(TRIM(hajj_company_en)) LIKE LOWER(:term)
           OR LOWER(TRIM(hajj_company_ar)) LIKE LOWER(:term)
           OR LOWER(city) LIKE LOWER(:term)
           OR LOWER(country) LIKE LOWER(:term)
           OR LOWER("المدينة") LIKE LOWER(:term)
           OR LOWER("الدولة") LIKE LOWER(:term)
        LIMIT 50
        """

        # 1️⃣ Exact match
        df, _ = self.execute_query(exact_query, {"term": original_term})
        if isinstance(df, pd.DataFrame) and not df.empty:
            if len(df) == 1: _save_last_company(df.iloc[0], df)
            return df

        # 2️⃣ Cleaned exact match
        if cleaned_term and cleaned_term != original_term:
            df, _ = self.execute_query(exact_query, {"term": cleaned_term})
            if isinstance(df, pd.DataFrame) and not df.empty:
                if len(df) == 1: _save_last_company(df.iloc[0], df)
                return df

        # 3️⃣ Fuzzy match
        term_to_search = f"%{cleaned_term or original_term}%"
        df, _ = self.execute_query(fuzzy_query, {"term": term_to_search})
        if isinstance(df, pd.DataFrame) and not df.empty:
            if len(df) == 1: _save_last_company(df.iloc[0], df)
            return df

        return pd.DataFrame()
