import chromadb

from collections.abc import Iterator
from functools import lru_cache
from typing import TypedDict, cast

from chromadb.api.types import Embeddable, EmbeddingFunction, Metadata
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)
from chromadb.utils import embedding_functions
from sentence_transformers import CrossEncoder

from app.common.exceptions import BusinessException
from app.config import BASE_PATH

KB_DIR = BASE_PATH / "data" / "kb"
CHROMA_DIR = BASE_PATH / "data" / "chorma"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"
COLLECTION_NAME = "lab_docs"
BATCH_SIZE = 64
CHUNK_SIZE = 300
CHUNK_OVERLAP = 30


class Candidate(TypedDict):
    text: str
    metadata: Metadata | None
    recall_score: float


class RankedCandidate(TypedDict):
    text: str
    metadata: Metadata | None
    recall_score: float
    rerank_score: float


def _load_data() -> Iterator[dict[str, str]]:
    for file in sorted(KB_DIR.glob("*.md")):
        yield {
            "source": file.name,
            "content": file.read_text(encoding="utf-8"),
        }


def build_chunks(
    content: str, doc_name: str | None = None
) -> tuple[list[str], list[Metadata]]:
    """将 Markdown 文档切分为文本块及对应的元数据。"""
    page_contents: list[str] = []
    metadatas: list[Metadata] = []
    header_to_split_on = [("#", "title"), ("##", "section")]
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=header_to_split_on, strip_headers=False
    )
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "。", "；", "，", " ", ""],
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    header_chunks = md_splitter.split_text(content)
    for chunk in header_chunks:
        metadata: Metadata = {
            "source": doc_name if doc_name else "",
            **chunk.metadata,
        }
        # 过长的块二次切分
        if len(chunk.page_content) > CHUNK_SIZE:
            for j, sub in enumerate(text_splitter.split_text(chunk.page_content)):
                page_contents.append(sub)
                metadatas.append({**metadata, "sub_index": j})
        else:
            page_contents.append(chunk.page_content)
            metadatas.append(metadata)

    return page_contents, metadatas


@lru_cache(maxsize=1)
def _get_embedding_function():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )


@lru_cache(maxsize=1)
def build_vectorstore() -> chromadb.Collection:
    """创建持久化向量集合，并将 Markdown 文件建立索引。"""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        # Chroma's protocol includes images; this embedding function accepts text only.
        embedding_function=cast(
            EmbeddingFunction[Embeddable], _get_embedding_function()
        ),
        configuration={"hnsw": {"space": "cosine"}},
    )

    for doc in _load_data():
        chunks, metadatas = build_chunks(doc["content"], doc["source"])
        for start in range(0, len(chunks), BATCH_SIZE):
            end = start + BATCH_SIZE
            collection.upsert(
                ids=[
                    f"{doc['source']}::{start}{offset:04d}"
                    for offset in range(min(BATCH_SIZE, len(chunks) - start))
                ],
                documents=chunks[start:end],
                metadatas=metadatas[start:end],
            )
    return collection


def recall(
    collection: chromadb.Collection, query: str, top_k: int = 10
) -> list[Candidate]:
    """从向量集合中召回最相关的文本块。"""
    if top_k <= 0:
        return []
    collection_size = collection.count()
    if collection_size == 0:
        return []

    res = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection_size),
    )
    documents = res["documents"]
    metadatas = res["metadatas"]
    distances = res["distances"]

    if documents is None or metadatas is None or distances is None:
        raise BusinessException("向量检索结果缺少必要字段")

    if not documents or not metadatas or not distances:
        return []

    candidates: list[Candidate] = []
    for doc, meta, dist in zip(documents[0], metadatas[0], distances[0]):
        candidates.append(
            {
                "text": doc,
                "metadata": meta,
                "recall_score": float(1 - dist),
            }
        )
    return candidates


@lru_cache(maxsize=1)
def _get_reranker() -> CrossEncoder:
    return CrossEncoder(RERANKER_MODEL_NAME, max_length=512)


def rerank(
    query: str, candidates: list[Candidate], top_n: int = 3
) -> list[RankedCandidate]:
    """对召回的文本块重新排序，并返回得分最高的结果。"""
    if not candidates or top_n <= 0:
        return []
    pairs = [(query, c["text"]) for c in candidates]
    scores = _get_reranker().predict(pairs, batch_size=32)

    ranked_candidates: list[RankedCandidate] = []
    for candidate, score in zip(candidates, scores, strict=True):
        ranked_candidates.append(
            {
                "text": candidate["text"],
                "metadata": candidate["metadata"],
                "recall_score": candidate["recall_score"],
                "rerank_score": float(score),
            }
        )

    return sorted(
        ranked_candidates,
        key=lambda candidate: candidate["rerank_score"],
        reverse=True,
    )[:top_n]


def retrieve(query: str, top_k: int = 10, top_n: int = 5) -> list[RankedCandidate]:
    collection = build_vectorstore()
    candidates = recall(collection, query, top_k)
    return rerank(query, candidates, top_n)


if __name__ == "__main__":
    print(retrieve("实验室开放时间"))
