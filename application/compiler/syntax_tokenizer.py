from dataclasses import dataclass
import re

@dataclass
class SyntaxToken():
    type:   str
    value:  str
    start:  int
    end:    int

@dataclass
class MismatchedValueError(Exception):   
    data: str

@dataclass
class SyntaxTokenizer():
    code: str

    def tokenize(self):
        keywords    = {'int', 'var', 'class', 'let','return','class','void','function','while','do','static','boolean','if','false','true','null','else','field','constructor','this','method','char'}
        symbols     = {'\+','\-','\*',';','<','>','=','\|','\&','\,','\.',',','\[','\]','\/','\(', '\)', '{', '}',"'",'~'}
        token_specification = [
            ('comments',        r'//.*|/\*(.|[\r\n])*?\*/'),   # Gets comments till the end of line
            ('keyword',         r'|'.join(keywords)),            
            ('symbol',          r'|'.join(symbols)),            # Assignment operator
            ('identifier',      r'[a-zA-Z_]+[a-zA-Z0-9_]*'),    # Identifier
            ('integerConstant', r'\d+'),                        # Integer number
            ('stringConstant',  r'"(.*)"'),                     # Integer number
            ('skip',            r'[ \t\n]+'),                   # Skip over spaces and tabs
            ('mismatch',        r'.'),                          # Any other character
        ]
        tok_regex = '|'.join(f'(?P<{group_name}>{match})' for group_name,match in token_specification)
        for regex_match in re.finditer(tok_regex, self.code):
            result = [(k,v) for k,v in regex_match.groupdict().items() if v is not None][0]  
            #print(result,regex_match.start(0),regex_match.end(0),regex_match.pos,regex_match.span(0))
            yield SyntaxToken(result[0],result[1].replace('"', ''),regex_match.start(0),regex_match.end(0))


def main():
    statements = '''class _123_Point_99 {
        var     a;
        while
    }
    '''

    lex_tokenizer = SyntaxTokenizer(statements)

    tokens = []

    for token in lex_tokenizer.tokenize():
        if token.type == 'MISMATCH':
            raise MismatchedValueError('Erro de token, verificar o código')
        if token.type != 'SKIP':
            tokens.append(token)
        #print(token)

    print(tokens)

if __name__ == '__main__':
    main()