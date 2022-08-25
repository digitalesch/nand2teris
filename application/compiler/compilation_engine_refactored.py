# created code
from operator import concat
from posixpath import split
from sys import exc_info
from parser import Parser

# built-in
import argparse, os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Iterable 

@dataclass
class LexicToken():
    type:   str = None
    value:  str = None

'''
    If the parser encounters a terminalElement xxx of type
        keyword, symbol, integer constant, string constant, or identifier,
    the parser generates the output:

    <terminalElement>
        xxx
    </terminalElement>

    If the parser encounter a nonTerminal element of type class declaration, class variable
    declaration, subroutine declaration, parameter list, subroutine body, variable
    declaration, statements, let statement, if statement, while statement,
    do statement, return statement, an expression, a term, or an expression list,
    the parser generates the output:    
    <nonTerminal>
        Recursive output for the non-terminal body
    </nonTerminal>
    where nonTerminal is:
    class, classVarDec, subroutineDec,
    parameterList, subroutineBody,
    varDec; statements, LetStatement,
    ifStatement, whileStatement,
    doStatement, returnStatement;
    expression, term, expressionList
'''
@dataclass
class CompilationEngine():
    xml_tree: ET
    current_token_index : int = 0

    def __post_init__(self):
        self.tokens = self.create_tokens()        

    def create_tokens(self) -> list:
        return [LexicToken(tag.tag, tag.text.strip()) for tag in self.xml_tree.iter() if tag.tag != 'tokens']

    def has_more_tokens(self):
        return True if self.current_token_index < len(self.tokens) else False

    def advance(self) -> LexicToken:
        if self.has_more_tokens():
            self.current_token = self.tokens[self.current_token_index]
            self.current_token_index += 1
            return self.current_token
        else:
            return LexicToken(type='quit',value='end')
        print(f'current token: {self.current_token}')
    
    def return_xml_tag(self, lex_token) -> str:
        translate = {
            "<": '&lt;',
            ">": '&gt;', 
            "'": '&quot;',
            "&": '&amp;'
        }
        return f'<{lex_token.type}> {translate[lex_token.value] if lex_token.value in translate else lex_token.value} </{lex_token.type}>'

    '''
        makes the assumption that, if both parameters are passed, both are compared, otherwise, only individual parameter is compared
        by creating none for input when not passed
        example11:
            current token: LexicToken(type='keyword', value='int')
            compared to: [LexicToken(type=None, value='int'), LexicToken(type=None, value='char'), LexicToken(type=None, value='boolean')]
            second parameter will be compared and will return
            [True,False,False]
        example2:
            current token: LexicToken(type='symbol', value='{')
            compared to: [LexicToken(type='symbol', value='{')]
            both parameters will be compared
            [True]
        example3:
            current token: LexicToken(type='symbol', value='{')
            compared to: [LexicToken(type='symbol', value='}')]
            both parameters will be compared
            [False]
    '''
    def compare_token(self, input: LexicToken, expectation: LexicToken):        
        if any([(input.type if token.type else None)==token.type and (input.value if token.value else None)==token.value for token in expectation]):
            return input
        else:
            # raises excpetion by not having the expected token in code
            raise Exception(f'Expected the following {expectation}, but got {input}')


    '''
        rule: 
    '''
    def compile_class(self):
        pass

    '''
        rule: 
    '''
    def compile_class_var_dec(self):
        pass

    '''
        rule: ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody
    '''
    def compile_subroutine_dec(self):
        print('entered compile_subroutine_dec')
        subroutine_dec = []

        subroutine_dec += [
            self.compare_token(
                self.advance(),
                [                     
                    LexicToken(type='keyword',value='constructor'),
                    LexicToken(type='keyword',value='function'),
                    LexicToken(type='keyword',value='method'),
                ]
            ),
            self.compile_type(),
            self.compare_token(self.advance(),[LexicToken(type='identifier')]),
            self.compare_token(self.advance(),[LexicToken(type='symbol',value='(')]),
        ]
        subroutine_dec.append(self.compile_parameter_list())
        subroutine_dec.append(self.compare_token(self.advance(),[LexicToken(type='symbol',value=')')]))
        subroutine_dec.append(self.compile_subroutine_body())
        
        return subroutine_dec

    '''
        ?: zero or one
        *: zero or more
        rule: (type varName (',' type varName)*)?
        example:
            draw() -> [<parameterList></parameterList>] since no parameter is passed
            draw(int x, int y) -> [
                <parameterList>
                    <keyword> int </keyword>
                    <identifier> x </identifier>
                    <symbol> , </symbol>
                    <keyword> int </keyword>
                    <identifier> y </identifier>
                </parameterList>
            ]
   '''
    def compile_parameter_list(self):
        print('entered compile_parameter_list')
        parameter_list = []

        parameter_list += [
            self.compare_token(
                self.advance(),
                [                     
                    LexicToken(value='int'),
                    LexicToken(value='char'),
                    LexicToken(value='boolean'),
                    LexicToken(type='identifier')
                ]
            ),
            self.compare_token(self.advance(),[LexicToken(type='identifier')])
        ]

        # advances next token, to check if recursion is needed for another parameter
        current_token = self.advance()
        if current_token.value == ',':
            parameter_list.append(self.return_xml_tag(current_token))
            parameter_list += self.compile_parameter_list()
        else:
            # returns to previous token and exits function
            self.current_token_index -= 1
            return parameter_list

        return parameter_list

    '''
        rule:
    '''
    def compile_subroutine_body(self):        
        print('entered compile_subroutine_body')
        subroutine_body = []

        current_token = self.advance()

        if current_token.value in ['constructor','function','method']:
            subroutine_body += [
                self.compare_token(
                    current_token,
                    [                     
                        LexicToken(type='keyword',value='constructor'),
                        LexicToken(type='keyword',value='function'),
                        LexicToken(type='keyword',value='method'),
                    ]
                ),
            ]

    '''
        rule: 'var' type varName (',' varName)* ';'
    '''
    def compile_var_dec(self):
        print('entered compile_var_dec')
        var_dec = []
        var_dec += [
            self.compare_token(self.advance(),[LexicToken(type='keyword',value='var')]),
            self.compile_type()            
        ]

        # starts recursive list of variable names for rule: (',' varName)*
        var_dec += self.compile_var_dec_list()
        var_dec.append(self.compare_token(self.advance(),[LexicToken(type='symbol',value=';')]))

        current_token = self.advance()
        if current_token.value == 'var':
            # returns to var token, so recursion can deal with it
            self.current_token_index -= 1
            var_dec += self.compile_var_dec()
        
        return var_dec

    '''
        rule: varName (',' varName)*
    '''
    def compile_var_dec_list(self):
        print('entered compile_var_dec_list')
        var_dec_list = [
            self.compare_token(self.advance(),[LexicToken(type='identifier')]),
        ]
        
        current_token = self.advance()
        if current_token.value == ',':
            var_dec_list.append(current_token)
            var_dec_list += self.compile_var_dec_list()
        else:
            self.current_token_index -= 1
            return var_dec_list

        return var_dec_list

    '''
        rule: 
    '''
    def compile_statements(self):
        pass

    '''
        rule: 
    '''
    def compile_let(self):
        pass

    '''
        rule: 
    '''
    def compile_if(self):
        pass

    '''
        rule: 
    '''
    def compile_while(self):
        pass

    '''
        rule: 
    '''
    def compile_do(self):
        pass

    '''
        rule: 
    '''
    def compile_return(self):
        pass

    '''
        rule: 
    '''
    def compile_expression(self):
        pass

    '''
        rule: 
            integerConstant | stringConstant | keywordConstant | varName |
            varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
    '''
    def compile_term(self):
        pass

    '''
        rule: 
    '''
    def compile_expression_list(self):
        pass

    '''
        rule: 'int' | 'char' | 'boolean' | className
    '''
    def compile_type(self):
        return self.compare_token(                                
                self.advance(),
                [                     
                    LexicToken(value='int'),                                    
                    LexicToken(value='char'),
                    LexicToken(value='boolean'),
                    LexicToken(value='void'),
                    LexicToken(type='identifier'),
                ]
            )

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

    if os.path.isfile(f'{os.path.join(os.getcwd(),args.file_path)}'):        
        split_path = os.path.split(args.file_path)
        file_path, file_name = split_path[0], split_path[1]
        print(f"{os.path.join(file_path,file_name.split('.')[0])}Tokens.xml")
        tree = ET.parse(f"{os.path.join(file_path,file_name.split('.')[0])}Tokens.xml")
    else:
        file_path = args.file_path
        tree = ET.parse(f'{os.path.join(os.getcwd(),file_path)}/MainTokens.xml')

    ce = CompilationEngine(tree)
    
    for token in ce.tokens:
        print(token)

    class_statments = ce.compile_class_statement()

    print(class_statments)

    flattened_statements = list(ce.flatten_statements(class_statments))
    xml_tree = ET.fromstring(''.join(flattened_statements))

    with open(f"{os.path.join(os.getcwd(),file_path)}/{file_name.split('.')[0]}Syntax.xml",'w') as fp:
        fp.write('\n'.join(flattened_statements)+'\n')


