import json
from types import SimpleNamespace
import pytest
from langchain_core.documents import Document
from luma.graph import build_graph, normalize_query
from luma.documents import load_documents, split_documents, snapshot_hash
from luma.config import COLLECTIONS

class Store:
    def __init__(self, score=.9):self.score=score;self.calls=[]
    def similarity_search_with_score(self,q,k):
        self.calls.append(q)
        return [(Document(page_content='RAG retrieves evidence before generating an answer.',metadata={'title':'RAG','source':'rag.md','chunk_id':'sample'}),self.score)]
class Model:
    def __init__(self,content):self.content=content;self.calls=0
    def invoke(self,messages):self.calls+=1;return SimpleNamespace(content=self.content)
def invoke(graph,q='What is RAG?',previous=''):
    return graph.invoke({'question':q,'previous_question':previous,'style':'Beginner-friendly','sources':[]})

def test_feedback_never_calls_paid_services():
    def forbidden():raise AssertionError('Paid service was called')
    result=invoke(build_graph(forbidden,forbidden),'you are wrong')
    assert result['sources']==[] and 'Which claim' in result['answer']

def test_low_score_abstains_without_generation():
    s=Store(.1)
    def forbidden():raise AssertionError('Model was called')
    r=invoke(build_graph(lambda:s,forbidden));assert 'could not find' in r['answer']

def test_cited_generation():
    m=Model(json.dumps({'supported':True,'answer':'RAG retrieves evidence [1].','citations':[1]}));s=Store()
    r=invoke(build_graph(lambda:s,lambda:m));assert r['answer'].endswith('[1].');assert r['sources'][0]['id']==1

@pytest.mark.parametrize('content',[
    '{"supported":true,"answer":"Invented [99]","citations":[99]}',
    'not json',
    '{"supported":true,"answer":"Unlisted [1]","citations":[]}',
])
def test_invalid_citation_or_output_is_not_shown(content):
    r=invoke(build_graph(lambda:Store(),lambda:Model(content)));assert 'did not pass' in r['answer']

def test_model_can_abstain_even_when_vectors_match():
    r=invoke(build_graph(lambda:Store(),lambda:Model('{"supported":false,"answer":"Not covered","citations":[]}')))
    assert r['sources']==[] and 'not find enough' in r['answer']

def test_followup_contains_prior_topic():
    assert 'embeddings' in normalize_query('Explain it more simply','What are embeddings?')
    assert normalize_query('What is testing?','What is RAG?')=='What is testing?'

def test_snapshot_and_collections_are_distinct():
    ai=split_documents(load_documents('ai'));sdet=split_documents(load_documents('sdet'))
    assert ai and sdet
    assert {d.metadata['collection'] for d in sdet}=={'sdet'}
    assert snapshot_hash(ai,'model')!=snapshot_hash(sdet,'model')
    assert snapshot_hash(ai,'model')!=snapshot_hash(ai,'other-model')

def test_private_import_dry_run_does_not_upload(tmp_path,monkeypatch):
    import ingest
    (tmp_path/'note.txt').write_text('A private lesson on embeddings.')
    monkeypatch.setitem(COLLECTIONS,'private',tmp_path)
    def forbidden():raise AssertionError('Network call attempted')
    monkeypatch.setattr(ingest,'embeddings',forbidden)
    ingest.ingest('private',dry_run=True)
    with pytest.raises(ValueError,match='--upload-private'):ingest.ingest('private')

def test_docx_and_empty_pdf_handling(tmp_path,monkeypatch):
    from docx import Document as Word
    from pypdf import PdfWriter
    d=Word();d.add_paragraph('Boundary value analysis checks edges.');d.save(tmp_path/'lesson.docx')
    monkeypatch.setitem(COLLECTIONS,'private',tmp_path)
    assert 'Boundary' in load_documents('private')[0].page_content
    pdf=PdfWriter();pdf.add_blank_page(width=200,height=200)
    with (tmp_path/'scan.pdf').open('wb') as f:pdf.write(f)
    with pytest.raises(ValueError,match='OCR'):load_documents('private')


def test_valid_source_ids_without_inline_refs_receive_sources_footer():
    # The restored application intentionally supplies this footer. This tests
    # presentation/reference validity, not semantic support of the answer.
    result=invoke(build_graph(lambda:Store(),lambda:Model(
        '{"supported":true,"answer":"RAG retrieves evidence.","citations":[1]}'
    )))
    assert result['answer']=='RAG retrieves evidence.\n\nSources: [1]'
    assert [source['id'] for source in result['sources']]==[1]
    assert 'citation_format_check' in result['trace_steps']
