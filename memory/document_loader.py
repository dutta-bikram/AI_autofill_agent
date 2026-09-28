import json
from pathlib import Path
from typing import List, Dict, Any
from memory.vector_store import RAGMemoryStore
from config import settings

class DocumentLoader:
    """Loads documents from disk into RAGMemoryStore."""

    def __init__(self, vector_store: RAGMemoryStore):
        self.vector_store = vector_store

    def load_file(self, file_path: Path) -> int:
        file_path = Path(file_path)
        if not file_path.exists():
            return 0

        suffix = file_path.suffix.lower()
        content = ""
        metadata = {"filename": file_path.name, "source": str(file_path)}

        try:
            if suffix in [".txt", ".md"]:
                content = file_path.read_text(encoding="utf-8")
            elif suffix == ".json":
                data = json.loads(file_path.read_text(encoding="utf-8"))
                content = json.dumps(data, indent=2)
            else:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"[DocumentLoader] Error reading {file_path}: {e}")
            return 0

        if content.strip():
            count = self.vector_store.add_document(
                doc_id=file_path.stem,
                content=content,
                metadata=metadata
            )
            print(f"[DocumentLoader] Loaded {file_path.name} -> {count} chunk(s)")
            return count
        return 0

    def load_directory(self, dir_path: Path) -> int:
        dir_path = Path(dir_path)
        if not dir_path.exists():
            return 0

        total_chunks = 0
        for p in dir_path.glob("*"):
            if p.is_file() and p.suffix.lower() in [".md", ".txt", ".json"]:
                total_chunks += self.load_file(p)
        return total_chunks
