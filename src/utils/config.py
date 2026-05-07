import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HISTORY_FILE = os.path.join(BASE_DIR, "data", "price_history.jsonl")
TRACE_FILE = os.path.join(BASE_DIR, "data/traces", "trace_record.jsonl")
DOCS_DIR = os.path.join(BASE_DIR, "data", "docs")
VECTOR_DB_DIR = os.path.join(BASE_DIR, "data", "vector_db")