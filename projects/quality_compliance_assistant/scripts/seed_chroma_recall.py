import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qms_project.settings')
django.setup()
from qms_app.models import Recall
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from pathlib import Path

CHROMA_DIR = str(Path('knowledge/chroma_db'))
EMBEDDING_MODEL = 'BAAI/bge-small-zh-v1.5'

embeddings = HuggingFaceBgeEmbeddings(model_name=EMBEDDING_MODEL,
                                      model_kwargs={'device': 'cpu'},
                                      encode_kwargs={'normalize_embeddings': True})

docs = [Document(page_content=f'{r.product.name} {r.defect_description} {r.consequence}',
                 metadata={'recall_id': str(r.id), 'source_type': r.source_type,
                           'product': r.product.name})
        for r in Recall.objects.all()]
print(f'[seed_chroma] {len(docs)} recalls to index')
if docs:
    Chroma.from_documents(docs, embedding=embeddings, persist_directory=CHROMA_DIR,
                          collection_name='recall_history')
    print('[done] recall_history collection populated')
