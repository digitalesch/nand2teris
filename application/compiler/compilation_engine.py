# created code
from parser import Parser

# built-in
import argparse, os
import xml.etree.ElementTree as ET
from dataclasses import dataclass

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

    def return_xml_tag(self, lex_token):
        return f'<{lex_token.type}> {lex_token.value} </{lex_token.type}>'

    def compare_token(self, input: LexicToken, expectation: LexicToken):
        _tmpLexToken = LexicToken(input.type,input.value)
        
        if expectation.type == True:
            _tmpLexToken.type = True
        if expectation.value == True:
            _tmpLexToken.value = True
        if all([_tmpLexToken.type == expectation.type, _tmpLexToken.value == expectation.value]):
            return input
        
        return 

    # a ideia é diferente aqui, só precisa compilar os termos que vai achando, não comparar com a gramática em si
    def compile_class_statement(self):
        return [
            self.return_xml_tag(self.compare_token(self.eat_token(),LexicToken(type='keyword',value='class'))),
            self.return_xml_tag(self.compile_terminal_element(self.eat_token())),
            self.return_xml_tag(self.compare_token(self.eat_token(),LexicToken(type='symbol',value='{'))),
            self.compile_var_class_dec(),
            self.return_xml_tag(self.compare_token(self.eat_token(),LexicToken(type='symbol',value='}'))),
        ]

    def compile_n_rules(self):
        pass

    def compile_or_token(self, lex_token: LexicToken, possible_values: list):
        for item in possible_values:
            if self.compare_token(lex_token,LexicToken(type=item.type,value=item.value)):
                return lex_token
        
        #raise Exception('Teste')

    def compile_var_class_dec(self):
        return [
            self.return_xml_tag(self.compile_or_token(self.eat_token(), [LexicToken(type='keyword',value='static'),LexicToken(type='keyword',value='field')])),
            self.return_xml_tag(self.compile_or_token(self.eat_token(), [LexicToken(type='keyword',value='int'),LexicToken(type='keyword',value='char'),LexicToken(type='keyword',value='boolean')])),
            self.return_xml_tag(self.compare_token(self.eat_token(),LexicToken(type='identifier',value=True))),
            self.return_xml_tag(self.compare_token(self.eat_token(),LexicToken(type='symbol',value=';'))),
        ]

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

    print(f'{os.path.join(os.getcwd(),args.file_path)}/MainTokens.xml')

    tree = ET.parse(f'{os.path.join(os.getcwd(),args.file_path)}/MainTokens.xml')

    ce = CompilationEngine(tree)
    
    #tokens =  ce.create_tokens()
    print(ce.tokens)
    for token in ce.tokens:
        print(token,ce.is_terminal_element(token))
    #print([ce.is_terminal_element(token) for token in ce.tokens])

    #print(ce.compile_class_statement())

if __name__ == "__main__":
    main()