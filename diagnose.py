import sys
import os
import traceback

try:
    print("Trying to load settings...")
    from app.config import get_settings
    settings = get_settings()
    print("Settings loaded. OpenAI model:", settings.openai_model)

    print("Trying to list documents...")
    from app.rag.crud import list_documents
    docs = list_documents()
    print("Successfully listed documents:", docs)

except Exception as e:
    print("An error occurred!")
    traceback.print_exc()
    with open("diagnostic_error.log", "w") as f:
        traceback.print_exc(file=f)
