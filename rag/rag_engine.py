"""
Home Credit AI Voice Agent - RAG Retrieval Engine
Retrieves relevant sections from knowledge.txt based on customer queries.
"""

import os
import re
from typing import List, Tuple

class RAGEngine:
    def __init__(self, knowledge_path: str = None):
        if knowledge_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            knowledge_path = os.path.join(base_dir, "knowledge.txt")
        self.knowledge_path = knowledge_path
        self.sections: List[Tuple[str, str]] = []  # List of (section_header, text)
        self._load_knowledge()

    def _load_knowledge(self):
        """Load sections from knowledge.txt."""
        if not os.path.exists(self.knowledge_path):
            return

        with open(self.knowledge_path, "r", encoding="utf-8") as f:
            content = f.read()

        raw_sections = content.split("[SECTION:")
        for sec in raw_sections:
            if not sec.strip():
                continue
            parts = sec.split("]", 1)
            if len(parts) == 2:
                header = parts[0].strip()
                body = parts[1].strip()
                self.sections.append((header, body))
            else:
                self.sections.append(("GENERAL", sec.strip()))

    def query(self, user_query: str, top_k: int = 2) -> str:
        """
        Retrieves the most relevant knowledge sections matching user_query.
        Returns formatted context string.
        """
        if not user_query or not self.sections:
            return ""

        query_words = set(re.findall(r'\w+', user_query.lower()))
        # Remove common stopwords
        stopwords = {"what", "is", "the", "are", "you", "for", "a", "an", "in", "to", "of", "and", "or", "how", "can", "i", "my", "do", "does", "it"}
        keywords = query_words - stopwords

        if not keywords:
            return ""

        scored_sections = []
        for header, body in self.sections:
            text_lower = (header + " " + body).lower()
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scored_sections.append((score, header, body))

        scored_sections.sort(key=lambda x: x[0], reverse=True)
        top_results = scored_sections[:top_k]

        if not top_results:
            return ""

        context_snippets = []
        for score, header, body in top_results:
            context_snippets.append(f"[{header}]\n{body}")

        return "\n\n".join(context_snippets)

# Global singleton instance for easy import
rag_instance = RAGEngine()

def get_rag_context(query: str) -> str:
    """Helper function to get RAG context for a user utterance."""
    return rag_instance.query(query)
