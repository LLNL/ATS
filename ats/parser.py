import ast
import itertools
import sys

class AtsCodeParser:
    """Parse ATS code into an ATS consumable format."""

    def __init__(self, code_text: str) -> None:
        self.ast = ast.parse(code_text)
        self.raw_text = code_text
        self.raw_text_dict = dict(enumerate(code_text.split(sep="\n"), 1))

    def _get_node_line_nums(self, node: ast.AST) -> list:
        """Get list of line numbers from node of an abstract syntax tree."""
        return list(range(node.lineno, node.end_lineno + 1))

    def get_code_line_nums(self) -> list:
        """Sorted list of line numbers of executable Python code."""
        line_nums = [self._get_node_line_nums(node) for node in self.ast.body]
        return sorted(itertools.chain.from_iterable(line_nums))

    def get_parsed_text(self) -> str:
        line_nums = self.get_code_line_nums()
        return "\n".join([self.raw_text_dict[num] for num in line_nums])


class AtsFileParser(AtsCodeParser):
    """Parse input files into an ATS consumable format."""

    ATS_HEADER = '#ATS:'

    def __init__(self, filename: str) -> None:
        with open(filename) as _file:
            file_contents = _file.read()
        super().__init__(file_contents)
        self._filename = filename
        lineno_to_text = dict(enumerate(file_contents.split(sep="\n"), 1))
        self.ATS_lines = {lineno: txt for lineno, txt in lineno_to_text.items()
                          if txt.startswith(self.ATS_HEADER)}

    @property
    def filename(self) -> str:
        return self._filename

    def get_ATS_line_nums(self) -> list:
        """Sorted list of line numbers starting with '#ATS:'"""
        return sorted(self.ATS_lines.keys())

    def get_parsed_text(self) -> str:
        line_nums = self.get_ATS_line_nums() + super().get_code_line_nums()
        parsed_text = [self.raw_text_dict[num] for num in sorted(line_nums)]
        return "\n".join(parsed_text)
