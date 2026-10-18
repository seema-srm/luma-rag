"""Public AI sample evaluation. Sends questions, outputs and traces to LangSmith."""
import json, re
from langsmith import Client
from luma.config import ROOT, required
from luma.runtime import create_runtime, ask

def main():
    required('LANGSMITH_API_KEY')
    graph=create_runtime('ai'); client=Client()
    examples=json.loads((ROOT/'evaluation/examples.json').read_text())
    data=[{'inputs':{'question':e['question']},'outputs':e} for e in examples]
    def target(inputs):
        r=ask(graph,inputs['question'],'ai')
        return {'answer':r['answer'],'sources':[{'id':s['id'],'source':s['source']} for s in r.get('sources',[])]}
    def retrieval_hit(inputs,outputs,reference_outputs):
        if reference_outputs.get('expect_feedback'):
            score=not outputs['sources'] and 'Which claim' in outputs['answer']
        else:score=any(reference_outputs['expected_source'] in s['source'] for s in outputs['sources'])
        return {'key':'expected_source_hit','score':int(score)}
    def citation_format(inputs,outputs,reference_outputs):
        if reference_outputs.get('expect_feedback'):return {'key':'citation_format','score':int(not outputs['sources'])}
        cited={int(x) for x in re.findall(r'\[(\d+)\]',outputs['answer'])}
        valid={s['id'] for s in outputs['sources']}
        return {'key':'citation_format','score':int(bool(cited) and cited<=valid)}
    result=client.evaluate(target,data=data,evaluators=[retrieval_hit,citation_format],experiment_prefix='luma-ai-baseline',max_concurrency=1)
    print(result)
if __name__=='__main__':main()
