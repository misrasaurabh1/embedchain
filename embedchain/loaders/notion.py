import queue
import hashlib
import logging
import os
from typing import Any, Optional

import requests

from embedchain.helpers.json_serializable import register_deserializable
from embedchain.loaders.base_loader import BaseLoader
from embedchain.utils.misc import clean_string


class NotionDocument:
    """
    A simple Document class to hold the text and additional information of a page.
    """

    def __init__(self, text: str, extra_info: dict[str, Any]):
        self.text = text
        self.extra_info = extra_info


class NotionPageLoader:
    """
    Notion Page Loader.
    Reads a set of Notion pages.
    """

    BLOCK_CHILD_URL_TMPL = "https://api.notion.com/v1/blocks/{block_id}/children"

    def __init__(self, integration_token: Optional[str] = None) -> None:
        """Initialize with Notion integration token."""
        if integration_token is None:
            integration_token = os.getenv("NOTION_INTEGRATION_TOKEN")
            if integration_token is None:
                raise ValueError(
                    "Must specify `integration_token` or set environment " "variable `NOTION_INTEGRATION_TOKEN`."
                )
        self.token = integration_token
        self.headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

    def _read_block(self, block_id: str, num_tabs: int = 0) -> str:
        """Read a block from Notion."""
        done = False
        result_lines_arr = []
        cur_block_id = block_id
        while not done:
            block_url = self.BLOCK_CHILD_URL_TMPL.format(block_id=cur_block_id)
            res = requests.get(block_url, headers=self.headers)
            data = res.json()

            for result in data["results"]:
                result_type = result["type"]
                result_obj = result[result_type]

                cur_result_text_arr = []
                if "rich_text" in result_obj:
                    for rich_text in result_obj["rich_text"]:
                        if "text" in rich_text:
                            text = rich_text["text"]["content"]
                            prefix = "\t" * num_tabs
                            cur_result_text_arr.append(prefix + text)

                result_block_id = result["id"]
                has_children = result["has_children"]
                if has_children:
                    children_text = self._read_block(result_block_id, num_tabs=num_tabs + 1)
                    cur_result_text_arr.append(children_text)

                cur_result_text = "\n".join(cur_result_text_arr)
                result_lines_arr.append(cur_result_text)

            if data["next_cursor"] is None:
                done = True
            else:
                cur_block_id = data["next_cursor"]

        result_lines = "\n".join(result_lines_arr)
        return result_lines

    def load_data(self, page_ids: list[str]) -> list[NotionDocument]:
        docs = []
        for page_id in page_ids:
            page_text = self._read_block(page_id)
            docs.append(NotionDocument(text=page_text, extra_info={"page_id": page_id}))
        return docs


@register_deserializable
class NotionLoader(BaseLoader):
    def load_data(self, page_ids: list[str]) -> list[NotionDocument]:
        docs = []
        for page_id in page_ids:
            page_text = self._read_block(page_id)
            docs.append(NotionDocument(text=page_text, extra_info={"page_id": page_id}))
        return docs


def _read_block(self, block_id: str, num_tabs: int = 0) -> str:
    result_lines_arr = []
    to_process = queue.Queue()
    to_process.put((block_id, num_tabs))

    with requests.Session() as s:
        s.headers.update(self.headers)

        while not to_process.empty():
            cur_block_id, cur_tabs = to_process.get()
            block_url = self.BLOCK_CHILD_URL_TMPL.format(block_id=cur_block_id)
            res = s.get(block_url)
            data = res.json()

            for result in data["results"]:
                result_type = result["type"]
                result_obj = result[result_type]

                cur_result_text_arr = []
                if "rich_text" in result_obj:
                    for rich_text in result_obj["rich_text"]:
                        if "text" in rich_text:
                            text = rich_text["text"]["content"]
                            prefix = "\t" * cur_tabs
                            cur_result_text_arr.append(prefix + text)

                result_block_id = result["id"]
                has_children = result["has_children"]
                if has_children:
                    to_process.put((result_block_id, cur_tabs + 1))

                cur_result_text = "\n".join(cur_result_text_arr)
                result_lines_arr.append(cur_result_text)

            if data["next_cursor"] is not None:
                to_process.put((data["next_cursor"], cur_tabs))

    result_lines = "\n".join(result_lines_arr)
    return result_lines
