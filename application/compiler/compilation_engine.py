# created code
from parser import Parser

# built-in
import argparse, os
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from hypothesis import currently_in_test_context

@dataclass
class LexicToken():
    type:   str
    value:  str

@dataclass
class CompilationEngine():
    xml_tree: ET
    current_token : int = 0

    def __post_init__(self):
        self.tokens = self.create_tokens()

    def create_tokens(self):
        return [LexicToken(tag.tag, tag.text.strip()) for tag in self.xml_tree.iter() if tag.tag != 'tokens']

    def eat_token(self) -> None:
        token = self.tokens[self.current_token]
        self.current_token += 1

        return token


    def is_terminal_element(self, lex_token: LexicToken):        
        return True if lex_token.type in ['keyword','symbol','integerConstant','stringConstant','identifier'] else False

    def compile_element(self, lex_token: LexicToken):
        if self.is_terminal_element:
            return lex_token
        else:
            pass

    def compile_terminal_element(self, lex_token: LexicToken):
        if self.is_terminal_element:
            return lex_token

    def compare_token(self, input: LexicToken, expectation: LexicToken):
        return any([input.type == expectation.type, input.value == expectation.value])

    # a ideia é diferente aqui, só precisa compilar os termos que vai achando, não comparar com a gramática em si
    def compile_class_statement(self):
        return [
            self.compare_token(self.eat_token(),LexicToken(type='keyword',value='class')),
            #self.compile_var_class_dec(code_tokens[1])
        ]

    def compile_var_class_dec(self, code_tokens):
        pass


def main():
    arguments_list = [
        {'name':'file_path','type':str,'help':'specifies the file / directory to be read'}        
    ]

    parser = argparse.ArgumentParser()

    # if more arguments are used, specifies each of them
    for arg in arguments_list:
        parser.add_argument(
            arg['name'],type=arg['type'],help=arg['help']
        )
    # creates argparse object to get arguments
    args = parser.parse_args()

    # Creates instance of parser code
    parsed_tokens = Parser(file_path=os.path.join(os.getcwd(),args.file_path))
    # Parses ".jack" files into XML format
    parsed_tokens.parse_files()

    tree = ET.parse(f'{os.path.join(os.getcwd(),args.file_path)}/MainTokens.xml')

    ce = CompilationEngine(tree)
    
    #tokens =  ce.create_tokens()
    print(ce.tokens)
    for token in ce.tokens:
        print(token,ce.is_terminal_element(token))
    #print([ce.is_terminal_element(token) for token in ce.tokens])

if __name__ == "__main__":
    main()