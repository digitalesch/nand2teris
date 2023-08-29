# created code
from lexical_tokenizer import LexicalTokenizer, LexicToken

# built-in
from dataclasses import dataclass
import os, argparse

@dataclass
class SyntaxToken():
    type:   str = None
    value:  str = None

@dataclass
class SyntaxError(Exception):
    data: str


@dataclass
class CompilationEngine():
    def __post_init__(self):
        self.syntax_tokens = []
        self.lexical_generator = None
        self.current_token = None


    def parse_files(self, path) -> None:
        if os.path.isfile(path):
            base_path = os.path.split(path)
            file_name = base_path[1].split('.')[0]
            with open(f'{path}','r') as input_fp:
                code_lines = ''.join(input_fp.readlines())
            self.tokenize(code_lines)

        else:
            for file in os.listdir(path):
                if file.endswith(".jack"):
                    file_name = file.split('.')[0]
                    with open(f'{path}/{file}','r') as input_fp:
                        code_lines = ''.join(input_fp.readlines())                    

    '''
        Def: gets next lexical token from the generator object, ignoring 'skip' and 'comments' types
        Params:
            - lexical_generator (type: generator)
    '''
    def advance_token(self):
        next_token = next(self.lexical_generator)
        while next_token.type in ['skip','comments']:
            next_token = next(self.lexical_generator)

        self.current_token = next_token

        return next_token

    def tokenize(self, file_content):
        lexical_tokenizer = LexicalTokenizer(file_content)
        self.lexical_generator = lexical_tokenizer.tokenize()
    
    def compare_tokens(self, input: LexicToken, expected: list) -> bool:
        comparison = False

        for lexic_token in expected:
            if lexic_token.type in ['symbol','keyword']:
                comparison = all([input.type == lexic_token.type, input.value == lexic_token.value]) | comparison
            else:
                comparison = (input.type == lexic_token.type) | comparison
        
        return comparison
        
    def check_syntax_token(self, input, expected: list) -> LexicToken:
        if self.compare_tokens(input,expected):
            self.syntax_tokens.append(SyntaxToken(type=input.type, value=input.value))
        else:
            raise SyntaxError(f"Incorrect token found, expected: {expected} and got {input}!")

    def compile_class(self):
        self.check_syntax_token(self.advance_token(),[LexicToken(type='keyword',value='class')])
        self.check_syntax_token(self.advance_token(),[LexicToken(type='identifier',value='')])
        self.check_syntax_token(self.advance_token(),[LexicToken(type='symbol',value='{')])
        self.compile_class_var_dec()
        self.check_syntax_token(self.current_token,[LexicToken(type='symbol',value='}')])
        
    # (',' varName)*;
    def compile_var_name_list(self):
        # since the ',' (comma) was already processed earlier, it checks the identifier directly
        self.check_syntax_token(self.advance_token(),[LexicToken(type='identifier')])

        if self.compare_tokens(self.advance_token(),[LexicToken(type='symbol',value=',')]):
            self.check_syntax_token(self.current_token,[LexicToken(type='symbol',value=',')])
            # checks for further variables in list
            self.compile_var_name_list()
        else:
            # exits code with ";" (semicolon)
            self.check_syntax_token(self.current_token,[LexicToken(type='symbol',value=';')])

    # (static | field) type varName (',' varName)*;
    def compile_class_var_dec(self):
        self.advance_token()
        # checks if the current token expresses the opening of variable initilization
        if self.compare_tokens(
            self.current_token,
            [
                LexicToken(type='keyword',value='static'),
                LexicToken(type='keyword',value='field')
            ]
        ):
            self.check_syntax_token(
                self.advance_token(),
                [
                    LexicToken(type='keyword',value='int'),
                    LexicToken(type='keyword',value='char'),
                    LexicToken(type='keyword',value='boolean'),
                    LexicToken(type='identifier')
                ]
            ),
            self.check_syntax_token(self.advance_token(),[LexicToken(type='identifier')])
            # continues checking if any there are other classVarDec*
            self.advance_token()
            # checks if current variable definition ended
            if self.compare_tokens(self.current_token,[LexicToken(type='symbol',value=';')]):
                self.check_syntax_token(self.current_token,[LexicToken(type='symbol',value=';')])
                # checks if further variable definitions are made
                self.compile_class_var_dec()
            # checks if its a comma separated variable definition of same type
            if self.compare_tokens(self.current_token,[LexicToken(type='symbol',value=',')]):
                self.check_syntax_token(self.current_token,[LexicToken(type='symbol',value=',')])
                # checks -> (',' varName)*;
                self.compile_var_name_list()
                # checks -> ((static | field) type varName (',' varName)*;)*
                self.compile_class_var_dec()
        

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
    print(args)
    ce = CompilationEngine()
    print(os.path.join(os.getcwd(),args.file_path))

    with open(f'{os.path.join(os.getcwd(),args.file_path)}','r') as input_fp:
        code_lines = ''.join(input_fp.readlines())
        
    print(code_lines)

    ce.tokenize(code_lines)
    ce.compile_class()
    print(ce.syntax_tokens)

if __name__ == "__main__":
    main()