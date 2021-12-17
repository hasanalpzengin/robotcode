from __future__ import annotations

from asyncio import CancelledError
from typing import TYPE_CHECKING, Any, List, Optional

from ....jsonrpc2.protocol import rpc_method
from ....utils.async_tools import CancelationToken, async_tasking_event
from ....utils.logging import LoggingDescriptor
from ..has_extend_capabilities import HasExtendCapabilities
from ..language import language_id_filter
from ..lsp_types import (
    Hover,
    HoverParams,
    Position,
    ServerCapabilities,
    TextDocumentIdentifier,
)
from ..text_document import TextDocument

if TYPE_CHECKING:
    from ..protocol import LanguageServerProtocol

from .protocol_part import LanguageServerProtocolPart


class HoverProtocolPart(LanguageServerProtocolPart, HasExtendCapabilities):

    _logger = LoggingDescriptor()

    def __init__(self, parent: LanguageServerProtocol) -> None:
        super().__init__(parent)

    @async_tasking_event
    async def collect(
        sender, document: TextDocument, position: Position, cancel_token: Optional[CancelationToken] = None
    ) -> Optional[Hover]:  # NOSONAR
        ...

    def extend_capabilities(self, capabilities: ServerCapabilities) -> None:
        if len(self.collect):
            capabilities.hover_provider = True

    @rpc_method(name="textDocument/hover", param_type=HoverParams)
    async def _text_document_hover(
        self,
        text_document: TextDocumentIdentifier,
        position: Position,
        cancel_token: Optional[CancelationToken] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[Hover]:

        results: List[Hover] = []

        document = await self.parent.documents.get(text_document.uri)
        if document is None:
            return None

        for result in await self.collect(
            self,
            document,
            position,
            cancel_token=cancel_token,
            callback_filter=language_id_filter(document),
        ):
            if isinstance(result, BaseException):
                if not isinstance(result, CancelledError):
                    self._logger.exception(result, exc_info=result)
            else:
                if result is not None:
                    results.append(result)

        if len(results) > 0 and results[-1].contents:
            # TODO: can we combine hover results?

            return results[-1]

        return None
