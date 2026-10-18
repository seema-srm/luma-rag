"""Independent regression checks; never call live providers."""
import json
from contextlib import contextmanager
from types import SimpleNamespace
from pathlib import Path
import pytest
from langchain_core.documents import Document
from luma.graph import build_graph, normalize_query

class Store:
    def __init__(self, metadata=None, score=.9):
        self.metadata=metadata or {'title':'RAG','source':'rag.md'};self.score=score;self.queries=[]
    def similarity_search_with_score(self,q,k):
        self.queries.append(q)
        return [(Document(page_content='RAG retrieves evidence before generating an answer.',metadata=self.metadata),self.score)]
class Model:
    def __init__(self,payload):self.payload=payload;self.inputs=[]
    def invoke(self,messages):
        self.inputs.append(json.loads(messages[1].content))
        return SimpleNamespace(content=json.dumps(self.payload) if not isinstance(self.payload,str) else self.payload)
def run(q='What is RAG?',payload=None,metadata=None,style='Technical',previous=''):
    s=Store(metadata);m=Model(payload if payload is not None else {'supported':True,'answer':'RAG retrieves evidence [1].','citations':[1]})
    result=build_graph(lambda:s,lambda:m).invoke({'question':q,'previous_question':previous,'style':style,'sources':[]})
    return result,s,m

@pytest.mark.parametrize('question',['hi','hello','thanks','ok','you are wrong','That is wrong!'])
def test_feedback_routes_without_retrieval(question):
    r,s,m=run(question)
    assert not s.queries and not m.inputs and not r['sources']
@pytest.mark.parametrize('question',['what is gen ai','what is llm','What is RAG?','I need to learn workflow'])
def test_new_questions_use_own_retrieval_query(question):
    r,s,m=run(question,previous='How do I write prompts?')
    assert s.queries==[question]
    assert m.inputs[0]['question']==question

def test_technical_style_reaches_model():
    _,_,m=run(style='Technical');assert m.inputs[0]['style']=='Technical'
def test_explicit_followup_carries_context():
    _,s,_=run('Explain it simply',previous='What are embeddings?')
    assert 'What are embeddings?' in s.queries[0]
@pytest.mark.parametrize('payload', ['not json',[],{'supported':True,'answer':'Bad [99]','citations':[99]}, {'supported':True,'answer':'Bad [1]','citations':[True]}])
def test_malformed_or_invalid_ids_are_rejected(payload):
    r,_,_=run(payload=payload);assert 'citation_check_failed' in r['trace_steps']
def test_missing_inline_refs_get_footer():
    r,_,_=run(payload={'supported':True,'answer':'RAG retrieves evidence.','citations':[1]})
    assert r['answer'].endswith('Sources: [1]')
def test_model_abstention():
    r,_,_=run(payload={'supported':False,'answer':'Not covered','citations':[]})
    assert not r['sources'] and 'abstain_insufficient_support' in r['trace_steps']
def test_dependency_errors_propagate_to_ui_handler():
    def fail():raise RuntimeError('unavailable')
    with pytest.raises(RuntimeError):build_graph(fail,fail).invoke({'question':'RAG?','sources':[]})

def test_runtime_missing_manifest_is_clear(tmp_path,monkeypatch):
    import luma.runtime as rt
    monkeypatch.setattr(rt,'manifest_path',lambda c:tmp_path/'missing.json')
    with pytest.raises(ValueError,match='Import this collection first'):rt.create_runtime('ai')
def test_runtime_changed_embedding_model_rejected(tmp_path,monkeypatch):
    import luma.runtime as rt
    p=tmp_path/'ai.json';p.write_text(json.dumps({'embedding_model':'old'}))
    monkeypatch.setattr(rt,'manifest_path',lambda c:p)
    monkeypatch.setenv('FIREWORKS_EMBEDDING_MODEL','new')
    with pytest.raises(ValueError,match='Embedding model changed'):rt.create_runtime('ai')
def test_private_tracing_disabled(monkeypatch):
    import luma.runtime as rt
    recorded=[]
    @contextmanager
    def trace(**kw):recorded.append(kw);yield
    monkeypatch.setattr(rt,'tracing_context',trace)
    monkeypatch.setenv('LANGSMITH_TRACING','true');monkeypatch.setenv('LANGSMITH_API_KEY','test-only')
    class Graph:
        def invoke(self,*a,**kw):return {'answer':'okay'}
    rt.ask(Graph(),'question','private')
    assert recorded[0]['enabled'] is False

