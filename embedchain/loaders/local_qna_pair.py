import hashlib

from embedchain.helpers.json_serializable import register_deserializable
from embedchain.loaders.base_loader import BaseLoader


@register_deserializable
class LocalQnaPairLoader(BaseLoader):
    def load_data(self, content):
        """Load data from a local QnA pair."""
        question, answer = content
        metadata = {"url": "local", "question": question}
        complete_content = f"Q: {question}\nA: {answer}local"
        doc_id = hashlib.sha256(complete_content.encode()).hexdigest()
        return {
            "doc_id": doc_id,
            "data": [
                {
                    "content": complete_content[:-5],  # Remove added 'local'
                    "meta_data": metadata,
                }
            ],
        }
