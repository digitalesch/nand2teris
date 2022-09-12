# built-in
from dataclasses import dataclass
import argparse, os
from threading import local
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
            return self.symbol_tables['subroutine'].find_symbol(symbol_name)
        except ValueError:
            return self.symbol_tables['class'].find_symbol(symbol_name)

    '''
        updates symbol tables
    '''
    def update_symbol_table(self, scope: str, symbol_name:str, symbol_type: str, symbol_kind: str):
        self.symbol_tables[scope].define(symbol_name=symbol_name, symbol_type=symbol_type, symbol_kind=symbol_kind)

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

    '''
        compiles file, to output tokens and syntax
    '''
    def compile_files(self, file_path: str):
        if os.path.isfile(f'{os.path.join(os.getcwd(),file_path)}'):
            CompilationEngine(file_path)        
        else:
            for file in os.listdir(file_path):            
                if file.endswith(".jack"):
                    CompilationEngine(os.path.join(file_path,file))
    
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

    # compiles folder / single file using CompilationEngine class
    if os.path.isfile(f'{os.path.join(os.getcwd(),args.file_path)}'):
        CompilationEngine(args.file_path)
        file_path, file_full_name = os.path.split(args.file_path)
        file_name, file_extension = file_full_name.split('.')
        xml_tree = ET.parse(f"{os.path.join(os.getcwd(),file_path,file_name+'Syntax.xml')}")
        # update class variable table, by using "classVarDec" and "classVarDecList" tag
        class_name = [tag.text for tag in xml_tree.find('className')][0]
        print(class_name)
        cw = CodeWriter(class_name)
        
        for class_var_declaration in xml_tree.iterfind('classVarDec'):
            tmp = []
            for var_type in class_var_declaration:                
                # adds to dict since its type or kind
                if var_type.tag == 'keyword':
                    # kind and type variables
                    tmp.append(var_type.text)
                if var_type.tag == 'classVarDecList':
                    # inside classVarDecList is possible identifiers (1 or more) names, like "static int x,y;"
                    for var_name in var_type.iter():
                        if var_name.tag == 'identifier':
                            cw.update_symbol_table('class',var_name.text,tmp[1],tmp[0])

        # checks for subroutines
        for subroutine_declaration in xml_tree.iterfind('subroutineDec'):
            cw.symbol_tables['subroutine'].start_subroutine(cw.class_name)
            # check for paramter list, to create entry in subroutine symbol table
            parameter_list = subroutine_declaration.find('parameterList')
            tmp_param = []
            for parameter in parameter_list if parameter_list else []:
                if parameter.tag != 'symbol':
                    tmp_param.append(parameter.text)
            # writes parameters to symbol table
            if len(tmp_param) > 0:
                # rewrites tmp_param, since its appended as <type> <param_name>, ex: int x
                for key, value in {tmp_param[i+1]:tmp_param[i] for i in range(int(len(tmp_param)/2))}.items():
                    cw.symbol_tables['subroutine'].define(symbol_name=key, symbol_type=value, symbol_kind='argument')
            
            local_variables = subroutine_declaration.find('subroutineBody').find('varDec')
            tmp_local_var = []
            for local_var in local_variables if local_variables else []:
                print(local_var, local_var.text)
                if local_var.tag != 'symbol':
                    tmp_local_var.append(local_var.text)
            # writes parameters to symbol table
            if len(tmp_local_var) > 0:
                # rewrites tmp_param, since its appended as <type> <param_name>, ex: int x
                for key, value in {tmp_local_var[i+2]:tmp_local_var[i+1] for i in range(int(len(tmp_local_var)/3))}.items():
                    cw.symbol_tables['subroutine'].define(symbol_name=key, symbol_type=value, symbol_kind='local')
            print(cw.symbol_tables)

            '''
            for item in  subroutine_declaration.iter():
                print(subroutine_declaration,item)
            '''
    else:
        for file in os.listdir(args.file_path):
            if file.endswith(".jack"):
                CompilationEngine(os.path.join(args.file_path,file))    

if __name__ == '__main__':
    main()