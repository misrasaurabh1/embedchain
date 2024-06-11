import hashlib

from langchain_community.document_loaders import Docx2txtLoader

from embedchain.loaders.base_loader import BaseLoader

try:
    from langchain_community.document_loaders import Docx2txtLoader
except ImportError:
    raise ImportError(
        'Docx file requires extra dependencies. Install with `pip install --upgrade "embedchain[dataloaders]"`'
    ) from None
from embedchain.helpers.json_serializable import register_deserializable
from embedchain.loaders.base_loader import BaseLoader


@register_deserializable
class DocxFileLoader(BaseLoader):
    def load_data(self, url):
        """Load data from a .docx file."""
        loader = Docx2txtLoader(url)
        data = loader.load()[0]
        content = data.page_content
        metadata = data.metadata
        metadata["url"] = "local"

        output = [{"content": content, "meta_data": metadata}]
        doc_id = hashlib.sha256(f"{content}{url}".encode()).hexdigest()

        return {
            "doc_id": doc_id,
            "data": output,
        }
