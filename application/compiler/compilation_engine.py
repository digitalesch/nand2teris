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

@dataclass
class CompilationEngine():
    xml_tree: ET
    current_token_index : int = 0

    def __post_init__(self):
        self.tokens = self.create_tokens()

    def create_tokens(self):
        return [LexicToken(tag.tag, tag.text.strip()) for tag in self.xml_tree.iter() if tag.tag != 'tokens']

    def eat_token(self) -> None:
        token = None
        if self.current_token_index < len(self.tokens):
            token = self.tokens[self.current_token_index]
            self.current_token_index += 1
        print(f'current token: {token}')
        return token
    
    def return_xml_tag(self, lex_token):
        translate = {
            "<": '&lt;',
            ">": '&gt;', 
            "'": '&quot;',
            "&": '&amp;'
        }
        return f'<{lex_token.type}> {translate[lex_token.value] if lex_token.value in translate else lex_token.value} </{lex_token.type}>'

    def compare_token(self, input: LexicToken, expectation: LexicToken):
        print(input, expectation)
        print([(input.type if token.type else None)==token.type and (input.value if token.value else None)==token.value for token in expectation])
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
        if any([(input.type if token.type else None)==token.type and (input.value if token.value else None)==token.value for token in expectation]):
            return input
        else:
            # raises excpetion by not having the expected token in code
            raise Exception(f'Expected the following {expectation}, but got {input}')

    # a ideia é diferente aqui, só precisa compilar os termos que vai achando, não comparar com a gramática em si
    def compile_class_statement(self):
        print('entered compile_class_statement compilation')
        return [
            '<class>',
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='keyword',value='class')])),
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='identifier')])),
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='{')])),
            '<classVarDec>',
            self.compile_var_class_dec(),
            '</classVarDec>',
            self.compile_subroutine_dec(),
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='}')])),
            '</class>',
        ]

    def compile_var_class_dec(self):
        print('entered compile_var_class_dec compilation')
        var_class_dec = []
        
        current_token = self.eat_token()
        if current_token.value in ['static','field']:
            var_class_dec += [
                self.return_xml_tag(current_token),
                self.return_xml_tag(
                    self.compare_token(
                        self.eat_token(),
                        [
                            LexicToken(value='int'),                                    
                            LexicToken(value='char'),
                            LexicToken(value='boolean')
                        ]
                    ),
                ),                
            ]

            var_class_dec += self.compile_var_dec_list()
            var_class_dec.append(self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value=';')])))
        else:
            self.current_token_index -= 1
            return var_class_dec

        current_token = self.eat_token()
        # recursevely construct expressions
        if current_token.value in ['static','field']:
            self.current_token_index -= 1
            var_class_dec += self.compile_var_class_dec(),
        else:            
            print('var class dec ended')
            self.current_token_index -= 1

        return var_class_dec

    def compile_subroutine_dec(self):
        print('entered compile_subroutine_dec compilation')
        subroutine_dec = []
        while 1:
            current_token = self.eat_token()
            if current_token:
                if current_token.value in ['constructor','function','method']:
                    subroutine_dec += [
                        '<subroutineDec>',
                        self.return_xml_tag(current_token),
                        # compiles options for ('void' | type)
                        self.return_xml_tag(
                            self.compare_token(
                                self.eat_token(),
                                [
                                    LexicToken(value='void'),
                                    LexicToken(value='int'),                                    
                                    LexicToken(value='char'),
                                    LexicToken(value='boolean'),
                                    LexicToken(type='identifier')
                                ]
                            ),
                        ),
                        self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='identifier')])),
                        self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='(')])),
                        '<parameterList>',
                        # gets tokens directly instead of xml tags, so list comprehension is needed
                        [self.return_xml_tag(token) for token in self.compile_parameter_list()], 
                        '</parameterList>',
                        self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value=')')])),
                        self.compile_subroutine_body(),
                        '</subroutineDec>',
                    ]
                if current_token.value in ['}']:
                    print('compile_subroutine_dec ended')
                    self.current_token_index -= 1
                    break
            else:
                break
        
        return subroutine_dec

    def compile_subroutine_body(self):
        print('entered compile_subroutine_body compilation')
        subroutine_body = []

        subroutine_body += [
            '<subroutineBody>',
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='{')])),
            '<varDec>',
            self.compile_var_dec(),
            '</varDec>',
            self.compile_statements(),
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='}')])),
            '</subroutineBody>',
        ]

        return subroutine_body

    '''
        def: 'var' type varName (',' varName)* ';'
    '''
    def compile_var_dec(self):
        print('entered compile_var_dec compilation')
        var_dec = []
        
        current_token = self.eat_token()

        if current_token.value in ['let','if','while','do','return']:
            #var_dec += ['</varDec>']
            self.current_token_index -= 1
            return var_dec

        var_dec = [
            self.return_xml_tag(self.compare_token(current_token,[LexicToken(type='keyword',value='var')])),
            self.return_xml_tag(
                self.compare_token(
                    self.eat_token(),
                    [
                        LexicToken(value='int'),
                        LexicToken(value='char'),
                        LexicToken(value='boolean'),
                        LexicToken(type='identifier')
                    ]
                ),
            ),
        ]

        var_dec += self.compile_var_dec_list()
        var_dec.append(self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value=';')])))

        current_token = self.eat_token()
        # recursevely construct expressions
        if current_token.value == 'var':
            self.current_token_index -= 1
            var_dec += self.compile_var_dec(),
        else:
            self.current_token_index -= 1
        
        print(var_dec)

        return var_dec

    def compile_var_dec_list(self):
        print('entered compile_var_dec_list compilation')
        var_dec_list = []

        var_dec_list += [
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='identifier')])),
        ]

        print(var_dec_list)

        current_token = self.eat_token()
        if current_token.value == ',':
            var_dec_list.append(self.return_xml_tag(current_token))
            var_dec_list += self.compile_var_dec_list()
        if current_token.value == ';':
            self.current_token_index -= 1
            return var_dec_list     

        return var_dec_list   

    def compile_statements(self):
        print('entered compile_statements compilation')
        statements = ['<statements>']
        while 1:
            current_token = self.eat_token()
            if current_token:
                print(f'Statement token is {current_token}')
                if current_token.value == 'let':
                    statements += [
                        '<letStatment>',
                        self.return_xml_tag(current_token),
                        self.compile_let_statement(),
                        '</letStatment>',
                    ]
                if current_token.value == 'if':
                    statements += [
                        '<ifStatement>',
                        self.return_xml_tag(current_token),
                        self.compile_if_statement(),
                        '</ifStatement>',
                    ]
                if current_token.value == 'while':
                    statements += [
                        '<whileStatment>',
                        self.return_xml_tag(current_token),
                        self.compile_while_statement(),
                        '</whileStatment>',
                    ]
                if current_token.value == 'do':
                    statements += [
                        '<doStatment>',
                        self.return_xml_tag(current_token),
                        self.compile_do_statement(),
                        '</doStatment>',
                    ]
                if current_token.value == 'return':
                    statements += [
                        '<returnStatment>',
                        self.return_xml_tag(current_token),
                        self.compile_return_statement(),
                        '</returnStatment>',
                    ]
                if current_token.value in ['}',')']:
                    statements +=[
                        '</statements>'
                    ]
                    self.current_token_index -= 1
                    break
            else:
                break
        
        return statements

    def compile_while_statement(self):
        print('entered while compilation')
        return [
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='(')])),            
            self.compile_expression(),
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value=')')])),
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='{')])),
            self.compile_statements(),
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='}')])),
        ]

    def compile_let_statement(self):
        print('entered let compilation')
        return [
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='identifier')])),
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='=')])),
            self.compile_expression(),
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value=';')])),
        ]

    '''
        def: if (expression) { statements } (else { statements })?
    
    '''
    def compile_if_statement(self):
        print('entered if compilation')
        return [            
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='(')])),
            self.compile_expression(),
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value=')')])),
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='{')])),
            self.compile_expression(),
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='}')])),
        ]

    '''
        def: 
    '''
    def compile_return_statement(self):
        print('entered return compilation')

        return [
            self.compile_expression(),
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value=';')])),
        ]

    '''
        def: do subroutineCall
    '''
    def compile_do_statement(self):
        print('entered do compilation')
        do_statement = []

        do_statement += [            
            self.compile_subroutine_call(),            
        ]

        return do_statement

    '''
        def: term (op term)*
        ex: count < 100
    '''
    def compile_expression(self):
        print('entered expression compilation')
        expression = ['<expression>']
        # compile term
        expression.append(self.compile_term())

        # loop to check how many iterations of (op term)* are present        
        while 1:
            current_token = self.eat_token()
            # checks if the (op term)* rules applies
            if current_token.value not in [')', '}', ';']:
                if any(
                    [
                        current_token.value=='+',
                        current_token.value=='-',
                        current_token.value=='*',
                        current_token.value=='/',
                        current_token.value=='&',
                        current_token.value=='|',
                        current_token.value=='<',
                        current_token.value=='>',
                        current_token.value=='=',
                    ]
                ):
                    expression.append(self.return_xml_tag(current_token))
                    expression.append(self.compile_term())
            # returns to previous token, so it can be evaluated
            else:
                expression += ['</expression>']
                self.current_token_index -= 1
                print(f"Expression is: {expression}")
                return expression
            expression += ['</expression>']
            return expression

    '''
        def: term (op term)*
        ex: count < 100
    '''
    def compile_expression(self):
        print('entered expression compilation')
        expression = ['<expression>']
        # compile term
        expression += self.compile_term()

        # compiles possible (op term)
        current_token = self.eat_token()
        print(f'ct: {current_token}')
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
            expression.append(self.return_xml_tag(current_token))
            expression.append(self.compile_term())
        else:
            self.current_token_index -= 1

        expression += ['</expression>']
        print(f'exited expression {expression}')
        return expression

    '''
        def: integerConstant | stringConstant | keywordConstant | varName
        # falta fazer esses
         | varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
    '''
    def compile_term(self):        
        print('entered term compilation')
        term = []

        current_token = self.eat_token()

        if (
            current_token.type in [
                'integerConstant',
                'stringConstant',
                'identifier'
            ]
            or current_token.value in [
                'true',
                'false',
                'null',
                'this'
            ]
        ):
            term.append(self.return_xml_tag(current_token))
            if current_token.type == 'identifier':
                # check for rule varName '[' expression ']'
                current_token = self.eat_token()
                if current_token.value == '[':
                    term += self.compile_expression()
                    term.append(self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value=']')])))
                if current_token.value == '.':
                    self.current_token_index -= 2
                    term += self.compile_subroutine_call()
                if current_token.value not in ['.','[']:
                    self.current_token_index -= 1
        if (
            current_token.value in [
                '~',
                '-',                
            ]
        ):
            term.append(self.return_xml_tag(current_token))
            term += self.compile_term()

        if (
            current_token.value in [
                '(',                
            ]
        ):
            term += self.compile_expression()
            term.append(self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value=')')])))

        if (current_token.value == ')'):
            self.current_token_index -= 1
        print(f'term is {term}')
        return term

    '''
        def: (type identifier (',' type identifier)*)*
    '''
    def compile_parameter_list(self):
        print('entered compile_parameter_list compilation')
        parameter_list = []
        
        current_token = self.eat_token()        

        # exits function when a right parenthesis is found
        if current_token.value == ')':
            print(f'param {parameter_list}')
            self.current_token_index -= 1
            return parameter_list
        else:        
            # builds first parameter, when passed
            parameter_list.append(
                    self.compare_token(                                
                        current_token,
                        [                     
                            LexicToken(value='int'),                                    
                            LexicToken(value='char'),
                            LexicToken(value='boolean'),
                            LexicToken(type='identifier')
                        ]
                    )                
            )
            parameter_list.append(
                self.compare_token(self.eat_token(),[LexicToken(type='identifier')])
            )
            # eats another token to see if second part of rule (',' type identifier)* exists
            current_token = self.eat_token()

            if current_token.value == ',':
                print(current_token)
                parameter_list.append(current_token)
                parameter_list += self.compile_parameter_list()
                if parameter_list[-1].value == ',':
                    raise Exception(f"Error in parameter list, since last item is {parameter_list[-1]}")
            else:
                self.current_token_index -= 1

            return parameter_list      
        
    '''
        def: subRoutineName '(' expressionList ')' | (className|varName) '.' subRoutineName '(' expressionList ')'
    '''
    def compile_subroutine_call(self):
        print('entered compile_subroutine_call compilation')
        subroutine_call = [
            '<subroutineCall>',
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='identifier')])),    
        ]

        # eats next token, to determine if its first or second option of or statement
        current_token = self.eat_token()

        # first rule
        if current_token.value == '(':
            # appends current token only
            subroutine_call.append(self.return_xml_tag(current_token))
        # second rule
        if current_token.value == '.':
            print('second')
            # appends current token and next identifier
            subroutine_call += [
                self.return_xml_tag(current_token),
                self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='identifier')])),
                self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(value='(')])),
            ]

        subroutine_call += [
            '<expressionList>',
            self.compile_expression_list(),
            '</expressionList>',
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value=')')])),
            #self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value=';')])),
            '</subroutineCall>'
        ]

        return subroutine_call

    '''
        def: (expression (, expression)*)?
    '''
    def compile_expression_list(self):
        print('entered compile_expression_list compilation')
        expression_list = []

        expression_list += [
            self.compile_expression()
        ]
        current_token = self.eat_token()

        if current_token.value == ',':
            expression_list.append(self.return_xml_tag(current_token))
            expression_list += self.compile_expression_list()
        else:
            self.current_token_index -= 1

        return expression_list

    def flatten_statements(self,items):
        """Yield items from any nested iterable; see Reference."""
        for x in items:
            if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
                for sub_x in self.flatten_statements(x):
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


def main2():    

    # let length = Keyboard.readInt("HOW MANY NUMBERS? ");
    ce = CompilationEngine(
        ET.fromstring(
            '''
                <tokens>
                    <keyword> let </keyword>
                    <identifier> length </identifier>
                    <symbol> = </symbol>
                    <identifier> Keyboard </identifier>
                    <symbol> . </symbol>
                    <identifier> readInt </identifier>
                    <symbol> ( </symbol>
                    
                    <symbol> ) </symbol>
                    <symbol> ; </symbol>
                </tokens>
            '''
        )
    )

    syntax_tokens = []

    syntax_tokens += ce.return_xml_tag(ce.compare_token(ce.eat_token(),[LexicToken(type='keyword',value='let')])),
    syntax_tokens += ce.return_xml_tag(ce.compare_token(ce.eat_token(),[LexicToken(type='identifier')])),
    syntax_tokens += ce.return_xml_tag(ce.compare_token(ce.eat_token(),[LexicToken(type='symbol',value='=')])),
    syntax_tokens += ce.compile_term()
    syntax_tokens += ce.return_xml_tag(ce.compare_token(ce.eat_token(),[LexicToken(type='symbol',value=';')])),

    print(syntax_tokens)

if __name__ == "__main__":
    main()