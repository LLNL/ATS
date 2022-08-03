import ast
import itertools
from pathlib import Path
import re
import sys

class AtsCodeParser:
    """Parse ATS code into an ATS consumable format."""

    def __init__(self, code_text: str) -> None:
        self.ast = ast.parse(code_text)
        self.raw_text = code_text
        self.raw_text_dict = dict(enumerate(code_text.splitlines(), 1))
        self._parsed_text = ''

    @property
    def parsed_text(self) -> str:
        """Filters out comments and other lines determined non-executable."""
        if not self._parsed_text:
            line_nums = self._get_code_line_nums()
            self._parsed_text = "\n".join([self.raw_text_dict[num]
                                           for num in line_nums])
        return self._parsed_text

    def _get_code_line_nums(self) -> list:
        """Sorted list of line numbers of executable Python code."""
        line_nums = [self._get_node_line_nums(node) for node in self.ast.body]
        return sorted(itertools.chain.from_iterable(line_nums))

    def _get_node_line_nums(self, node: ast.AST) -> list:
        """Get list of line numbers from node of an abstract syntax tree."""
        return list(range(node.lineno, node.end_lineno + 1))

    def get_code_iterator(self):
        """Get generator to iterate over code segments. Derived from ast nodes.

        Segments may contain a single line of code for simple expressions or
        multiple lines of code as found in loops and conditional statements."""
        source = self.parsed_text
        return (ast.get_source_segment(source, node) for node in self.ast.body)


class AtsFileParser(AtsCodeParser):
    """Parse input files into an ATS consumable format."""

    ATS_HEADER = '#ATS:'
    PATTERN = re.compile(f'^{ATS_HEADER}', re.MULTILINE)

    def __init__(self, filename: str) -> None:
        with open(filename) as _file:
            text = _file.read()
        self._filename = filename
        self.ATS_lines = {line_number: line_text for line_number, line_text in
                          enumerate(text.splitlines(), 1)
                          if line_text.startswith(self.ATS_HEADER)}
        text_no_ATS_header = re.sub(self.PATTERN, '', text)
        super().__init__(text_no_ATS_header)

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def ATS_line_nums(self) -> list:
        """Sorted list of line numbers starting with '#ATS:'"""
        return sorted(self.ATS_lines.keys())
