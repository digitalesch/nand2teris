from dataclasses import dataclass
from typing import NamedTuple
import re

class Token(NamedTuple):
    type: str
    value: str
    line: int
    column: int

@dataclass
class Tokenizer:
    keywords: dict
    token_specification: list
    line_number: int = 0  

    def tokenize(self,code):
        # creates paring for token_specification passed, so it returns the group name
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in self.token_specification)
        self.line_number = 1
        line_start = 0
        for mo in re.finditer(tok_regex, code):
            kind = mo.lastgroup
            value = mo.group()
            column = mo.start() - line_start
            if kind == 'NUMBER':
                value = float(value) if '.' in value else int(value)
            elif kind == 'ID' and value in self.keywords:
                kind = value
            elif kind == 'NEWLINE':
                line_start = mo.end()
                self.line_number += 1
                continue
            elif kind == 'SKIP':
                continue
            elif kind == 'MISMATCH':
                raise RuntimeError(f'{value!r} unexpected on line {self.line_number}')
            yield Token(kind, value, self.line_number, column)

token_specification = [
            ('NUMBER',   r'@\d+(\.\d*)?'),  # Integer or decimal number
            ('ASSIGN',   r'='),            # Assignment operator
            ('END',      r';'),            # Statement terminator
            ('ID',       r'[A-Za-z]+'),    # Identifiers
            ('OP',       r'[+\-*/]'),      # Arithmetic operators
            ('NEWLINE',  r'\n'),           # Line endings
            ('SKIP',     r'[ \t]+'),       # Skip over spaces and tabs
            ('MISMATCH', r'.'),            # Any other character
        ]

print('|'.join('(?P<%s>%s)' % pair for pair in token_specification))