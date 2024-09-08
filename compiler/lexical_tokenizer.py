import re
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class LexicToken:
    type: str
    value: Optional[str] = None
    start: int = 0
    end: int = 0


@dataclass
class MismatchedValueError(Exception):
    data: str


@dataclass
class LexicalTokenizer:
    code: str
    keywords: set
    symbols: set
    token_specification: list = field(default_factory=list)

    def tokenize(self):
        token_specification = [
            ("comments",r"//.*|/\*(.|[\r\n])*?\*/"),        # Gets comments till the end of line
            ("skip", r"[\s\t\n]+"),                         # Skip over spaces and tabs
            ("keyword", r"|".join(self.keywords)),          # Keywords
            ("symbol", r"|".join(self.symbols)),            # Symbols
        ] + self.token_specification

        # creates matching groups
        tok_regex = "|".join(
            f"(?P<{group_name}>{match})" for group_name, match in token_specification
        )

        # loops through the matches in the regex
        for regex_match in re.finditer(tok_regex, self.code):
            result = [
                (k, v) for k, v in regex_match.groupdict().items() if v is not None
            ][0]

            token = LexicToken(
                type=result[0],
                value=result[1],
                start=regex_match.start(0),
                end=regex_match.end(0),
            )

            if token.type in ["mismatch", "mismatched_identifier"]:
                raise MismatchedValueError(
                    f"Token error, input '{token.value}' at position ({token.start} to {token.end}) with type '{token.type}', check constraints!"
                )

            yield token


def main():
    statements = """class Point_999 {
        var     a = 8000; // 1aaasasd
        var     b = "100";
        while (a>b) {
            return 0;
        }
    }
    """

    lex_tokenizer = LexicalTokenizer(
        code=statements,
        keywords={
            "int",
            "var",
            "let",
            "return",
            "class",
            "void",
            "function",
            "while",
            "do",
            "static",
            "boolean",
            "if",
            "false",
            "true",
            "null",
            "else",
            "field",
            "constructor",
            "this",
            "method",
            "char",
            "that",
        },
        symbols={
            "\+",
            "\-",
            "\*",
            ";",
            "<",
            ">",
            "=",
            "\|",
            "\&",
            "\,",
            "\.",
            ",",
            "\[",
            "\]",
            "\/",
            "\(",
            "\)",
            "{",
            "}",
            "'",
            "~",
        },
        token_specification=[
            ("mismatched_identifier",r"[0-9]+[a-zA-Z_]+[0-9]*"),    # Mismatched identifier, starting with a number
            ("integerConstant", r"\d+"),                            # Integer number
            ("identifier", r"[a-zA-Z_0-9]+"),                       # Identifier
            ("stringConstant", r'"(.*)"'),                          # String constant
            ("mismatch", r"."),                                     # Any other character
        ],
    )

    for token in lex_tokenizer.create_tokens():
        print(token)


if __name__ == "__main__":
    main()
