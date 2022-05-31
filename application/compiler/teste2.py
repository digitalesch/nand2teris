rules = {
    'class':            ['class','!className','{','!classVarDec*','!subRoutineDec*','}'],
    '!classVarDec':     [('static','field'),'!type','!varName','(',',','!varName',')'],
    '!type':            [('int','char','boolean','!className')],
    '!subRoutineDec':   [('constructor','function','method'),('void','!type'),'!subRoutineName','(','!parameterList',')','!subRoutineBody'],
    '!parameterList':   [(('!type','!varName'),'?')],
    '!subRoutineBody':  ['{','!varDec*','!statements','}'],
    '!varDec':          ['var', '!type', '!varName', ';'],
    '!className':       ['%identifier'],
    '!subRoutineName':  ['%identifier'],
    '!varName':         ['%identifier'],

    '!statements':      ['!statement*'],
    '!statement':       [('!letStatement','!ifStatement','!whileStatement','!doStatement','!returnStatement')],
    '!letStatement':    ['let','!varName',],
    '!ifStatement':     ['if','(','!expression',')','{','!statements','}'],
    '!whileStatement':  ['while','(','!expression',')','{','!statements','}'],
    '!doStatement':     ['do','!subRoutineCall',';'],
    '!returnStatement': ['return', '!expression'],
    '!expression':      ['!term'], ###inc
    '!term':            [('!integerConstant','!stringConstant','!keywordConstant','!varName','!subRoutineCall',')','!unaryOp','!term')],
    '!integerConstant': ['%integerConstant'],
    '!stringConstant':  ['%stringConstant'],
    '!keywordConstant': ['%keyword'],
    '!subRoutineCall':  [('!subRoutineName','(','!expressionList',')',('!className','!varName'),'.','!subRoutineName','(','!experssionList',')')],
    '!expressionList':  ['?','!expression']
}

from dataclasses import dataclass
import re

@dataclass 
class SyntaxTree():
    x: str

def main():    
    x = rules['class']
    print(teste2(x))

def teste2(grammar):
    code = []
    print(grammar)
    for i in grammar:
        print(i)
        if type(i) == str:
            if not re.search(r'[@!%]',i):
                code.append(i)
                print('xxx')
            # get type
            if '%' in i:
                code.append(i)
                print('x2')
            # drill down to rule
            if re.search(r'^!',i):
                print('zzz')
                replaced_string = i.replace('*','')
                if re.search(r'\*',i):
                    code.append(teste2(['*']+rules[replaced_string]))
                else:
                    code.append(teste2(rules[replaced_string]))
        else:
            print(f'aaa {list(i)}')
            code.append((teste2(i),))
    return code

if __name__ == "__main__":
    main()