def test_nomic_embedding_prefixes(monkeypatch):
    import luma.services as sv
    captured={}
    class Fake:
        def __init__(self,**kw):pass
        def embed_documents(self,texts):captured['docs']=texts;return [[1.0]]
        def embed_query(self,text):captured['query']=text;return [1.0]
    monkeypatch.setattr(sv,'FireworksEmbeddings',Fake)
    emb=sv.LearningEmbeddings('nomic-ai/nomic-embed-text-v1.5')
    emb.embed_documents(['Lesson']);emb.embed_query('Question')
    assert captured=={'docs':['search_document: Lesson'],'query':'search_query: Question'}
def test_chat_binding_schema(monkeypatch):
    import luma.services as sv
    captured={}
    class Fake:
        def __init__(self,**kw):captured['init']=kw
        def bind(self,**kw):captured['binding']=kw;return self
    monkeypatch.setattr(sv,'ChatFireworks',Fake)
    monkeypatch.setenv('FIREWORKS_API_KEY','test-only');monkeypatch.setenv('FIREWORKS_MODEL','test-model')
    sv.chat_model()
    assert captured['init']['max_tokens']==4096
    assert captured['binding']['reasoning_effort']=='none'
    assert captured['binding']['response_format']['type']=='json_schema'

# Characterization probes: they document limitations, not answer-quality passes.
def test_characterize_unrelated_answer_with_valid_id_is_accepted():
    r,_,_=run('What is Tavily?',{'supported':True,'answer':'Tavily is a web search service [1].','citations':[1]})
    assert 'citation_format_check' in r['trace_steps']
def test_characterize_metadata_can_override_reserved_id():
    r,_,_=run(metadata={'id':99,'text':'Overridden','title':'RAG','source':'rag.md'})
    assert not r['sources'] and r['answer'].endswith('[1].')

@pytest.fixture
def ui(monkeypatch,tmp_path):
    from streamlit.testing.v1 import AppTest
    import luma.config as cfg
    import luma.runtime as rt
    p=tmp_path/'manifest.json';p.write_text('{}')
    monkeypatch.setattr(cfg,'manifest_path',lambda c:p)
    monkeypatch.setattr(rt,'create_runtime',lambda c:'fake-graph')
    calls=[]
    def ask(*args):
        calls.append(args)
        return {'answer':'Answer to '+args[1]+' [1]','sources':[{'id':1,'title':'Lesson','text':'Supporting passage.'}]}
    monkeypatch.setattr(rt,'ask',ask)
    app=AppTest.from_file(str(cfg.ROOT/'app.py')).run()
    assert not app.exception
    return app,calls,p

def test_ui_initial_collection_and_no_provider_calls(ui):
    app,calls,_=ui
    assert app.selectbox[0].options==['AI learning — public']
    assert not calls and not app.chat_message

def test_ui_newest_pair_first_and_context_stays_chronological(ui):
    app,calls,_=ui
    app.chat_input[0].set_value('What is RAG?').run()
    app.chat_input[0].set_value('Explain it more simply').run()
    assert not app.exception
    assert len(app.chat_message)==4
    assert app.chat_message[0].markdown[0].value=='Explain it more simply'
    assert app.chat_message[2].markdown[0].value=='What is RAG?'
    assert calls[1][3]=='What is RAG?'
    assert [m['role'] for m in app.session_state['messages']]==['user','assistant','user','assistant']

def test_ui_technical_style_forwarded(ui):
    app,calls,_=ui
    app.selectbox[1].set_value('Technical').run()
    app.chat_input[0].set_value('What is LLM?').run()
    assert not app.exception and calls[-1][4]=='Technical'
def test_ui_feedback_does_not_call_runtime(ui):
    app,calls,_=ui
    app.chat_input[0].set_value('you are wrong').run()
    assert not calls and 'Which claim' in app.chat_message[-1].markdown[0].value

def test_ui_navigation_and_history(ui):
    app,calls,_=ui
    app.chat_input[0].set_value('Question').run()
    app.radio[0].set_value('Learning library').run()
    assert not app.exception and len(app.expander)==6 and not app.chat_input
    app.radio[0].set_value('Why these tools?').run()
    assert not app.exception and len(app.table)==1
    app.radio[0].set_value('Conversation').run()
    assert not app.exception and len(app.chat_message)==2 and len(calls)==1

