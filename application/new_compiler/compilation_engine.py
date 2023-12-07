# created code
from lexical_tokenizer import LexicalTokenizer, LexicToken, MismatchedValueError

# built-in
from dataclasses import dataclass
import os, argparse
from enum import Enum

# class syntax
class Position(Enum):
    CURRENT = 0
    NEXT = 1

# functional syntax
Position = Enum('Position', ['CURRENT', 'NEXT'])

@dataclass
class SyntaxToken:
    type: str = None
    value: str = None


@dataclass
class SyntaxError(Exception):
    data: str


@dataclass
class CompilationEngine:
    def __post_init__(self):
        self.syntax_tokens = []
        self.lexical_generator = None
        self.current_token = None
        self.next_token = None
        self.code_line = None
        self.line_number = 1

    def read_lines(self, filename: str):
        with open(filename, 'r') as file:
            for line in file:
                yield line.strip()

    def parse_files(self, path) -> None:
        if os.path.isfile(path):
            base_path = os.path.split(path)
            file_name = base_path[1].split(".")[0]
            with open(f"{path}", "r") as input_fp:
                code_lines = "".join(input_fp.readlines())
            self.tokenize(code_lines)

        else:
            for file in os.listdir(path):
                if file.endswith(".jack"):
                    file_name = file.split(".")[0]
                    with open(f"{path}/{file}", "r") as input_fp:
                        code_lines = "".join(input_fp.readlines())

    """
        Def: parses line into its lexical tokens from the generator object, ignoring 'skip' and 'comments' types, yields a tuple with current and next token respectively
        Params:
            - file_path (type: str)
        Example:
            - CompilationEngine.parse_line('<path to file>')
    """
    def parse_lines(self, file_path: str):
        for line in self.read_lines(file_path):
            print(f"{self.line_number}: {line}")
            lex_tokenizer = LexicalTokenizer(line)

            for token in lex_tokenizer.tokenize():
                if token.type in ["mismatch", "mismatch_identifier"]:
                    raise MismatchedValueError(
                        f"Token error, input '{token.value}' at position ({token.start+1} to {token.end+1}) with type '{token.type}' at line {self.line_number}!"
                    )

                if token.type not in ["skip", "comments"]:
                    self.current_token = self.next_token
                    self.next_token = token
                    yield (self.current_token, self.next_token)

            self.line_number += 1

    def tokenize(self, file_content):
        lexical_tokenizer = LexicalTokenizer(file_content)
        self.lexical_generator = lexical_tokenizer.tokenize()

    def compile_new_class(self):
        self.check_syntax_token_position(Position.NEXT,True,[LexicToken(type="keyword",value='class')])

    def get_position_token(self, position: Position) -> SyntaxToken:
        return self.current_token if position == Position.CURRENT else self.next_token

    def compare_tokens(self, input: LexicToken, position, expected: list) -> bool:
        comparison = False

        for lexic_token in expected:
            if lexic_token.type in ["symbol", "keyword"]:
                comparison = (
                    all(
                        [
                            input.type == lexic_token.type,
                            input.value == lexic_token.value,
                        ]
                    )
                    | comparison
                )
            else:
                comparison = (input.type == lexic_token.type) | comparison

        return comparison

    def check_syntax_token(self, input, expected: list) -> LexicToken:
        if self.compare_tokens(input, expected):
            self.syntax_tokens.append(SyntaxToken(type=input.type, value=input.value))
        else:
            raise SyntaxError(
                f"Incorrect token found, expected: {expected} and got {input}!"
            )

def main():
    arguments_list = [
        {
            "name": "file_path",
            "type": str,
            "help": "specifies the file / directory to be read",
        }
    ]

    parser = argparse.ArgumentParser()

    # if more arguments are used, specifies each of them
    for arg in arguments_list:
        parser.add_argument(arg["name"], type=arg["type"], help=arg["help"])
    # creates argparse object to get arguments
    args = parser.parse_args()

    ce = CompilationEngine()
    lexical_tokens = ce.parse_lines(args.file_path)

    for token in lexical_tokens:
        print(token)

if __name__ == "__main__":
    main()
