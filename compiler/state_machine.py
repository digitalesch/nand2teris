from dataclasses import dataclass
from lexical_tokenizer import LexicalTokenizer, LexicToken
from enum import Enum

class Position(Enum):
    CURRENT = 0
    NEXT = 1

@dataclass
class SyntaxToken(LexicToken):
    position: Position = 0
    terminal: bool = True
    optional: bool = False
    multiple: bool = False

@dataclass
class StateMachine:
    code: str
    keywords: set
    symbols: set
    token_specification: list
    
    def __post_init__(self):
        self.lexical_tokenizer = LexicalTokenizer(
            code=self.code,
            keywords=self.keywords,
            symbols=self.symbols,
            token_specification=self.token_specification
        )

        self.token_generator = self.lexical_tokenizer.tokenize()

        """
            sets both current_token and next_token to null, 
            since some comparsions must be made with LL(1) token
        """
        self.current_token, self.next_token = None, None

        self.rules = {
            'START': [
                SyntaxToken(type='nonTerminal',value='CLASS', position=Position.NEXT, terminal=False)
            ],
            'CLASS': [
                SyntaxToken(type='keyword',value='class', position=Position.NEXT),
                SyntaxToken(type='identifier', position=Position.NEXT),
                SyntaxToken(type='nonTerminal',value='CLASS_DECLARATION', position=Position.NEXT, terminal=False),
            ],
            'CLASS_DECLARATION': [
                SyntaxToken(type='symbol',value='{', position=Position.NEXT),
                SyntaxToken(type='nonTerminal',value='VAR_DEC', position=Position.NEXT, terminal=False),
                SyntaxToken(type='symbol',value='}', position=Position.NEXT),
            ],
            'VAR_DEC': [
                SyntaxToken(type='keyword',value='var', position=Position.NEXT, optional=True),
                SyntaxToken(type='nonTerminal',value='VAR_TYPE', position=Position.NEXT, terminal=False, optional=True),
                SyntaxToken(type='identifier', position=Position.NEXT, optional=True),
                SyntaxToken(type='nonTerminal',value='MULTIPLE_VARDEC', position=Position.NEXT, terminal=False, optional=True),
                SyntaxToken(type='symbol',value=';', position=Position.NEXT, optional=True),
            ],
            'MULTIPLE_VARDEC': [
                SyntaxToken(type='symbol',value=',', position=Position.NEXT, optional=True),
                SyntaxToken(type='identifier', position=Position.NEXT, optional=True),
            ],
            'VAR_TYPE': [
                SyntaxToken(type='keyword',value=['char','int','boolean'], position=Position.NEXT),
            ],
            'VAR_TESTE': [
                SyntaxToken(type='nonTerminal',value='MVT', position=Position.NEXT, terminal=False, multiple=True),
            ],
            'MVT': [
                SyntaxToken(type='keyword',value='var', position=Position.NEXT),
                SyntaxToken(type='nonTerminal',value='VAR_TYPE', position=Position.NEXT, terminal=False),
                SyntaxToken(type='identifier', position=Position.NEXT, optional=True),
                SyntaxToken(type='nonTerminal',value='MULTIPLE_VARDEC', position=Position.NEXT, terminal=False, multiple=True),
                SyntaxToken(type='symbol',value=';', position=Position.NEXT)
            ],
            'X': [
                SyntaxToken(type='keyword',value='var', position=Position.NEXT),
                SyntaxToken(type='identifier', position=Position.NEXT),
                SyntaxToken(type='nonTerminal',value='Y', position=Position.NEXT, optional=True, terminal=False, multiple=True),
                SyntaxToken(type='symbol',value=';', position=Position.NEXT)
            ],
            'Y': [
                SyntaxToken(type='symbol',value=',', position=Position.NEXT),
                SyntaxToken(type='identifier', position=Position.NEXT),
            ],
        }

    def has_tokens(self):
        try:
            token = next(self.token_generator)
            while token.type in ('skip','comments'):
                token = next(self.token_generator)
            return token
        except StopIteration:
            return None

    def eat_token(self):
        self.current_token = self.next_token
        self.next_token = self.has_tokens()
        return (self.current_token, self.next_token)
    
    def get_positional_token(
        self, 
        position: Position
    ):
        return self.current_token if position == Position.CURRENT else self.next_token
    
    def compare_token_and_rule(
        self, 
        syntax_rule: SyntaxToken,
        current_token: LexicToken,
    ) -> bool:
        print(f'Comparing ("{current_token.type}" - "{current_token.value}") with ("{syntax_rule.type}" - "{syntax_rule.value}")')
        return all(
            [
                current_token.type == syntax_rule.type,
                # uses coalesce when identifier is met
                current_token.value in syntax_rule.value if syntax_rule.value else [current_token.value]
            ]
        )

    '''
        START -> class <identifier> { varDec* subRoutineDec* }
    '''
    def traverse_syntax_tree(
        self,
        rule_name: SyntaxToken,
        multiple: bool = False,
        optional: bool = False
    ):
        for syntax_rule in self.rules[rule_name]:
            if syntax_rule.terminal:
                # inherits previous nonTerminal rule multiple flag
                syntax_rule.multiple = multiple
                syntax_rule.optional = optional
                yield(syntax_rule)
            if not syntax_rule.terminal:
                yield from (self.traverse_syntax_tree(syntax_rule.value,syntax_rule.multiple,syntax_rule.optional))
    
    def traverse_syntax_tree_(
        self,
        rule_name: SyntaxToken,
        multiple: bool = False,
        optional: bool = False
    ):
        multiple = yield
        yield(not multiple)
    
    def compile_language(self, start_rule):
        syntax_tree = self.traverse_syntax_tree(start_rule)
        current_rule = next(syntax_tree)
        syntax_tree.send(False)
        while current_token := self.has_tokens():
            
            comparison_output = self.compare_token_and_rule(
                syntax_rule=current_rule,
                current_token=current_token
            )

            print(comparison_output)
            # checks if the comparison is equal and multiple flag is inherited from previous rule
            if (not comparison_output and current_rule.multiple) or (comparison_output):
                print('a')
                current_rule = next(syntax_tree)

            # if not comparison_output and current_rule.optional:
            #     print('a')
            #     while True:
            #         current_rule = next(syntax_tree)
            #         if not current_rule.optional:
            #             print(current_rule)
            #             break
                    
            #     comparison_output = self.compare_token_and_rule(
            #         syntax_rule=current_rule,
            #         current_token=current_token
            #     )
        
