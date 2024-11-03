from pathlib import Path
from textwrap import indent
from typing import Set, Tuple

import click

from robotcode.analyze.config import AnalyzeConfig
from robotcode.core.lsp.types import DiagnosticSeverity
from robotcode.core.text_document import TextDocument
from robotcode.plugin import Application, pass_application
from robotcode.robot.config.loader import (
    load_robot_config_from_path,
)
from robotcode.robot.config.utils import get_config_files

from .__version__ import __version__
from .code_analyzer import CodeAnalyzer


@click.group(
    add_help_option=True,
    invoke_without_command=False,
)
@click.version_option(
    version=__version__,
    package_name="robotcode.analyze",
    prog_name="RobotCode Analyze",
)
@pass_application
def analyze(app: Application) -> None:
    """\
    The analyze command provides various subcommands for analyzing Robot Framework code.
    These subcommands support specialized tasks, such as code analysis, style checking or dependency graphs.
    """


SEVERITY_COLORS = {
    DiagnosticSeverity.ERROR: "red",
    DiagnosticSeverity.WARNING: "yellow",
    DiagnosticSeverity.INFORMATION: "blue",
    DiagnosticSeverity.HINT: "cyan",
}


class Statistic:
    def __init__(self) -> None:
        self.files: Set[TextDocument] = set()
        self.errors = 0
        self.warnings = 0
        self.infos = 0
        self.hints = 0

    def __str__(self) -> str:
        return (
            f"Files: {len(self.files)}, Errors: {self.errors}, Warnings: {self.warnings}, "
            f"Infos: {self.infos}, Hints: {self.hints}"
        )


@analyze.command(
    add_help_option=True,
)
@click.version_option(
    version=__version__,
    package_name="robotcode.analyze",
    prog_name="RobotCode Analyze",
)
@click.option(
    "-f",
    "--filter",
    "filter",
    type=str,
    multiple=True,
    help="""\
        Glob pattern to filter files to analyze. Can be specified multiple times.
        """,
)
@click.argument(
    "paths", nargs=-1, type=click.Path(exists=True, dir_okay=True, file_okay=True, readable=True, path_type=Path)
)
@pass_application
def code(app: Application, filter: Tuple[str], paths: Tuple[Path]) -> None:
    """\
        Performs static code analysis to detect syntax errors, missing keywords or variables,
        missing arguments, and more on the given *PATHS*. *PATHS* can be files or directories.
        If no PATHS are given, the current directory is used.
    """

    config_files, root_folder, _ = get_config_files(
        paths,
        app.config.config_files,
        root_folder=app.config.root,
        no_vcs=app.config.no_vcs,
        verbose_callback=app.verbose,
    )

    try:
        robot_config = load_robot_config_from_path(
            *config_files, extra_tools={"robotcode-analyze": AnalyzeConfig}, verbose_callback=app.verbose
        )

        analyzer_config = robot_config.tool.get("robotcode-analyze", None) if robot_config.tool is not None else None
        if analyzer_config is None:
            analyzer_config = AnalyzeConfig()

        robot_profile = robot_config.combine_profiles(
            *(app.config.profiles or []), verbose_callback=app.verbose, error_callback=app.error
        ).evaluated_with_env()

        statistics = Statistic()
        for e in CodeAnalyzer(
            app=app, config=analyzer_config, robot_profile=robot_profile, root_folder=root_folder
        ).run(paths=paths, filter=filter):
            statistics.files.add(e.document)

            doc_path = e.document.uri.to_path().relative_to(root_folder) if root_folder else e.document.uri.to_path()
            if e.items:

                for item in e.items:
                    severity = item.severity if item.severity is not None else DiagnosticSeverity.ERROR

                    if severity == DiagnosticSeverity.ERROR:
                        statistics.errors += 1
                    elif severity == DiagnosticSeverity.WARNING:
                        statistics.warnings += 1
                    elif severity == DiagnosticSeverity.INFORMATION:
                        statistics.infos += 1
                    elif severity == DiagnosticSeverity.HINT:
                        statistics.hints += 1

                    app.echo(
                        f"{doc_path}:{item.range.start.line + 1}:{item.range.start.character + 1}: "
                        + click.style(f"[{severity.name[0]}] {item.code}", fg=SEVERITY_COLORS[severity])
                        + f": {indent(item.message, prefix='  ').strip()}",
                    )

        statistics_str = str(statistics)
        if statistics.errors > 0:
            statistics_str = click.style(statistics_str, fg="red")

        app.echo(statistics_str)

        app.exit(statistics.errors)

    except (TypeError, ValueError) as e:
        raise click.ClickException(str(e)) from e
