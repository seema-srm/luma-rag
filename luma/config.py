import os
from pathlib import Path
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT/'.env', override=True)
COLLECTIONS = {'ai': ROOT/'documents/public/ai', 'sdet': ROOT/'documents/public/sdet', 'private': ROOT/'documents/private'}

def required(*names):
    missing = [n for n in names if not os.getenv(n, '').strip()]
    if missing:
        raise ValueError('Fill these values in your local .env: '+', '.join(missing))

def manifest_path(collection):
    if collection not in COLLECTIONS: raise ValueError('Unknown collection')
    return ROOT/'.luma'/f'{collection}.json'
