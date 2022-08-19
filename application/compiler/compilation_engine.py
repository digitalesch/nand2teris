# created code
from operator import concat
from posixpath import split
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
                second parameter will be compared
            example2:
                current token: LexicToken(type='symbol', value='{')
                compared to: [LexicToken(type='symbol', value='{')]
                both parameters will be compared
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
            self.compile_var_class_dec(),
            self.compile_subroutine_dec(),
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='}')])),
            '</class>',
        ]
    
    def compile_var_class_dec(self):
        print('entered compile_var_class_dec compilation')
        var_class_dec = []
        while 1:
            current_token = self.eat_token()
            if current_token:
                if current_token.value in ['static','field']:
                    var_class_dec += [
                        '<classVarDec>',
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
                        self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='identifier')])),
                        self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value=';')])),
                        '</classVarDec>',
                    ]
                if current_token.value in ['constuctor','function','method','}', ';']:
                    print('var class dec ended')
                    self.current_token_index -= 1
                    break
            else:
                break
        
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
                                    LexicToken(value='boolean')
                                ]
                            ),
                        ),
                        self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='identifier')])),
                        self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='(')])),
                        self.compile_parameter_list(),
                        self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value=')')])),
                        #self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='{')])),
                        self.compile_subroutine_body(),
                        #self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='}')])),
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
            self.compile_var_dec(),
            self.compile_statements(),
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value='}')])),
            '</subroutineBody>',
        ]

        return subroutine_body

    def compile_var_dec(self):
        print('entered compile_var_dec compilation')
        var_dec = []

        while 1:
            current_token = self.eat_token()
            if current_token:
                if current_token.value in ['var']:
                    pass
                if current_token.value in [';','let','if','while','do','return']:
                    print('compile_var_dec ended')
                    self.current_token_index -= 1
                    break
            else:
                break
        
        return var_dec

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
            print(f"Expression is: {expression}")
            expression += ['</expression>']
            return expression

    
    '''
        def: integerConstant | stringConstant | keywordConstant | varName ...
    '''
    def compile_term(self):        
        print('entered term compilation')
        term = []
        current_token = self.eat_token()
        if any(
            [
                current_token.type=='integerConstant',
                current_token.type=='stringConstant',
                current_token.type=='identifier',
                current_token.value=='true',
                current_token.value=='false',
                current_token.value=='null',
                current_token.value=='this',
            ]
        ):
            term += [
                '<term>',
                self.return_xml_tag(current_token),
                '</term>'
            ]
        else:
            self.current_token_index -= 1
        
        return term

    def compile_parameter_list(self):
        print('entered compile_parameter_list compilation')
        parameter_list = ['<parameterList>']

        concated_params = []
        
        # loop to check how many iterations of (op term)* are present        
        while 1:
            print(f'XXX {concated_params}')
            current_token = self.eat_token()            
            # checks if the (op term)* rules applies
            if current_token.value not in [')']:
                concated_params.append(current_token)
                # condition so first value of parameters isn't a comma
                # will break if the first parameter is a comma, by accessing weird list positions that don't yet exist
                try:
                    if current_token.value == ',' and concated_params[-2].type=='identifier':
                        #concated_params.append(current_token)
                        parameter_list += [
                            self.return_xml_tag(self.compare_token(current_token,[LexicToken(type='symbol',value=',')])),
                        ]                
                    else:
                        concated_params.append(self.eat_token())
                        parameter_list += [
                            self.return_xml_tag(
                                self.compare_token(                                
                                    concated_params[-2],
                                    [                     
                                        LexicToken(value='int'),                                    
                                        LexicToken(value='char'),
                                        LexicToken(value='boolean')
                                    ]
                                ),
                            ),
                            self.return_xml_tag(self.compare_token(concated_params[-1],[LexicToken(type='identifier')])),
                        ]
                except IndexError:
                    raise Exception(f'Error in parameter list, got unexpected {current_token}')
            # returns to previous token, so it can be evaluated
            else:
                parameter_list += ['</parameterList>']
                self.current_token_index -= 1
                break

        # rule to check on impossible parameters list, like "int x," or "," or ", int"
        if len(concated_params)%3==0 and len(concated_params)>0:
            raise Exception(f"Error in parameter list, got {concated_params}")

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
            self.return_xml_tag(self.compare_token(self.eat_token(),[LexicToken(type='symbol',value=';')])),
            '</subroutineCall>'
        ]

        return subroutine_call

    '''
        def: (expression (, expression)*)?
    '''
    def compile_expression_list(self):
        expression_list = []

        expression_list += [
            self.compile_expression()
        ]

        current_token = self.eat_token()
        # recursevely construct expressions
        if current_token.value == ',':
            expression_list += self.compile_expression_list()
        else:
            self.current_token_index -= 1
        
        print(expression_list)

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

if __name__ == "__main__":
    main()