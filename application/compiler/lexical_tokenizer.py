from dataclasses import dataclass
import re


@dataclass
class LexicToken:
    type: str
    value: str
    start: int
    end: int


@dataclass
class MismatchedValueError(Exception):
    data: str


@dataclass
class LexicalTokenizer:
    code: str

    def tokenize(self):
        keywords = {
            "int",
            "var",
            "class",
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
        }

        symbols = {
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
        }

        token_specification = [
            (
                "comments",
                r"//.*|/\*(.|[\r\n])*?\*/",
            ),  # Gets comments till the end of line
            ("skip", r"[\s\t\n]+"),  # Skip over spaces and tabs
            ("keyword", r"|".join(keywords)),
            ("symbol", r"|".join(symbols)),  # Assignment operator
            (
                "mismatch_identifier",
                r"[0-9]+[a-zA-Z_]+[0-9]*",
            ),  # Mismatched identifier, starting with a number
            ("integerConstant", r"\d+"),  # Integer number
            ("identifier", r"[a-zA-Z_0-9]+"),  # Identifier
            ("stringConstant", r'"(.*)"'),  # String constant
            ("mismatch", r"."),  # Any other character
        ]
        tok_regex = "|".join(
            f"(?P<{group_name}>{match})" for group_name, match in token_specification
        )

        for regex_match in re.finditer(tok_regex, self.code):
            result = [
                (k, v) for k, v in regex_match.groupdict().items() if v is not None
            ][0]

            yield LexicToken(
                result[0],
                result[1].replace('"', ""),
                regex_match.start(0),
                regex_match.end(0),
            )


def main():
    statements = """class Point_99 {
        var     a = 8000; // 1aaasasd
        var     b = "100";
        while (a>b) {
            return 0;
        }
    }
    """

    lex_tokenizer = LexicalTokenizer(statements)

    tokens = []

    for token in lex_tokenizer.tokenize():
        if token.type in ["mismatch", "mismatch_identifier"]:
            raise MismatchedValueError(
                f"Token error, input '{token.value}' at position ({token.start} to {token.end}) with type '{token.type}', check constraints!"
            )
        if token.type != "skip":
            tokens.append(token)

    for token in tokens:
        print(token)


if __name__ == "__main__":
    main()
