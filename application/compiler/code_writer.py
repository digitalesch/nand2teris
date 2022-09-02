# built-in
from dataclasses import dataclass
import argparse, os
import xml.etree.ElementTree as ET

# symbol table custom code
from symbol_table import SymbolTable, VariableNotFound
from compilation_engine import CompilationEngine

'''
Will only need to mantain two symbol tables:
1 - Class variables
2 - Subroutine variables, being the first always "this - className - argument - class - 0" as the specified CompilerToken definition
'''

@dataclass
class UndefinedSymbol(Exception):   
    data: str

@dataclass
class CodeWriter():
    class_name: str # defines writer for class file passed as parameter

    '''
        creates class and subroutine symbol tables
    '''
    def __post_init__(self):
        self.symbol_tables = {'class': SymbolTable('class'), 'subroutine': SymbolTable('subroutine')}
        self.symbol_tables['subroutine'].start_subroutine(self.class_name)

    '''
        finds symbol in subroutine level and if not found, searches class symbol table. If both fail, error is thrown
    '''
    def search_symbol_table(self, symbol_name: str):
        # tries to find the symbol in the subroutine symbol table and if not found, in the class symbol table
        try:
            self.symbol_tables['subroutine'].find_symbol(symbol_name)
        except ValueError:
            self.symbol_tables['class'].find_symbol(symbol_name)

    '''
        uses rule:
            if expression is a number n:
                output "push n"
            if expression is a variable var:
                output "push var"
            if expression is "exp1 op exp2"
                write_expression(exp1)
                write_expression(exp2)
                output "op"
            if expression is "op exp"
                write_expression(exp)
                output "op"
            if expression is "f(exp1, exp2))"
                write_expression(exp1)
                write_expression(exp2)
                output "call f"
    '''
    def write_expression(self, expression):
        pass

    

def main():
    x = CodeWriter('class')
    x.symbol_tables['class'].define('teste','int','static')
    print(x.symbol_tables)


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

    xml_tree = ET.parse(f'{args.file_path}')

    for tag in xml_tree.iter():
        print(f'{tag.tag}, {tag.text}')

    ce = CompilationEngine(xml_tree)
    tokens = ce.tokens
    print(tokens)

if __name__ == '__main__':
    main()