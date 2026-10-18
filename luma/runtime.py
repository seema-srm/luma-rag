import json, os
from langsmith import tracing_context
from .config import manifest_path
from .services import embeddings, pinecone_client, vector_store, chat_model
from .graph import build_graph

def create_runtime(collection):
    path=manifest_path(collection)
    if not path.exists(): raise ValueError(f'Import this collection first: python ingest.py --collection {collection}')
    manifest=json.loads(path.read_text())
    current_model=os.getenv('FIREWORKS_EMBEDDING_MODEL','nomic-ai/nomic-embed-text-v1.5')
    if manifest['embedding_model']!=current_model:raise ValueError('Embedding model changed. Re-import this collection before searching.')
    def store():
        pc=pinecone_client();desc=pc.describe_index(manifest['index'])
        if desc.dimension!=manifest['dimension']:raise ValueError('Index dimension changed. Re-import into the correct index.')
        return vector_store(pc.Index(host=desc.host),embeddings(),manifest['namespace'])
    return build_graph(store,chat_model,float(os.getenv('RETRIEVAL_MIN_SCORE','0.45')))

def ask(graph,question,collection,previous_question='',style='Beginner-friendly'):
    enabled=collection!='private' and os.getenv('LANGSMITH_TRACING','false').lower()=='true' and bool(os.getenv('LANGSMITH_API_KEY'))
    # Private collection never sends traces to LangSmith, even when enabled globally.
    with tracing_context(enabled=enabled,project_name=os.getenv('LANGSMITH_PROJECT','luma-learning')):
        return graph.invoke({'question':question,'previous_question':previous_question,'style':style,'sources':[]},config={'run_name':'Luma learning question','metadata':{'collection':collection}})
