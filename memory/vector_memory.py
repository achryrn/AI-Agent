# memory/vector_memory.py

from memory.base_memory import Memory
from sentence_transformers import SentenceTransformer, util
from typing import List, Tuple
import torch


class VectorMemory(Memory):
    def __init__(self):
        self.entries: List[Tuple[str, str]] = []  # [(role, content)]
        self.embeddings = []
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def save(self, role: str, content: str, tags: List[str] = None):
        tags = tags or []
        self.entries.append((role, content, tags))
        embedding = self.model.encode(content, convert_to_tensor=True)
        self.embeddings.append(embedding)


    def recall(self, limit=10) -> List[str]:
        return [f"{role}: {text}" for role, text in self.entries[-limit:]]

    def semantic_search(self, query: str, top_k=5, topic: str = None) -> List[str]:
        if not self.entries:
            return []

        query_vec = self.model.encode(query, convert_to_tensor=True)
        scores = util.pytorch_cos_sim(query_vec, torch.stack(self.embeddings))[0]
        top_results = torch.topk(scores, k=min(top_k, len(scores)))

        results = []
        for idx in top_results.indices.tolist():
            role, text, tags = self.entries[idx]
            if topic and topic not in tags:
                continue
            results.append(f"{role}: {text}")
        return results
