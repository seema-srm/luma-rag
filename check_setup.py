import importlib,os
from luma.config import ROOT
print('Luma Python setup check — no API calls')
for name in ['streamlit','langchain_core','langchain_text_splitters','langchain_fireworks','langchain_pinecone','langgraph','langsmith','pypdf','docx']:
    try:importlib.import_module(name); print(name+': installed')
    except ImportError:print(name+': MISSING')
for key in ['FIREWORKS_API_KEY','FIREWORKS_MODEL','PINECONE_API_KEY','LANGSMITH_API_KEY']:
    print(key+': '+('configured' if os.getenv(key) else 'not configured'))
print('Secrets are never printed. .env present: '+str((ROOT/'.env').exists()))
