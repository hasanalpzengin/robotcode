from pathlib import Path
from typing import Any, Iterable, Iterator, Tuple, Union

import pytest
import yaml

from robotcode.core.lsp.types import (
    ClientCapabilities,
    FoldingRangeClientCapabilities,
    TextDocumentClientCapabilities,
)
from robotcode.core.text_document import TextDocument
from robotcode.language_server.robotframework.protocol import (
    RobotLanguageServerProtocol,
)
from tests.robotcode.language_server.robotframework.tools import (
    GeneratedTestData,
    generate_test_id,
    generate_tests_from_source_document,
)

from .pytest_regtestex import RegTestFixtureEx


def prepend_protocol_data(
    protocol: Iterable[Any],
    data: Iterable[Union[Tuple[Any, Path, GeneratedTestData], Any]],
) -> Iterator[Union[Tuple[Any, Path, GeneratedTestData], Any]]:
    for p in protocol:
        for d in data:
            yield (p, *d)


def generate_foldingrange_test_id(params: Any) -> Any:
    if (
        isinstance(params, ClientCapabilities)
        and params.text_document is not None
        and params.text_document.folding_range is not None
    ):
        return params.text_document.folding_range.line_folding_only

    return generate_test_id(params)


@pytest.mark.parametrize(
    ("protocol", "test_document", "data"),
    prepend_protocol_data(
        [
            ClientCapabilities(
                text_document=TextDocumentClientCapabilities(
                    folding_range=FoldingRangeClientCapabilities(line_folding_only=True)
                )
            ),
            ClientCapabilities(
                text_document=TextDocumentClientCapabilities(
                    folding_range=FoldingRangeClientCapabilities(line_folding_only=False)
                )
            ),
        ],
        list(generate_tests_from_source_document(Path(Path(__file__).parent, "data/tests/foldingrange.robot"))),
    ),
    indirect=["protocol", "test_document"],
    ids=generate_foldingrange_test_id,
    scope="module",
)
def test(
    regtest: RegTestFixtureEx,
    protocol: RobotLanguageServerProtocol,
    test_document: TextDocument,
    data: GeneratedTestData,
) -> None:
    result = protocol.robot_folding_ranges.collect(protocol.robot_folding_ranges, test_document)

    if result is not None:
        result = [
            r
            for r in result
            if ("start" in data.name.lower() and r.start_line == data.line)
            or (
                "end" in data.name.lower()
                and r.end_line
                == data.line
                - (0 if ("else" in data.name.lower() or "if" in data.name.lower() or "for" in data.name.lower()) else 1)
            )
        ]

    regtest.write(yaml.dump({"data": data, "result": result}))
