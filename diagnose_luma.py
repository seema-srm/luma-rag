"""Run from luma-rag: python diagnose_luma.py. One live RAG request."""
import json
import re
from pathlib import Path
import luma.runtime as runtime
from luma.config import manifest_path

print('Luma response diagnostic (keys and raw model content are NOT printed)')
print('Runtime file:', Path(runtime.__file__).name)
print('Active AI manifest present:', manifest_path('ai').exists())
original_factory = runtime.chat_model

def capture_factory():
    model = original_factory()
    fmt = getattr(model, 'kwargs', {}).get('response_format', {})
    print('Structured output mode:', fmt.get('type', 'NOT ENABLED — check services.py replacement'))
    class CapturingModel:
        def invoke(self, messages):
            result = model.invoke(messages)
            metadata = getattr(result, 'response_metadata', {}) or {}
            print('Finish reason:', metadata.get('finish_reason', 'not reported'))
            content = result.content
            print('Content type:', type(content).__name__)
            print('Content character count:', len(content) if isinstance(content, (str, list)) else 'unknown')
            if not isinstance(content, str):
                print('CHECK FAILED: expected string content')
                return result
            content = re.sub(r'^```(?:json)?\s*|\s*```$', '', content.strip())
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as exc:
                print('CHECK FAILED: JSON parsing; position:', exc.pos)
                print('Contains a reasoning wrapper:', '<think>' in content or '</think>' in content)
                return result
            if not isinstance(parsed, dict):
                print('CHECK FAILED: JSON is not an object')
                return result
            print('Required fields present:', {k:k in parsed for k in ['supported','answer','citations']})
            text = parsed.get('answer')
            ids = parsed.get('citations')
            print('Supported field type:', type(parsed.get('supported')).__name__)
            print('Supported value:', parsed.get('supported') if type(parsed.get('supported')) is bool else 'invalid type')
            print('Answer is nonempty text:', isinstance(text,str) and bool(text.strip()))
            print('Citations is a list:', isinstance(ids,list))
            print('Citations are integers:', isinstance(ids,list) and all(type(x) is int for x in ids))
            # Only print integer source references, never arbitrary model strings.
            safe_ids=[x for x in ids if type(x) is int] if isinstance(ids,list) else []
            print('Citation source IDs:',safe_ids)
            inline={int(n) for n in re.findall(r'\[(\d+)\]',text)} if isinstance(text,str) else set()
            print('Inline [number] source IDs:', sorted(inline))
            try:
                payload=json.loads(messages[-1].content)
                valid={s['id'] for s in payload['sources']}
                print('Available source IDs:',sorted(valid))
                print('Citations reference available sources:',bool(safe_ids) and set(safe_ids)<=valid)
                print('Inline citations match listed IDs:',bool(inline) and inline<=set(safe_ids) and inline<=valid)
            except (ValueError,TypeError,KeyError):
                print('Could not inspect request source IDs')
            return result
    return CapturingModel()

runtime.chat_model=capture_factory
try:
    graph=runtime.create_runtime('ai')
    result=runtime.ask(graph,'What is RAG?','ai')
    print('Workflow steps:', ', '.join(result.get('trace_steps',[])))
    print('Answer passed validation:', 'citation_format_check' in result.get('trace_steps',[]))
except Exception as exc:
    print('Request failed with error type:', type(exc).__name__)
    print('Raw exception omitted to avoid exposing credentials or provider data.')
print('Diagnostic complete. Share this terminal output; do not share .env.')
