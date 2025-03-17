from typing import List

import faiss
import nltk
import numpy as np

from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer

from .models import Document, DocumentEmbedding


class RAGEngine:
    def __init__(self):
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        # Download required NLTK data
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt")
        self.index = None     # Initialize FAISS index
        self.chunks = []
        self.dimension = 384  # Dimension of embeddings from all-MiniLM-L6-v2

    def process_document(self, text: str, document: Document = None, chunk_size: int = 3) -> None:
        """
        Process document text into chunks and create embeddings.
        """
        sentences = sent_tokenize(text)

        chunks = []
        for i in range(0, len(sentences), chunk_size):
            chunk = " ".join(sentences[i : i + chunk_size])
            chunks.append(chunk)
        embeddings = self.encoder.encode(chunks)

        if document:
            document.text_chunks = chunks
            document.save()

            for i, embedding in enumerate(embeddings):
                DocumentEmbedding.objects.create(
                    document=document, chunk_index=i, embedding=embedding.tolist()
                )

        if self.index is None:
            self.index = faiss.IndexFlatL2(self.dimension)

        self.index.add(np.array(embeddings).astype("float32"))
        self.chunks = chunks

    def get_relevant_chunks(self, query: str, k: int = 3) -> List[str]:
        """
        Retrieve the k most relevant chunks for a given query.
        """
        query_embedding = self.encoder.encode([query])
        distances, indices = self.index.search(np.array(query_embedding).astype("float32"), k)
        return [self.chunks[i] for i in indices[0]]

    def get_context_for_query(self, query: str, k: int = 3) -> str:
        """
        Get concatenated context from relevant chunks.
        """
        relevant_chunks = self.get_relevant_chunks(query, k)
        return "\n".join(relevant_chunks)

    def reset_index(self) -> None:
        """
        Reset the FAISS index and chunks.
        """
        if self.index is not None:
            self.index.reset()
        self.chunks = []