def test_ui_clear_conversation(ui):
    app,calls,_=ui
    app.chat_input[0].set_value('Question').run()
    app.button[0].click().run()
    assert not app.exception and not app.chat_message and app.session_state['previous_question']==''
def test_ui_manifest_missing_disables_question(ui):
    app,_,p=ui;p.unlink();app.run()
    assert not app.exception and app.chat_input[0].disabled

def test_ui_provider_failure_is_safe(ui,monkeypatch):
    app,_,_=ui
    import luma.runtime as rt
    def fail(c):raise RuntimeError('DO_NOT_DISPLAY_PROVIDER_DETAIL')
    monkeypatch.setattr(rt,'create_runtime',fail)
    app.chat_input[0].set_value('Question').run()
    assert not app.exception
    text=app.chat_message[-1].markdown[0].value
    assert 'couldn’t complete' in text and 'DO_NOT_DISPLAY' not in text

@pytest.mark.parametrize('change',['add','replace','remove'])
def test_document_changes_produce_new_snapshot(tmp_path,monkeypatch,change):
    from luma.config import COLLECTIONS
    from luma.documents import load_documents,split_documents,snapshot_hash
    monkeypatch.setitem(COLLECTIONS,'ai',tmp_path)
    (tmp_path/'first.md').write_text('A lesson about embeddings and semantic document search.')
    (tmp_path/'second.md').write_text('A lesson about retrieval augmented generation.')
    def snapshot():return snapshot_hash(split_documents(load_documents('ai')),'test-model')
    before=snapshot()
    if change=='add':(tmp_path/'third.md').write_text('A lesson about AI agents.')
    elif change=='replace':(tmp_path/'first.md').write_text('A replacement lesson about tokenization.')
    else:(tmp_path/'second.md').unlink()
    assert snapshot()!=before

def test_ingestion_write_failure_preserves_active_manifest(tmp_path,monkeypatch):
    import ingest
    from luma.config import COLLECTIONS
    docs=tmp_path/'docs';docs.mkdir();(docs/'lesson.md').write_text('A public lesson about embeddings.')
    monkeypatch.setitem(COLLECTIONS,'ai',docs)
    manifest=tmp_path/'ai.json';manifest.write_text('{"namespace":"previous-active"}')
    monkeypatch.setattr(ingest,'manifest_path',lambda c:manifest)
    emb=SimpleNamespace(model='test-model',embed_query=lambda q:[1.,0.])
    monkeypatch.setattr(ingest,'embeddings',lambda:emb)
    class PC:
        def has_index(self,name):return True
        def describe_index(self,name):return SimpleNamespace(status={'ready':True},dimension=2,metric='cosine',host='not-a-real-host')
        def Index(self,**kw):return object()
    monkeypatch.setattr(ingest,'pinecone_client',PC)
    class FailingStore:
        def add_documents(self,*a,**kw):raise RuntimeError('simulated upload failure')
    monkeypatch.setattr(ingest,'vector_store',lambda *a:FailingStore())
    with pytest.raises(RuntimeError,match='simulated'):ingest.ingest('ai')
    assert json.loads(manifest.read_text())['namespace']=='previous-active'

def test_ingestion_success_creates_manifest_after_readable_writes(tmp_path,monkeypatch):
    import ingest
    from luma.config import COLLECTIONS
    docs=tmp_path/'docs';docs.mkdir();(docs/'lesson.md').write_text('A public lesson about embeddings.')
    monkeypatch.setitem(COLLECTIONS,'ai',docs)
    manifest=tmp_path/'ai.json'
    monkeypatch.setattr(ingest,'manifest_path',lambda c:manifest)
    emb=SimpleNamespace(model='test-model',embed_query=lambda q:[1.,0.])
    monkeypatch.setattr(ingest,'embeddings',lambda:emb)
    class Index:
        def fetch(self,ids,namespace):return SimpleNamespace(vectors={i:object() for i in ids})
    class PC:
        def has_index(self,name):return True
        def describe_index(self,name):return SimpleNamespace(status={'ready':True},dimension=2,metric='cosine',host='not-a-real-host')
        def Index(self,**kw):return Index()
    class Store:
        def add_documents(self,*a,**kw):assert not manifest.exists()
    monkeypatch.setattr(ingest,'pinecone_client',PC)
    monkeypatch.setattr(ingest,'vector_store',lambda *a:Store())
    ingest.ingest('ai')
    data=json.loads(manifest.read_text())
    assert data['chunk_count']==1 and data['dimension']==2 and data['namespace'].startswith('luma-ai-')
