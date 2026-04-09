from collections.abc import Generator
from typing import Any, Literal

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from playwright.sync_api import sync_playwright


def run_playwright(uri: str, commands: str, uri_type: Literal["ws", "cdp"]) -> str | bytes:
    with sync_playwright() as p:
        if uri_type == "ws":
            browser = p.chromium.connect(ws_endpoint=uri, timeout=3000)
        else:
            browser = p.chromium.connect_over_cdp(endpoint_url=uri, timeout=3000)
        local_vars = {"browser": browser}
        exec(commands, {}, local_vars)
        result = local_vars.get("result")

    return result


class PlaywrightTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        commands = tool_parameters.get("script")
        result = run_playwright(
            self.runtime.credentials.get("playwright_uri"), commands, self.runtime.credentials.get("uri_type")
        )
        if isinstance(result, str):
            yield self.create_text_message(result)
        elif isinstance(result, bytes):
            if result.startswith(b'\x89PNG\r\n\x1a\n'):
                mime_type = "image/png"
            elif result.startswith(b'%PDF-'):
                mime_type = "application/pdf"
            elif result.startswith(b'PK\x03\x04'):
                mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            else:
                mime_type = "application/octet-stream"
            yield self.create_blob_message(blob=result, meta={"mime_type": mime_type})
        else:
            yield self.create_text_message("Nothing output")
