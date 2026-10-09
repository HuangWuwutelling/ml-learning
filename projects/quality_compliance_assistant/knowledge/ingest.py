import json
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    BSHTMLLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma

EMBEDDING_MODEL = 'BAAI/bge-small-zh-v1.5'
KNOWLEDGE_DIR = Path('data/knowledge_sources')
MANIFEST_PATH = Path('knowledge/manifest.json')
CHROMA_DIR = Path('knowledge/chroma_db')
COLLECTION = 'qms_knowledge'
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def load_doc(src: dict) -> list:
    p = KNOWLEDGE_DIR / src['path']
    if src['type'] == 'pdf':
        return PyPDFLoader(str(p)).load()
    if src['type'] == 'html':
        return BSHTMLLoader(str(p)).load()
    if src['type'] == 'md':
        return TextLoader(str(p), encoding='utf-8').load()
    raise ValueError(f'unsupported type: {src["type"]}')


def split_docs(docs: list) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=['\n\n', '\n', '。', '；', '，'],
    )
    return splitter.split_documents(docs)


def main():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True},
    )
    all_chunks = []
    for src in manifest['documents']:
        print(f'[ingest] {src["id"]}...')
        docs = load_doc(src)
        chunks = split_docs(docs)
        for c in chunks:
            c.metadata.update({'doc_id': src['id'], 'title': src['title']})
        all_chunks.extend(chunks)
    print(f'[ingest] total chunks: {len(all_chunks)}')
    Chroma.from_documents(
        all_chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION,
    )
    print(f'[done] persisted to {CHROMA_DIR}')


if __name__ == '__main__':
    main()