import functools
import logging
import os
import subprocess
from pathlib import Path
from docutils import nodes

from sphinx.application import Sphinx as SphinxApp
from sphinx.roles import EmphasizedLiteral


_logger = logging.getLogger(f"sphinx.ext.{__name__}")


@functools.lru_cache
def _get_repo_root() -> Path:
    try:
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
        ).strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Unable to get repository root") from e
    return Path(repo_root).resolve()


class PathRoleBase:
    def __init__(self, base_path=""):
        self.base_path = Path(base_path)

    def validate(self, path: Path) -> None:
        if not path.exists():
            relpath = path.relative_to(self.base_path)
            _logger.warning(
                "path %r does not exist within %r",
                os.fspath(relpath),
                os.fspath(self.base_path),
            )

    def display(self, path: Path, text="") -> str:
        raise NotImplementedError

    def __call__(
        self,
        name: str,
        rawtext: str,
        text: str,
        lineno: int,
        options: dict = None,
        content: list = None,
    ):

        path = self.base_path / text
        self.validate(path)
        path_to_display = self.display(path=path)
        node = nodes.literal(path_to_display, path_to_display)
        return [node], []


class Relpath(PathRoleBase):
    def display(self, path: Path, text="") -> str:
        return os.fspath(path.relative_to(self.base_path))


class Filename(PathRoleBase):
    def validate(self, path: Path) -> None:
        if not path.is_file():
            _logger.warning(
                "No file named %r in directory %r", path.name, os.fspath(path.parent)
            )
        if not path.stat().st_size > 0:
            _logger.warning(
                "File %r in %r exists but it's empty", path.name, os.fspath(path.parent)
            )

    def display(self, path: Path, text="") -> str:
        return path.name


def setup(app: SphinxApp):
    repo_root = _get_repo_root()

    app.add_role("path", Relpath(repo_root))
    app.add_role("filename", Filename(repo_root))
