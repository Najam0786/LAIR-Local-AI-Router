from app.core.settings import settings


class EmbeddingModel:
    """
    Local text embeddings for RAG-lite (I-08), via `fastembed`
    (ONNX runtime, no torch -- a meaningfully lighter dependency than
    `sentence-transformers` for a tool whose own mission is running
    well on ordinary laptops).

    Lazily loaded: the ONNX model is fetched from Hugging Face Hub on
    first real use (a one-time acquisition, the same pattern as an
    LM Studio model download -- not a per-request network call) and
    cached on disk after that. Importing this module, or constructing
    an `EmbeddingModel`, never triggers a download by itself.
    """

    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or settings.RAG_EMBEDDING_MODEL
        self._model = None

    def _ensure_loaded(self):
        if self._model is None:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=self._model_name)

        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        model = self._ensure_loaded()

        return [vector.tolist() for vector in model.embed(texts)]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


default_embedding_model = EmbeddingModel()
