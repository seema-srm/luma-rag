"""Usage: python ingest.py --collection ai [--dry-run]. Upload is explicit."""
import argparse, json, os, time
from pinecone import ServerlessSpec
from langsmith import tracing_context
from luma.config import manifest_path
from luma.documents import load_documents, split_documents, snapshot_hash
from luma.services import embeddings, pinecone_client, vector_store

def ingest(collection, dry_run=False, upload_private=False):
    chunks=split_documents(load_documents(collection))
    print(f'{len(chunks)} chunks ready from {collection}.')
    if dry_run:
        print('Dry run complete. No API calls, uploads, or model charges.');return
    if collection=='private' and not upload_private:
        raise ValueError('Private import sends text to Fireworks and Pinecone. Use --upload-private only for documents you are permitted to process with these services.')
    # No ingestion traces: avoid recording document contents during import.
    with tracing_context(enabled=False):
        embedding=embeddings(); model=embedding.model
        dimension=len(embedding.embed_query('embedding dimension probe'))
        pc=pinecone_client(); name=os.getenv('PINECONE_INDEX','luma-learning')
        if not pc.has_index(name):
            pc.create_index(name=name,dimension=dimension,metric='cosine',spec=ServerlessSpec(cloud=os.getenv('PINECONE_CLOUD','aws'),region=os.getenv('PINECONE_REGION','us-east-1')))
        deadline=time.monotonic()+120
        while True:
            desc=pc.describe_index(name)
            if desc.status['ready']:break
            if time.monotonic()>deadline:raise TimeoutError('Index is still provisioning. Wait and rerun the import.')
            time.sleep(2)
        if desc.dimension!=dimension or desc.metric!='cosine':
            raise ValueError(f'Index must use cosine and dimension {dimension}. Set PINECONE_INDEX to a new unused name; existing data is not deleted.')
        namespace=f'luma-{collection}-{snapshot_hash(chunks,model)}'
        index=pc.Index(host=desc.host);store=vector_store(index,embedding,namespace)
        for offset in range(0,len(chunks),32):
            batch=chunks[offset:offset+32]
            store.add_documents(batch,ids=[d.metadata['chunk_id'] for d in batch])
            print(f'Uploaded {min(offset+32,len(chunks))}/{len(chunks)} chunks')
        # Do not mark the new snapshot active until writes are readable.
        deadline=time.monotonic()+60
        while True:
            found=index.fetch(ids=[chunks[0].metadata['chunk_id'],chunks[-1].metadata['chunk_id']],namespace=namespace)
            if len(found.vectors)==len(set([chunks[0].metadata['chunk_id'],chunks[-1].metadata['chunk_id']])):break
            if time.monotonic()>deadline:raise TimeoutError('Writes not yet readable. Rerun the import; the old active snapshot has been preserved.')
            time.sleep(2)
        manifest={'collection':collection,'namespace':namespace,'index':name,'embedding_model':model,'dimension':dimension,'chunk_count':len(chunks)}
        path=manifest_path(collection);path.parent.mkdir(exist_ok=True)
        tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(manifest,indent=2));tmp.replace(path)
        print(f'Collection ready: {collection}. Namespace: {namespace}')
        print('Older snapshots are retained in Pinecone; no namespaces were deleted.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--collection',choices=['ai','sdet','private'],default='ai');p.add_argument('--dry-run',action='store_true');p.add_argument('--upload-private',action='store_true');a=p.parse_args()
    try:ingest(a.collection,a.dry_run,a.upload_private)
    except Exception as exc:raise SystemExit(str(exc))
