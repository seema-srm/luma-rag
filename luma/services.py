import os
from langchain_core.embeddings import Embeddings
from langchain_fireworks import FireworksEmbeddings, ChatFireworks
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from .config import required

class LearningEmbeddings(Embeddings):
    """Nomic uses task prefixes; retain this contract for both indexing and queries."""
    def __init__(self, model):
        self.model=model
        self.client=FireworksEmbeddings(model=model)
    def embed_documents(self,texts):
        prefix='search_document: ' if 'nomic' in self.model else ''
        return self.client.embed_documents([prefix+t for t in texts])
    def embed_query(self,text):
        prefix='search_query: ' if 'nomic' in self.model else ''
        return self.client.embed_query(prefix+text)

def embeddings():
    required('FIREWORKS_API_KEY')
    return LearningEmbeddings(os.getenv('FIREWORKS_EMBEDDING_MODEL','nomic-ai/nomic-embed-text-v1.5'))

def pinecone_client():
    required('PINECONE_API_KEY')
    return Pinecone(api_key=os.environ['PINECONE_API_KEY'])

def vector_store(index,embedding,namespace):
    return PineconeVectorStore(index=index,embedding=embedding,namespace=namespace)

def chat_model():
    required('FIREWORKS_API_KEY','FIREWORKS_MODEL')
    schema={
        'type':'object',
        'properties':{
            'supported':{'type':'boolean'},
            'answer':{'type':'string'},
            'citations':{'type':'array','items':{'type':'integer'}},
        },
        'required':['supported','answer','citations'],
        'additionalProperties':False,
    }
    # Enforce the response shape at generation time, rather than only asking
    # for JSON in the prompt. Fireworks documents that json_schema mode also
    # disables reasoning output. Keep citation/source validation in graph.py.
    model=ChatFireworks(
        model=os.environ['FIREWORKS_MODEL'],temperature=0,max_tokens=4096,
        request_timeout=60,max_retries=1,
    )
    # return model.bind(response_format={
    #     'type':'json_schema',
    #     'json_schema':{'name':'LumaGroundedAnswer','schema':schema},
    # }
    return model.bind(
    reasoning_effort="none",
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "LumaGroundedAnswer",
            "schema": schema,
        },
    },
    )
