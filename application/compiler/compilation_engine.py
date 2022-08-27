# created code
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
    current_token: LexicToken = None
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
            print(f'current token is: {self.current_token}')
            return self.current_token
        else:
            return LexicToken(type='quit',value='end')        
    
    def return_xml_tag(self, lex_token) -> str:
        translate = {
            "<": '&lt;',
            ">": '&gt;',
            "'": '&quot;',
            "&": '&amp;'
        }
        print(lex_token)
        if lex_token.type not in ['tag_start','tag_end']:
            return f'<{lex_token.type}> {translate[lex_token.value] if lex_token.value in translate else lex_token.value} </{lex_token.type}>'
        else:
            return f"<{'/' if lex_token.type == 'tag_end' else ''}{lex_token.value}>"

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
        print('entered compile_class_statement compilation')
        class_dec =  [
            LexicToken(type='tag_start',value='class'),
            self.compare_token(self.advance(),[LexicToken(type='keyword',value='class')]),
            self.compare_token(self.advance(),[LexicToken(type='identifier')]),
            self.compare_token(self.advance(),[LexicToken(type='symbol',value='{')]),
            LexicToken(type='tag_start',value='classVarDec'),
            self.compile_class_var_dec(),
            LexicToken(type='tag_end',value='classVarDec'),
            LexicToken(type='tag_start',value='subroutineDec'),
            self.compile_subroutine_dec(),
            LexicToken(type='tag_end',value='subroutineDec'),
            self.compare_token(self.advance(),[LexicToken(type='symbol',value='}')]),
            LexicToken(type='tag_end',value='class')
        ]

        return class_dec

    '''
        rule: 
    '''
    def compile_class_var_dec(self):
        print('entered compile_var_class_dec compilation')
        var_class_dec = []
        
        current_token = self.advance()
        if current_token.value in ['static','field']:
            var_class_dec += [
                current_token,
                self.compare_token(
                    self.advance(),
                    [
                        LexicToken(value='int'),
                        LexicToken(value='char'),
                        LexicToken(value='boolean')
                    ]
                ),                
            ]

            var_class_dec += self.compile_var_dec_list()
            var_class_dec.append(self.compare_token(self.advance(),[LexicToken(type='symbol',value=';')]))
        else:
            self.current_token_index -= 1
            return var_class_dec

        current_token = self.advance()
        # recursevely construct expressions
        if current_token.value in ['static','field']:
            self.current_token_index -= 1
            var_class_dec += self.compile_class_var_dec(),
        else:            
            print('var class dec ended')
            self.current_token_index -= 1

        return var_class_dec

    '''
        rule: ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody
    '''
    def compile_subroutine_dec(self):
        print('entered compile_subroutine_dec')
        subroutine_dec = []

        current_token = self.advance()        
        if all(
            [
                current_token.type in ['keyword'],
                current_token.value in ['constructor','function','method']
            ]
        ):
            subroutine_dec += [
                self.compare_token(
                    current_token,
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
            subroutine_dec += self.compile_parameter_list()
            subroutine_dec.append(self.compare_token(self.advance(),[LexicToken(type='symbol',value=')')]))
            subroutine_dec.append(LexicToken(type='tag_start',value='subroutineBody'))
            subroutine_dec += self.compile_subroutine_body()
            subroutine_dec.append(LexicToken(type='tag_end',value='subroutineBody'))
        else:
            self.current_token_index -= 1

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

        current_token = self.advance()
        if all(
            [
                current_token.type in ['keyword'],
                current_token.value in ['int','char','boolean']
            ]
        ):

            parameter_list += [
                self.compare_token(
                    current_token,
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
        else:
            # returns to previous token and exits function
            self.current_token_index -= 1

        return parameter_list

    '''
        rule: '{' varDec* statements '}'
    '''
    def compile_subroutine_body(self):
        print('entered compile_subroutine_body')
        print(self.current_token)
        subroutine_body = [
            self.compare_token(self.advance(),[LexicToken(type='symbol',value='{')])
        ]

        current_token = self.advance()
        # moves index back, so function can treat it
        self.current_token_index -= 1

        # tests if variable declaration is needed
        if current_token.value == 'var':
            #subroutine_body.append(LexicToken(type='tag_start',value='varDec'))
            subroutine_body += self.compile_var_dec()
            #subroutine_body.append(LexicToken(type='tag_end',value='varDec'))
        
        subroutine_body.append(LexicToken(type='tag_start',value='statements'))
        subroutine_body += self.compile_statements()
        subroutine_body.append(LexicToken(type='tag_end',value='statements'))
        
        return subroutine_body

    '''
        rule: 'var' type varName (',' varName)* ';'
    '''
    def compile_var_dec(self):
        print('entered compile_var_dec')
        var_dec = [LexicToken(type='tag_start',value='varDec')]
        var_dec += [
            self.compare_token(self.advance(),[LexicToken(type='keyword',value='var')]),
            self.compile_type()
        ]

        # starts recursive list of variable names for rule: (',' varName)*
        var_dec += self.compile_var_dec_list()
        var_dec.append(self.compare_token(self.advance(),[LexicToken(type='symbol',value=';')]))
        var_dec.append(LexicToken(type='tag_end',value='varDec'))
        current_token = self.advance()
        # returns to var token, so recursion can deal with it
        self.current_token_index -= 1
        if current_token.value == 'var':            
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

    '''
        rule: letStatement | ifStatment | whileStatment | doStatement | returnStatement
    '''
    # missing null statement
    def compile_statements(self):
        print('entered compile_statements')
        statements = []
        
        current_token = self.advance()
        if current_token.value in ['let','if','while','do','return']:
            print(f'statement_token: {self.current_token}')
            self.current_token_index -= 1
            if self.current_token.value == 'let':
                statements.append(LexicToken(type='tag_start',value='letStatement'))
                statements += self.compile_let()
                statements.append(LexicToken(type='tag_end',value='letStatement'))
            if self.current_token.value == 'if':
                statements.append(LexicToken(type='tag_start',value='ifStatement'))
                statements += self.compile_if()
                statements.append(LexicToken(type='tag_end',value='ifStatement'))
            if self.current_token.value == 'while':
                statements.append(LexicToken(type='tag_start',value='whileStatement'))
                statements += self.compile_while()
                statements.append(LexicToken(type='tag_end',value='whileStatement'))
            if self.current_token.value == 'do':
                statements.append(LexicToken(type='tag_start',value='doStatement'))
                statements += self.compile_do()
                statements.append(LexicToken(type='tag_end',value='doStatement'))
            if self.current_token.value == 'return':
                statements.append(LexicToken(type='tag_start',value='returnStatement'))
                statements += self.compile_return()
                statements.append(LexicToken(type='tag_end',value='returnStatement'))
            
            current_token = self.advance()
            self.current_token_index -= 1

            if current_token.value in ['let','if','while','do','return']:
                statements += self.compile_statements()
        else:
            self.current_token_index -= 1

        return statements

    '''
        rule: 'let' varName('[' expreession ']')? '=' expression ';'
    '''
    def compile_let(self):
        print('entered compile_let')
        let_statement = [
            self.compare_token(self.advance(),[LexicToken(type='keyword',value='let')]),
            self.compare_token(self.advance(),[LexicToken(type='identifier')]),
        ]

        current_token = self.advance()
        
        # checks if expression evaluation is needed
        if current_token.value == '[':
            let_statement.append(self.compare_token(current_token,[LexicToken(type='symbol',value='[')]))
            let_statement += self.compile_expression()
            let_statement.append(self.compare_token(self.advance(),[LexicToken(type='symbol',value=']')]))
        else:
            self.current_token_index -= 1
        let_statement.append(self.compare_token(self.advance(),[LexicToken(type='symbol',value='=')]))
        let_statement += self.compile_expression()

        let_statement.append(self.compare_token(self.advance(),[LexicToken(type='symbol',value=';')]))

        print(let_statement)
        return let_statement

    '''
        rule: 
    '''
    def compile_if(self):
        print('entered if statement')
        if_statement = [
            self.compare_token(self.advance(),[LexicToken(type='keyword',value='if')]),
            self.compare_token(self.advance(),[LexicToken(type='symbol',value='(')]),
        ]

        if_statement += self.compile_expression()
        if_statement += [
            self.compare_token(self.advance(),[LexicToken(type='symbol',value=')')]),
            self.compare_token(self.advance(),[LexicToken(type='symbol',value='{')]),
        ]

        if_statement += self.compile_statements()
        if_statement.append(self.compare_token(self.advance(),[LexicToken(type='symbol',value='}')]))

        current_token = self.advance()
        print(f'if {current_token}')
        # checks if expression evaluation is needed
        if current_token.value == 'else':
            if_statement += [
                current_token,
                self.compare_token(self.advance(),[LexicToken(type='symbol',value='{')])
            ]

            if_statement += self.compile_statements()
            if_statement.append(self.compare_token(self.advance(),[LexicToken(type='symbol',value='}')]))
        else:
            self.current_token_index -= 1            

        return if_statement

    '''
        rule: 
    '''
    def compile_while(self):
        print('entered while statement')
        while_statement = []

        while_statement = [
            self.compare_token(self.advance(),[LexicToken(type='keyword',value='while')]),
            self.compare_token(self.advance(),[LexicToken(type='symbol',value='(')]),
        ]

        while_statement += self.compile_expression()
        while_statement += [
            self.compare_token(self.advance(),[LexicToken(type='symbol',value=')')]),
            self.compare_token(self.advance(),[LexicToken(type='symbol',value='{')]),
        ]

        while_statement += self.compile_statements()
        while_statement.append(self.compare_token(self.advance(),[LexicToken(type='symbol',value='}')]))

        return while_statement

    '''
        rule: 
    '''
    def compile_do(self):
        print('entered do statement')
        return [
            self.compare_token(self.advance(),[LexicToken(type='keyword',value='do')]),
            self.compile_subroutine_call(),
            self.compare_token(self.advance(),[LexicToken(type='symbol',value=';')])
        ]

    '''
        rule: 
    '''
    def compile_return(self):
        print('entered return statement')
        return_statement = []

        return_statement.append(self.compare_token(self.advance(),[LexicToken(type='keyword',value='return')]))
        
        current_token = self.advance()
        # no expression is passed
        #print(current_token)
        if current_token.value == ';':
            return_statement.append(current_token)
        else:
            self.current_token_index -= 1
            return_statement += self.compile_expression()
            return_statement.append(self.compare_token(self.advance(),[LexicToken(type='symbol',value=';')]))

        return return_statement

    '''
        rule: term (op term)*
    '''
    def compile_expression(self):
        print('entered expression compilation')
        expression = [
            LexicToken(type='tag_start',value='expression')
        ]
        # compile term
        expression.append(LexicToken(type='tag_start',value='term'))
        expression += self.compile_term()
        expression.append(LexicToken(type='tag_end',value='term'))

        # compiles possible (op term)
        current_token = self.advance()
        if current_token.value in [
            '+',
            '-',
            '*',
            '/',
            '&',
            '|',
            '<',
            '>',
            '=',
        ]:
            expression.append(current_token)
            expression.append(LexicToken(type='tag_start',value='term'))
            expression.append(self.compile_term())
            expression.append(LexicToken(type='tag_end',value='term'))
        else:
            self.current_token_index -= 1

        expression += [
            LexicToken(type='tag_end',value='expression')
        ]
        print(f'exited expression {expression}')
        return expression

    '''
        rule: 
            integerConstant | stringConstant | keywordConstant | varName |
            varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
    '''
    # no null term possible
    def compile_term(self):
        print('entered compile_term')
        term = []
        print(f'term {term}')
        
        term += [
            self.compare_token(
                self.advance(),
                [                     
                    LexicToken(type='integerConstant'),
                    LexicToken(type='stringConstant'),
                    LexicToken(value='true'),
                    LexicToken(value='false'),
                    LexicToken(value='null'),
                    LexicToken(value='this'),
                    LexicToken(type='identifier'),
                    LexicToken(value='('),
                    LexicToken(value='-'),
                    LexicToken(value='~'),
                ]
            ),
        ]

        # checks for varName | varName '[' expression ']' | subroutineCall rules
        if self.current_token.type == 'identifier':
            # checks next token for 
            current_token = self.advance()

            if current_token.value in ['[', '(', '.']:
                # rule: varName '[' expression ']'
                if current_token.value == '[':
                    term.append(self.compare_token(current_token,[LexicToken(type='symbol',value='[')]))
                    term += self.compile_expression()
                    term.append(self.compare_token(self.advance(),[LexicToken(type='symbol',value=']')]))
                # compile subroutinecall
                if current_token.value == '(':
                    # gets subroutineName | (className | subroutineName) rule
                    self.current_token_index -= 1
                    del term[-1]
                    term += self.compile_subroutine_call()
                if current_token.value == '.':
                    # gets subroutineName | (className | subroutineName) rule
                    self.current_token_index -= 2
                    del term[-1]
                    term += self.compile_subroutine_call()
            else:
                # sets back index, since its only varName and doesn't need to be expanded
                self.current_token_index -= 1
        # checks for unaryOp term rule
        if self.current_token.value in ['-','~']:
            term.append(self.current_token)
            term += self.compile_term()
        # checks for '(' expression ')'
        if self.current_token.value in ['(']:
            term.append(self.current_token)
            term += self.compile_expression()
            term.append(self.compare_token(self.advance(),[LexicToken(type='symbol',value=')')]))

        return term

    '''
        rule: subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')' 
    '''
    def compile_subroutine_call(self):
        print('entered compile_subroutine_call')
        subroutine_call = [self.compare_token(self.advance(),[LexicToken(type='identifier')])]

        # eats next token, to determine if its first or second option of or statement
        current_token = self.advance()

        # first rule
        if current_token.value == '(':
            # appends current token only
            subroutine_call.append(current_token)
        # second rule
        if current_token.value == '.':
            # appends current token and next identifier
            subroutine_call += [
                current_token,
                self.compare_token(self.advance(),[LexicToken(type='identifier')]),
                self.compare_token(self.advance(),[LexicToken(value='(')]),
            ]

        subroutine_call.append(LexicToken(type='tag_start',value='expressionList'))
        subroutine_call += self.compile_expression_list()
        subroutine_call.append(LexicToken(type='tag_end',value='expressionList'))
        subroutine_call.append(self.compare_token(self.advance(),[LexicToken(type='symbol',value=')')]))
        print(subroutine_call)
        return subroutine_call

    '''
        rule: (expression (',' expression)*)?
    '''
    # null expression
    def compile_expression_list(self):
        print('entered compile_expression_list')
        expression_list = []
        
        current_token = self.advance()
        self.current_token_index -= 1
        if any(
            [
                current_token.type in ['integerConstant','stringConstant','identifier'],
                current_token.value in ['true','false','null','this','(','-','~']
            ]
        ):            
            expression_list += self.compile_expression()
            
            current_token = self.advance()
            if current_token.value == ',':
                expression_list.append(current_token)
                expression_list += self.compile_expression_list()
            else:
                self.current_token_index -= 1
        
        return expression_list

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
    
    def flatten_list(self,items):
        for x in items:
            if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
                for sub_x in self.flatten_list(x):
                    yield sub_x
            else:
                yield x

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

    #print(f'{os.path.join(os.getcwd(),args.file_path)}/MainTokens.xml')

    if os.path.isfile(f'{os.path.join(os.getcwd(),args.file_path)}'):
        split_path = os.path.split(args.file_path)
        file_path, file_name = split_path[0], split_path[1]
        print(f"{os.path.join(file_path,file_name.split('.')[0])}Tokens.xml")
        tree = ET.parse(f"{os.path.join(file_path,file_name.split('.')[0])}Tokens.xml")
    else:
        file_path = args.file_path
        tree = ET.parse(f'{os.path.join(os.getcwd(),file_path)}/MainTokens.xml')

    ce = CompilationEngine(tree)
    
    class_statments = ce.compile_class()

    print(class_statments)

    flattened_statements = [ce.return_xml_tag(syntax_token) for syntax_token in ce.flatten_list(class_statments)]
    xml_tree = ET.fromstring(''.join(flattened_statements))

    with open(f"{os.path.join(os.getcwd(),file_path)}/{file_name.split('.')[0]}Syntax.xml",'w') as fp:
        fp.write('\n'.join(flattened_statements)+'\n')


def main2():
    # Test for class statement with var declarations
    ce = CompilationEngine(
        ET.fromstring(
            '''
                <tokens>
                    <keyword> class </keyword>
                    <identifier> Main </identifier>
                    <symbol> { </symbol>
                    <keyword> static </keyword>
                    <keyword> int </keyword>
                    <identifier> a </identifier>
                    <symbol> , </symbol>
                    <identifier> b </identifier>
                    <symbol> ; </symbol>
                    <keyword> function </keyword>
                    <keyword> int </keyword>
                    <identifier> main </identifier>
                    <symbol> ( </symbol>
                    <symbol> ) </symbol>
                    <symbol> { </symbol>
                    <keyword> var </keyword>
                    <keyword> int </keyword>
                    <identifier> i </identifier>
                    <symbol> , </symbol>
                    <identifier> j </identifier>
                    <symbol> ; </symbol>
                    <keyword> do </keyword>
                    <identifier> Game </identifier>
                    <symbol> . </symbol>
                    <identifier> run </identifier>
                    <symbol> ( </symbol>
                    <symbol> ) </symbol>
                    <symbol> ; </symbol>
                    <keyword> do </keyword>
                    <identifier> run </identifier>
                    <symbol> ( </symbol>
                    <symbol> ) </symbol>
                    <symbol> ; </symbol>
                    <keyword> let </keyword>
                    <identifier> a </identifier>
                    <symbol> = </symbol>
                    <integerConstant> 5 </integerConstant>
                    <symbol> ; </symbol>
                    <keyword> if </keyword>
                    <symbol> ( </symbol>
                    <stringConstant> false </stringConstant>
                    <symbol> ) </symbol>
                    <symbol> { </symbol>
                    <keyword> do </keyword>
                    <identifier> Game </identifier>
                    <symbol> . </symbol>
                    <identifier> run </identifier>
                    <symbol> ( </symbol>
                    <symbol> ) </symbol>
                    <symbol> ; </symbol>
                    <symbol> } </symbol>
                    <keyword> else </keyword>
                    <symbol> { </symbol>
                    <keyword> do </keyword>
                    <identifier> Game </identifier>
                    <symbol> . </symbol>
                    <identifier> run </identifier>
                    <symbol> ( </symbol>
                    <symbol> ) </symbol>
                    <symbol> ; </symbol>
                    <symbol> } </symbol>
                    <keyword> while </keyword>
                    <symbol> ( </symbol>
                    <stringConstant> true </stringConstant>
                    <symbol> ) </symbol>
                    <symbol> { </symbol>
                    <keyword> let </keyword>
                    <identifier> a </identifier>
                    <symbol> [ </symbol>
                    <identifier> i </identifier>
                    <symbol> ] </symbol>
                    <symbol> = </symbol>
                    <integerConstant> 1 </integerConstant>
                    <symbol> ; </symbol>
                    <keyword> return </keyword>
                    <stringConstant> true </stringConstant>
                    <symbol> ; </symbol>
                    <symbol> } </symbol>
                    <symbol> } </symbol>
                </tokens>
            '''
        )
    )

    class_definition = ce.compile_class()

    # Test for class statement with var declarations
    ce = CompilationEngine(
        ET.fromstring(
            '''
                <tokens>                    
                    <keyword> let </keyword>
                    <identifier> a </identifier>
                    <symbol> [ </symbol>
                    <identifier> i </identifier>
                    <symbol> ] </symbol>
                    <symbol> = </symbol>
                    <identifier> Keybaord </identifier>
                    <symbol> . </symbol>
                    <identifier> readInt </identifier>
                    <symbol> ( </symbol>
                    <stringConstant> "HOW MANY NUMBERS? " </stringConstant>
                    <symbol> ) </symbol>
                    <symbol> ; </symbol>                    
                </tokens>
            '''
        )
    )

    class_definition = ce.compile_let()
    print(f'Result: {class_definition}')

    print('teste')
    xml_tags = [ce.return_xml_tag(syntax_token) for syntax_token in ce.flatten_list(class_definition)]
    print(''.join(xml_tags))

if __name__ == "__main__":
    main()