def main():
    # test for parameter list
    ce = CompilationEngine(
        ET.fromstring(
            '''
                <tokens>
                    <keyword> int </keyword>
                    <identifier> length </identifier>
                    <symbol> , </symbol>
                    <keyword> int </keyword>
                    <identifier> width </identifier>
                </tokens>
            '''
        )
    )
    print(ce.compile_parameter_list())

    # Test for var list
    ce = CompilationEngine(
        ET.fromstring(
            '''
                <tokens>
                    <keyword> var </keyword>
                    <keyword> int </keyword>
                    <identifier> width </identifier>
                    <symbol> , </symbol>
                    <identifier> width2 </identifier>
                    <symbol> ; </symbol>
                    <keyword> var </keyword>
                    <keyword> char </keyword>
                    <identifier> test </identifier>
                    <symbol> , </symbol>
                    <identifier> test2 </identifier>
                    <symbol> ; </symbol>
                </tokens>
            '''
        )
    )
    print(ce.compile_var_dec())

    # Test for subroutine declaration
    ce = CompilationEngine(
        ET.fromstring(
            '''
                <tokens>
                    <keyword> constructor </keyword>
                    <keyword> void </keyword>
                    <identifier> teste </identifier>
                    <symbol> ( </symbol>
                    <keyword> char </keyword>
                    <identifier> width2 </identifier>
                    <symbol> ) </symbol>                    
                </tokens>
            '''
        )
    )
    print(ce.compile_subroutine_dec())

if __name__ == "__main__":
    main()