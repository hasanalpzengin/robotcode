from __future__ import annotations

import ast
import asyncio
from typing import TYPE_CHECKING, Any, List, Optional

from ....utils.async_tools import check_canceled, threaded
from ....utils.logging import LoggingDescriptor
from ....utils.uri import Uri
from ...common.decorators import language_id
from ...common.lsp_types import (
    Diagnostic,
    DiagnosticSeverity,
    DiagnosticTag,
    Position,
    Range,
)
from ...common.parts.diagnostics import (
    DOCUMENT_DIAGNOSTICS_DEBOUNCE,
    WORKSPACE_DIAGNOSTICS_DEBOUNCE,
    DiagnosticsResult,
)
from ...common.text_document import TextDocument
from ..diagnostics.analyzer import Analyzer
from ..utils.ast_utils import (
    HeaderAndBodyBlock,
    Token,
    range_from_node,
    range_from_token,
)

if TYPE_CHECKING:
    from ..protocol import RobotLanguageServerProtocol

from .protocol_part import RobotLanguageServerProtocolPart


class RobotDiagnosticsProtocolPart(RobotLanguageServerProtocolPart):
    _logger = LoggingDescriptor()

    def __init__(self, parent: RobotLanguageServerProtocol) -> None:
        super().__init__(parent)

        self.source_name = "robotcode.diagnostics"

        parent.diagnostics.collect.add(self.collect_token_errors)
        parent.diagnostics.collect.add(self.collect_model_errors)

        parent.diagnostics.collect.add(self.collect_namespace_diagnostics)

        parent.diagnostics.collect.add(self.collect_unused_references)

        parent.documents_cache.namespace_invalidated.add(self.namespace_invalidated)

        parent.documents.did_change.add(self.documents_did_change)

    async def cache_cleared(self, sender: Any) -> None:
        ...

    @language_id("robotframework")
    async def namespace_invalidated(self, sender: Any, document: TextDocument) -> None:
        await self.parent.diagnostics.create_publish_document_diagnostics_task(
            document,
            wait_time=DOCUMENT_DIAGNOSTICS_DEBOUNCE if document.opened_in_editor else WORKSPACE_DIAGNOSTICS_DEBOUNCE,
        )

    @language_id("robotframework")
    async def documents_did_change(self, sender: Any, document: TextDocument) -> None:
        namespace = await self.parent.documents_cache.get_namespace(document)
        if namespace is None:
            return

        resources = (await namespace.get_resources()).values()
        for res in resources:
            if res.library_doc.source:
                res_document = await self.parent.documents.get(Uri.from_path(res.library_doc.source).normalized())
                if res_document is not None:
                    await self.parent.diagnostics.create_publish_document_diagnostics_task(
                        res_document,
                        wait_time=DOCUMENT_DIAGNOSTICS_DEBOUNCE
                        if res_document.opened_in_editor
                        else WORKSPACE_DIAGNOSTICS_DEBOUNCE,
                    )

    @language_id("robotframework")
    @threaded()
    async def collect_namespace_diagnostics(self, sender: Any, document: TextDocument) -> DiagnosticsResult:
        try:
            namespace = await self.parent.documents_cache.get_namespace(document)
            if namespace is None:
                return DiagnosticsResult(self.collect_namespace_diagnostics, None)

            return DiagnosticsResult(self.collect_namespace_diagnostics, await namespace.get_diagnostisc())
        except (asyncio.CancelledError, SystemExit, KeyboardInterrupt):
            raise
        except BaseException as e:
            self._logger.exception(e)
            return DiagnosticsResult(
                self.collect_namespace_diagnostics,
                [
                    Diagnostic(
                        range=Range(
                            start=Position(
                                line=0,
                                character=0,
                            ),
                            end=Position(
                                line=len(await document.get_lines()),
                                character=len((await document.get_lines())[-1] or ""),
                            ),
                        ),
                        message=f"Fatal: can't get namespace diagnostics '{e}' ({type(e).__qualname__})",
                        severity=DiagnosticSeverity.ERROR,
                        source=self.source_name,
                        code=type(e).__qualname__,
                    )
                ],
            )

    def _create_error_from_node(
        self, node: ast.AST, msg: str, source: Optional[str] = None, only_start: bool = True
    ) -> Diagnostic:
        from robot.parsing.model.statements import Statement

        if isinstance(node, HeaderAndBodyBlock):
            if node.header is not None:
                node = node.header
            elif node.body:
                stmt = next((n for n in node.body if isinstance(n, Statement)), None)
                if stmt is not None:
                    node = stmt

        return Diagnostic(
            range=range_from_node(node, True, only_start),
            message=msg,
            severity=DiagnosticSeverity.ERROR,
            source=source if source is not None else self.source_name,
            code="ModelError",
        )

    def _create_error_from_token(self, token: Token, source: Optional[str] = None) -> Diagnostic:
        return Diagnostic(
            range=range_from_token(token),
            message=token.error if token.error is not None else "(No Message).",
            severity=DiagnosticSeverity.ERROR,
            source=source if source is not None else self.source_name,
            code="TokenError",
        )

    @language_id("robotframework")
    @_logger.call
    async def collect_token_errors(self, sender: Any, document: TextDocument) -> DiagnosticsResult:
        from robot.errors import VariableError
        from robot.parsing.lexer.tokens import Token

        result: List[Diagnostic] = []
        try:
            for token in await self.parent.documents_cache.get_tokens(document):
                await check_canceled()

                if token.type in [Token.ERROR, Token.FATAL_ERROR] and not await Analyzer.should_ignore(
                    document, range_from_token(token)
                ):
                    result.append(self._create_error_from_token(token))

                try:
                    for variable_token in token.tokenize_variables():
                        await check_canceled()
                        if variable_token == token:
                            break

                        if variable_token.type in [Token.ERROR, Token.FATAL_ERROR] and not await Analyzer.should_ignore(
                            document, range_from_token(variable_token)
                        ):
                            result.append(self._create_error_from_token(variable_token))

                except VariableError as e:
                    if not await Analyzer.should_ignore(document, range_from_token(token)):
                        result.append(
                            Diagnostic(
                                range=range_from_token(token),
                                message=str(e),
                                severity=DiagnosticSeverity.ERROR,
                                source=self.source_name,
                                code=type(e).__qualname__,
                            )
                        )
        except (asyncio.CancelledError, SystemExit, KeyboardInterrupt):
            raise
        except BaseException as e:
            return DiagnosticsResult(
                self.collect_token_errors,
                [
                    Diagnostic(
                        range=Range(
                            start=Position(
                                line=0,
                                character=0,
                            ),
                            end=Position(
                                line=len(await document.get_lines()),
                                character=len((await document.get_lines())[-1] or ""),
                            ),
                        ),
                        message=f"Fatal: can't get token diagnostics '{e}' ({type(e).__qualname__})",
                        severity=DiagnosticSeverity.ERROR,
                        source=self.source_name,
                        code=type(e).__qualname__,
                    )
                ],
            )

        return DiagnosticsResult(self.collect_token_errors, result)

    @language_id("robotframework")
    @threaded()
    @_logger.call
    async def collect_model_errors(self, sender: Any, document: TextDocument) -> DiagnosticsResult:

        from ..utils.ast_utils import HasError, HasErrors
        from ..utils.async_ast import iter_nodes

        try:
            model = await self.parent.documents_cache.get_model(document, True)

            result: List[Diagnostic] = []
            async for node in iter_nodes(model):
                error = node.error if isinstance(node, HasError) else None
                if error is not None and not await Analyzer.should_ignore(document, range_from_node(node)):
                    result.append(self._create_error_from_node(node, error))
                errors = node.errors if isinstance(node, HasErrors) else None
                if errors is not None:
                    for e in errors:
                        if not await Analyzer.should_ignore(document, range_from_node(node)):
                            result.append(self._create_error_from_node(node, e))

            return DiagnosticsResult(self.collect_model_errors, result)

        except (asyncio.CancelledError, SystemExit, KeyboardInterrupt):
            raise
        except BaseException as e:
            return DiagnosticsResult(
                self.collect_model_errors,
                [
                    Diagnostic(
                        range=Range(
                            start=Position(
                                line=0,
                                character=0,
                            ),
                            end=Position(
                                line=len(await document.get_lines()),
                                character=len((await document.get_lines())[-1] or ""),
                            ),
                        ),
                        message=f"Fatal: can't get model diagnostics '{e}' ({type(e).__qualname__})",
                        severity=DiagnosticSeverity.ERROR,
                        source=self.source_name,
                        code=type(e).__qualname__,
                    )
                ],
            )

    @language_id("robotframework")
    @threaded()
    @_logger.call
    async def collect_unused_references(self, sender: Any, document: TextDocument) -> DiagnosticsResult:
        try:
            namespace = await self.parent.documents_cache.get_namespace(document)
            if namespace is None:
                return DiagnosticsResult(self.collect_unused_references, None)

            result: List[Diagnostic] = []
            for kw in (await namespace.get_library_doc()).keywords.values():
                references = await self.parent.robot_references.find_keyword_references(document, kw, False)
                if not references and not await Analyzer.should_ignore(document, kw.name_range):
                    result.append(
                        Diagnostic(
                            range=kw.name_range,
                            message=f"Keyword '{kw.name}' is not used.",
                            severity=DiagnosticSeverity.WARNING,
                            source=self.source_name,
                            code="KeywordNotUsed",
                            tags=[DiagnosticTag.Unnecessary],
                        )
                    )
            return DiagnosticsResult(self.collect_unused_references, result)
        except (asyncio.CancelledError, SystemExit, KeyboardInterrupt):
            raise
        except BaseException as e:
            return DiagnosticsResult(
                self.collect_unused_references,
                [
                    Diagnostic(
                        range=Range(
                            start=Position(
                                line=0,
                                character=0,
                            ),
                            end=Position(
                                line=len(await document.get_lines()),
                                character=len((await document.get_lines())[-1] or ""),
                            ),
                        ),
                        message=f"Fatal: can't collect unused references '{e}' ({type(e).__qualname__})",
                        severity=DiagnosticSeverity.ERROR,
                        source=self.source_name,
                        code=type(e).__qualname__,
                    )
                ],
            )
