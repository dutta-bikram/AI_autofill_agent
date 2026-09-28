import os
import re
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import settings

class RAGMemoryStore:
    """Persistent Retrieval-Augmented Generation (RAG) Memory Store for AI Autofill.
    
    Provides vector and semantic retrieval over unstructured documents such as:
    - Resumes & CVs
    - Cover letters & personal statements
    - STAR method interview answers
    - Project deep-dives & technical writeups
    - Past form submissions
    """

    def __init__(self, persist_dir: Optional[Path] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = "user_knowledge_base"
        self.chroma_client = None
        self.collection = None
        
        # In-memory document chunk index (for fast semantic similarity fallback)
        self.chunks: List[Dict[str, Any]] = []

        self._init_backend()

    def _init_backend(self):
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            self.chroma_client = chromadb.PersistentClient(path=str(self.persist_dir))
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print("[RAGMemoryStore] ChromaDB initialized successfully.")
        except Exception as e:
            print(f"[RAGMemoryStore] ChromaDB initialization notice ({e}). Operating in resilient built-in semantic retrieval mode.")
            self.chroma_client = None
            self.collection = None

    def add_document(self, doc_id: str, content: str, metadata: Optional[Dict[str, Any]] = None, chunk_size: int = 400, overlap: int = 60) -> int:
        """Chunks a document and adds it to the persistent memory store."""
        metadata = metadata or {}
        raw_chunks = self._chunk_text(content, chunk_size=chunk_size, overlap=overlap)
        if not raw_chunks:
            return 0

        chunk_ids = []
        chunk_texts = []
        chunk_metas = []

        for i, chunk in enumerate(raw_chunks):
            cid = f"{doc_id}_chunk_{i}"
            meta = {**metadata, "doc_id": doc_id, "chunk_index": i}
            chunk_ids.append(cid)
            chunk_texts.append(chunk)
            chunk_metas.append(meta)
            
            # Keep in-memory cache for fast fallback
            self.chunks.append({
                "id": cid,
                "text": chunk,
                "metadata": meta,
                "tokens": self._tokenize(chunk)
            })

        if self.collection is not None:
            try:
                self.collection.upsert(
                    ids=chunk_ids,
                    documents=chunk_texts,
                    metadatas=chunk_metas
                )
            except Exception as e:
                print(f"[RAGMemoryStore] Warning adding to ChromaDB ({e}). Kept in memory store.")

        return len(chunk_texts)

    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves top-k most relevant context chunks for a given form question."""
        if not query_text.strip():
            return []

        # Attempt ChromaDB query first
        if self.collection is not None:
            try:
                results = self.collection.query(
                    query_texts=[query_text],
                    n_results=min(top_k, max(1, self.collection.count()))
                )
                if results and results.get("documents") and results["documents"][0]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                    distances = results["distances"][0] if results.get("distances") else [0.2] * len(docs)
                    
                    matched = []
                    for doc, meta, dist in zip(docs, metas, distances):
                        # Convert cosine distance to confidence score
                        score = max(0.0, min(1.0, 1.0 - dist))
                        matched.append({
                            "content": doc,
                            "metadata": meta,
                            "score": round(score, 3)
                        })
                    return matched
            except Exception as e:
                print(f"[RAGMemoryStore] ChromaDB query error ({e}). Falling back to semantic TF-IDF matcher.")

        # Resilient fallback: BM25/Cosine token similarity
        return self._fallback_query(query_text, top_k)

    def _fallback_query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_tokens = self._tokenize(query_text)
        if not query_tokens or not self.chunks:
            return []

        scored = []
        for chk in self.chunks:
            score = self._compute_similarity(query_tokens, chk["tokens"])
            if score > 0:
                scored.append({
                    "content": chk["text"],
                    "metadata": chk["metadata"],
                    "score": round(score, 3)
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        words = text.split()
        if not words:
            return []
        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            if end >= len(words):
                break
            start += max(1, chunk_size - overlap)
        return chunks

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\w+", text) if len(w) > 2]

    def _compute_similarity(self, q_tokens: List[str], doc_tokens: List[str]) -> float:
        if not doc_tokens:
            return 0.0
        q_set = set(q_tokens)
        d_set = set(doc_tokens)
        intersection = q_set.intersection(d_set)
        if not intersection:
            return 0.0
        # Jaccard / Cosine blend
        overlap = len(intersection)
        return overlap / (math.sqrt(len(q_set)) * math.sqrt(len(d_set)))

    def clear(self):
        self.chunks.clear()
        if self.collection is not None:
            try:
                self.chroma_client.delete_collection(self.collection_name)
                self.collection = self.chroma_client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                print(f"[RAGMemoryStore] Error clearing ChromaDB: {e}")