'''
    varType* ;
'''

def main():
    # statements = """
    #     class Point {
    #         //var int point_value, point_type;
    #         var int point_value;
    #     }
    # """
    # statements = """int"""
    # statements = """teste"""
    # statements = """{}"""
    statements = """var t1, t2;"""
    
    state_machine = StateMachine(
        code=statements,
        keywords={"int", "var", "let", "return", "class", "void", "function", "while", "do", "static", "boolean", "if", "false", "true", "null", "else", "field", "constructor", "this", "method", "char", "that",},
        symbols={"\+", "\-", "\*", ";", "<", ">", "=", "\|", "\&", "\,", "\.", ",", "\[", "\]", "\/", "\(", "\)", "{", "}", "'", "~",},
        token_specification=[
            ("mismatched_identifier",r"[0-9]+[a-zA-Z_]+[0-9]*"),            # Mismatched identifier, starting with a number
            ("integerConstant", r"\d+"),                                    # Integer number
            ("identifier", r"[a-zA-Z_0-9]+"),                               # Identifier
            ("stringConstant", r'"(.*)"'),                                  # String constant
            ("mismatch", r"."),                                             # Any other character
        ],
    )

    # state_machine.compile_language('START')
    # state_machine.compile_language('X')
    x = state_machine.traverse_syntax_tree_('X')
    next(x)
    print(x.send(True))

if __name__ == "__main__":
    main()
