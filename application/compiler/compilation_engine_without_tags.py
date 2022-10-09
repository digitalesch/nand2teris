# created code
from parser import Parser

# built-in
import argparse, os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Iterable 

def flatten_list(items):
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatten_list(x):
                yield sub_x
        else:
            yield x

@dataclass
class SyntaxToken():
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
    file_path:              str
    current_token:          SyntaxToken = None
    current_token_index:    int = 0

    def __post_init__(self):
        # gets tuple of (file folder, file name with extension)
        self.file_folder, self.file_full_name = os.path.split(self.file_path)
        # file name without extension
        self.file_name = self.file_full_name.split('.')[0]
        # compiles tokens for path
        parser = Parser(self.file_path)
        parser.parse_files()
        # tokenized file name to be searched for compilation
        self.token_file_name = self.file_name + 'Tokens.xml'
        # path for tokenized file
        self.token_file_path = os.path.join(self.file_folder,self.token_file_name)
        # loads up parsed tokenized entry
        self.xml_tree = ET.parse(self.token_file_path)
        # creates tokens
        self.tokens = self.create_tokens()
        # executes compilation of generated tokenized parsed entry
        self.execute_compilation()

    def create_tokens(self) -> list:
        return [SyntaxToken(tag.tag, tag.text) for tag in self.xml_tree.iter() if tag.tag != 'tokens']

    def has_more_tokens(self):
        return True if self.current_token_index < len(self.tokens) else False

    def advance(self) -> SyntaxToken:
        if self.has_more_tokens():
            self.current_token = self.tokens[self.current_token_index]
            self.current_token_index += 1
            return self.current_token
        else:
            return SyntaxToken(type='quit',value='end')        
    
    def return_xml_tag(self, syntax_token: SyntaxToken, full: bool = True) -> str:
        translate = {
            "<": '&lt;',
            ">": '&gt;',
            "'": '&quot;',
            "&": '&amp;'
        }
        if syntax_token.type not in ['tag_start','tag_end']:
            return f'<{syntax_token.type}>{translate[syntax_token.value] if syntax_token.value in translate else syntax_token.value}</{syntax_token.type}>'
        else:
            return f"<{'/' if syntax_token.type == 'tag_end' else ''}{syntax_token.value}>"    

    '''
        makes the assumption that, if both parameters are passed, both are compared, otherwise, only individual parameter is compared
        by creating none for input when not passed
        example11:
            current token: SyntaxToken(type='keyword', value='int')
            compared to: [SyntaxToken(type=None, value='int'), SyntaxToken(type=None, value='char'), SyntaxToken(type=None, value='boolean')]
            second parameter will be compared and will return
            [True,False,False]
        example2:
            current token: SyntaxToken(type='symbol', value='{')
            compared to: [SyntaxToken(type='symbol', value='{')]
            both parameters will be compared
            [True]
        example3:
            current token: SyntaxToken(type='symbol', value='{')
            compared to: [SyntaxToken(type='symbol', value='}')]
            both parameters will be compared
            [False]
    '''
    def compare_token(self, input: SyntaxToken, expectation: SyntaxToken):
        if any([(input.type if token.type else None)==token.type and (input.value if token.value else None)==token.value for token in expectation]):
            return input
        else:
            # raises excpetion by not having the expected token in code
            raise Exception(f'Expected the following {expectation}, but got {input}')


    '''
        rule: 
    '''
    def compile_class(self):
        ##print('entered compile_class_statement compilation')
        class_dec =  [
            SyntaxToken(type='tag_start',value='class'),
            self.compare_token(self.advance(),[SyntaxToken(type='keyword',value='class')]),
            SyntaxToken(type='tag_start',value='className'),                                            # added className tag for easier parsing
            self.compare_token(self.advance(),[SyntaxToken(type='identifier')]),
            SyntaxToken(type='tag_end',value='className'),                                            # added className tag for easier parsing
            self.compare_token(self.advance(),[SyntaxToken(type='symbol',value='{')]),
            self.compile_class_var_dec(),
            self.compile_subroutine_dec(),
            self.compare_token(self.advance(),[SyntaxToken(type='symbol',value='}')]),
            SyntaxToken(type='tag_end',value='class')
        ]

        return class_dec

    '''
        rule: 
    '''
    def compile_class_var_dec(self):
        #print('entered compile_var_class_dec compilation')
        var_class_dec = []
        
        current_token = self.advance()
        if current_token.value in ['static','field']:
            var_class_dec += [
                SyntaxToken(type='tag_start',value='classVarDec'),
                current_token,
                self.compare_token(
                    self.advance(),
                    [
                        SyntaxToken(value='int'),
                        SyntaxToken(value='char'),
                        SyntaxToken(value='boolean'),
                        SyntaxToken(type='identifier')
                    ]
                ),                
            ]
            var_class_dec += [SyntaxToken(type='tag_start',value='classVarDecList'),]
            var_class_dec += self.compile_var_dec_list()
            var_class_dec += [SyntaxToken(type='tag_end',value='classVarDecList'),]
            var_class_dec.append(self.compare_token(self.advance(),[SyntaxToken(type='symbol',value=';')]))
            var_class_dec.append(SyntaxToken(type='tag_end',value='classVarDec'))
        else:
            self.current_token_index -= 1
            return var_class_dec

        current_token = self.advance()
        # recursevely construct expressions
        if current_token.value in ['static','field']:
            self.current_token_index -= 1
            var_class_dec += self.compile_class_var_dec(),
        else:
            #print('var class dec ended')
            self.current_token_index -= 1

        return var_class_dec

    '''
        rule: ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody
    '''
    def compile_subroutine_dec(self):
        #print('entered compile_subroutine_dec')
        subroutine_dec = []

        current_token = self.advance()
        if all(
            [
                current_token.type in ['keyword'],
                current_token.value in ['constructor','function','method']
            ]
        ):
            subroutine_dec += [
                SyntaxToken(type='tag_start',value='subroutineDec'),
                self.compare_token(
                    current_token,
                    [
                        SyntaxToken(type='keyword',value='constructor'),
                        SyntaxToken(type='keyword',value='function'),
                        SyntaxToken(type='keyword',value='method'),
                    ]
                ),
                self.compile_type(),
                SyntaxToken(type='tag_start',value='subroutineName'),                                            # added subroutineName tag for easier parsing
                self.compare_token(self.advance(),[SyntaxToken(type='identifier')]),
                SyntaxToken(type='tag_end',value='subroutineName'),                                            # added subroutineName tag for easier parsing
                self.compare_token(self.advance(),[SyntaxToken(type='symbol',value='(')]),
            ]
            subroutine_dec.append(SyntaxToken(type='tag_start',value='parameterList'))
            subroutine_dec += self.compile_parameter_list()
            subroutine_dec.append(SyntaxToken(type='tag_end',value='parameterList'))
            subroutine_dec.append(self.compare_token(self.advance(),[SyntaxToken(type='symbol',value=')')]))
            subroutine_dec.append(SyntaxToken(type='tag_start',value='subroutineBody'))
            subroutine_dec += self.compile_subroutine_body()
            subroutine_dec.append(SyntaxToken(type='tag_end',value='subroutineBody'))            

            # checks for further subroutines declaratioon
            current_token = self.advance()
            #print(current_token)
            if all(
                [
                    current_token.type in ['keyword'],
                    current_token.value in ['constructor','function','method']
                ]
            ):
                subroutine_dec.append(SyntaxToken(type='tag_end',value='subroutineDec'))
                self.current_token_index -= 1
                subroutine_dec += self.compile_subroutine_dec()
            else:
                subroutine_dec.append(SyntaxToken(type='tag_end',value='subroutineDec'))
                self.current_token_index -= 1
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
        if any(
                [
                    current_token.type in ['keyword'] and current_token.value in ['int','char','boolean'],
                    current_token.type in ['identifier']
                ]            
        ):
            parameter_list += [
                self.compare_token(
                    current_token,
                    [
                        SyntaxToken(value='int'),
                        SyntaxToken(value='char'),
                        SyntaxToken(value='boolean'),
                        SyntaxToken(type='identifier')
                    ]
                ),
                self.compare_token(self.advance(),[SyntaxToken(type='identifier')])
            ]

            # advances next token, to check if recursion is needed for another parameter
            current_token = self.advance()
            if current_token.value == ',':
                parameter_list.append(current_token)
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
        #print('entered compile_subroutine_body')
        #print(self.current_token)
        subroutine_body = [
            self.compare_token(self.advance(),[SyntaxToken(type='symbol',value='{')])
        ]

        current_token = self.advance()
        # moves index back, so function can treat it
        self.current_token_index -= 1

        # tests if variable declaration is needed
        subroutine_body.append(SyntaxToken(type='tag_start',value='subroutineVarDec'))
        if current_token.value == 'var':
            subroutine_body += self.compile_var_dec()
        subroutine_body.append(SyntaxToken(type='tag_end',value='subroutineVarDec'))
        
        subroutine_body.append(SyntaxToken(type='tag_start',value='statements'))
        subroutine_body += self.compile_statements()
        subroutine_body.append(SyntaxToken(type='tag_end',value='statements'))
        
        subroutine_body.append(self.compare_token(self.advance(),[SyntaxToken(type='symbol',value='}')]))

        return subroutine_body

    '''
        rule: 'var' type varName (',' varName)* ';'
    '''
    def compile_var_dec(self):
        #print('entered compile_var_dec')
        var_dec = [SyntaxToken(type='tag_start',value='varDec')]
        #var_dec = []
        var_dec += [
            self.compare_token(self.advance(),[SyntaxToken(type='keyword',value='var')]),
            self.compile_type()
        ]

        # starts recursive list of variable names for rule: (',' varName)*
        var_dec += self.compile_var_dec_list()
        var_dec.append(self.compare_token(self.advance(),[SyntaxToken(type='symbol',value=';')]))
        var_dec.append(SyntaxToken(type='tag_end',value='varDec'))
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
        #print('entered compile_var_dec_list')
        var_dec_list = [
            self.compare_token(self.advance(),[SyntaxToken(type='identifier')]),
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
        #print('entered compile_statements')
        statements = []
        
        current_token = self.advance()
        if current_token.value in ['let','if','while','do','return']:
            #print(f'statement_token: {self.current_token}')
            self.current_token_index -= 1
            if self.current_token.value == 'let':
                statements.append(SyntaxToken(type='tag_start',value='letStatement'))
                statements += self.compile_let()
                statements.append(SyntaxToken(type='tag_end',value='letStatement'))
            if self.current_token.value == 'if':
                statements.append(SyntaxToken(type='tag_start',value='ifStatement'))
                statements += self.compile_if()
                statements.append(SyntaxToken(type='tag_end',value='ifStatement'))
            if self.current_token.value == 'while':
                statements.append(SyntaxToken(type='tag_start',value='whileStatement'))
                statements += self.compile_while()
                statements.append(SyntaxToken(type='tag_end',value='whileStatement'))
            if self.current_token.value == 'do':
                statements.append(SyntaxToken(type='tag_start',value='doStatement'))
                statements += self.compile_do()
                statements.append(SyntaxToken(type='tag_end',value='doStatement'))
            if self.current_token.value == 'return':
                statements.append(SyntaxToken(type='tag_start',value='returnStatement'))
                statements += self.compile_return()
                statements.append(SyntaxToken(type='tag_end',value='returnStatement'))
            
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
        #print('entered compile_let')
        let_statement = [
            self.compare_token(self.advance(),[SyntaxToken(type='keyword',value='let')]),
            SyntaxToken(type='tag_start',value='assignVariable'),
            self.compare_token(self.advance(),[SyntaxToken(type='identifier')]),
        ]

        current_token = self.advance()
        
        # checks if expression evaluation is needed
        if current_token.value == '[':
            let_statement.append(self.compare_token(current_token,[SyntaxToken(type='symbol',value='[')]))
            let_statement += self.compile_expression()
            let_statement.append(self.compare_token(self.advance(),[SyntaxToken(type='symbol',value=']')]))
        else:
            self.current_token_index -= 1
        let_statement.append(SyntaxToken(type='tag_end',value='assignVariable'))
        let_statement.append(self.compare_token(self.advance(),[SyntaxToken(type='symbol',value='=')]))
        #let_statement.append(SyntaxToken(type='tag_start',value='evaluateExpression'))
        let_statement += self.compile_expression()
        #let_statement.append(SyntaxToken(type='tag_end',value='evaluateExpression'))
        let_statement.append(self.compare_token(self.advance(),[SyntaxToken(type='symbol',value=';')]))

        #print(let_statement)
        return let_statement

    '''
        rule: 
    '''
    def compile_if(self):
        #print('entered if statement')
        if_statement = [
            self.compare_token(self.advance(),[SyntaxToken(type='keyword',value='if')]),
            self.compare_token(self.advance(),[SyntaxToken(type='symbol',value='(')]),
        ]

        if_statement += self.compile_expression()
        if_statement += [
            self.compare_token(self.advance(),[SyntaxToken(type='symbol',value=')')]),
            self.compare_token(self.advance(),[SyntaxToken(type='symbol',value='{')]),
        ]
        if_statement.append(SyntaxToken(type='tag_start',value='statements_if'))

        if_statement += self.compile_statements()
        if_statement.append(SyntaxToken(type='tag_end',value='statements_if'))
        if_statement.append(self.compare_token(self.advance(),[SyntaxToken(type='symbol',value='}')]))

        current_token = self.advance()
        # checks if expression evaluation is needed
        if current_token.value == 'else':
            if_statement += [
                current_token,
                self.compare_token(self.advance(),[SyntaxToken(type='symbol',value='{')])
            ]
            if_statement.append(SyntaxToken(type='tag_start',value='statements_else'))
            if_statement += self.compile_statements()
            if_statement.append(SyntaxToken(type='tag_end',value='statements_else'))
            if_statement.append(self.compare_token(self.advance(),[SyntaxToken(type='symbol',value='}')]))
        else:
            self.current_token_index -= 1            

        return if_statement

    '''
        rule: 
    '''
    def compile_while(self):
        #print('entered while statement')
        while_statement = []

        while_statement = [
            self.compare_token(self.advance(),[SyntaxToken(type='keyword',value='while')]),
            self.compare_token(self.advance(),[SyntaxToken(type='symbol',value='(')]),
        ]

        while_statement += self.compile_expression()
        while_statement += [
            self.compare_token(self.advance(),[SyntaxToken(type='symbol',value=')')]),
            self.compare_token(self.advance(),[SyntaxToken(type='symbol',value='{')]),
        ]

        while_statement.append(SyntaxToken(type='tag_start',value='statements'))
        while_statement += self.compile_statements()
        while_statement.append(SyntaxToken(type='tag_end',value='statements'))
        while_statement.append(self.compare_token(self.advance(),[SyntaxToken(type='symbol',value='}')]))

        return while_statement

    '''
        rule: 
    '''
    def compile_do(self):
        #print('entered do statement')
        return [
            self.compare_token(self.advance(),[SyntaxToken(type='keyword',value='do')]),
            self.compile_subroutine_call(),
            self.compare_token(self.advance(),[SyntaxToken(type='symbol',value=';')])
        ]

    '''
        rule: 
    '''
    def compile_return(self):
        #print('entered return statement')
        return_statement = []

        return_statement.append(self.compare_token(self.advance(),[SyntaxToken(type='keyword',value='return')]))
        
        current_token = self.advance()
        # no expression is passed
        if current_token.value == ';':
            return_statement.append(current_token)
        else:
            self.current_token_index -= 1
            return_statement += self.compile_expression()
            return_statement.append(self.compare_token(self.advance(),[SyntaxToken(type='symbol',value=';')]))

        return return_statement

    '''
        rule: term (op term)*
    '''
    def compile_expression(self):
        #print('entered expression compilation')
        expression = [
            SyntaxToken(type='tag_start',value='expression')
        ]
        # compile term
        #expression.append(SyntaxToken(type='tag_start',value='term'))
        expression += self.compile_term()
        #expression.append(SyntaxToken(type='tag_end',value='term'))
        #print(expression)

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
            #expression.append(SyntaxToken(type='tag_start',value='operation'))
            #expression.append(current_token)
            expression.append(SyntaxToken(type='operation',value=current_token.value))  # test for tagging as operation
            #expression.append(SyntaxToken(type='tag_end',value='operation'))
            #expression.append(SyntaxToken(type='tag_start',value='term'))
            expression.append(self.compile_term())
            #expression.append(SyntaxToken(type='tag_end',value='term'))
        else:
            self.current_token_index -= 1

        expression += [
            SyntaxToken(type='tag_end',value='expression')
        ]
        #print(f'exited expression {expression}')
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
        term += [
            self.compare_token(
                self.advance(),
                [                     
                    SyntaxToken(type='integerConstant'),
                    SyntaxToken(type='stringConstant'),
                    SyntaxToken(value='true'),
                    SyntaxToken(value='false'),
                    SyntaxToken(value='null'),
                    SyntaxToken(value='this'),
                    SyntaxToken(type='identifier'),
                    SyntaxToken(value='('),
                    SyntaxToken(value='-'),
                    SyntaxToken(value='~'),
                    SyntaxToken(type='keyword',value='this'),
                    SyntaxToken(type='keyword',value='that')
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
                    term.append(self.compare_token(current_token,[SyntaxToken(type='symbol',value='[')]))
                    term += self.compile_expression()
                    term.append(self.compare_token(self.advance(),[SyntaxToken(type='symbol',value=']')]))
                # compile subroutinecall
                else:
                #if current_token.value in ['(', '.']:
                    # gets subroutineName | (className | subroutineName) rule
                    self.current_token_index -= 2
                    del term[-1]
                    term += self.compile_subroutine_call()
            else:
                # sets back index, since its only varName and doesn't need to be expanded
                self.current_token_index -= 1
        # checks for unaryOp term rule, by checking first list value is unaryOp ("-" | "~")
        if term[0].value in ['-','~']:
            #term.append(term[0])
            #term.append(SyntaxToken(type='operation',value=term[0].value))
            #term[0] = SyntaxToken(type='tag_start',value='operation')
            term[0] = SyntaxToken(type='operation',value=term[0].value)
            #term.append(SyntaxToken(type='tag_end',value='operation'))            
            term += self.compile_term()
            print(term)
        # checks for '(' expression ')'
        if self.current_token.value in ['(']:
            term += self.compile_expression()
            term.append(self.compare_token(self.advance(),[SyntaxToken(type='symbol',value=')')]))

        return term

    '''
        rule: subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')' 
    '''
    def compile_subroutine_call(self):
        #print('entered compile_subroutine_call')
        subroutine_call = [
            SyntaxToken(type='tag_start',value='subroutineCall'),
            self.compare_token(self.advance(),[SyntaxToken(type='identifier')])
        ]

        # eats next token, to determine if its first or second option of or statement
        current_token = self.advance()

        # first rule
        if current_token.value == '(':
            # appends current token only
            subroutine_call.append(SyntaxToken(type='tag_end',value='subroutineCall'))
            subroutine_call.append(current_token)
        # second rule
        if current_token.value == '.':
            # appends current token and next identifier
            subroutine_call += [
                current_token,
                self.compare_token(self.advance(),[SyntaxToken(type='identifier')]),
                SyntaxToken(type='tag_end',value='subroutineCall'),
                self.compare_token(self.advance(),[SyntaxToken(value='(')]),
            ]


        #subroutine_call.append(SyntaxToken(type='tag_start',value='expressionList'))
        subroutine_call += self.compile_expression_list()
        #subroutine_call.append(SyntaxToken(type='tag_end',value='expressionList'))
        subroutine_call.append(self.compare_token(self.advance(),[SyntaxToken(type='symbol',value=')')]))
        return subroutine_call

    '''
        rule: (expression (',' expression)*)?
    '''
    # null expression
    def compile_expression_list(self):
        #print('entered compile_expression_list')
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
                    SyntaxToken(value='int'),
                    SyntaxToken(value='char'),
                    SyntaxToken(value='boolean'),
                    SyntaxToken(value='void'),
                    SyntaxToken(type='identifier'),
                ]
            )
    
    def flatten_list(self,items):
        for x in items:
            if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
                for sub_x in self.flatten_list(x):
                    yield sub_x
            else:
                yield x

    def execute_compilation(self):
        class_statments = self.compile_class()
        #print(class_statments)
        flattened_statements = [self.return_xml_tag(syntax_token) for syntax_token in flatten_list(class_statments)]
        with open(f"{os.path.join(os.getcwd(),self.file_folder)}/{self.file_name}Syntax.xml",'w') as fp:
            fp.write('\n'.join(flattened_statements)+'\n')        

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
    
    if os.path.isfile(f'{os.path.join(os.getcwd(),args.file_path)}'):
        CompilationEngine(args.file_path)        
    else:
        for file in os.listdir(args.file_path):            
            if file.endswith(".jack"):
                CompilationEngine(os.path.join(args.file_path,file))

if __name__ == "__main__":
    main()