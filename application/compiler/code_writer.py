# built-in
from dataclasses import dataclass
import argparse, os
from threading import local
import xml.etree.ElementTree as ET

# symbol table custom code
from symbol_table import SymbolTable, VariableNotFound
from compilation_engine_without_tags import CompilationEngine

'''
Will only need to mantain two symbol tables:
1 - Class variables
2 - Subroutine variables, being the first always "this - className - argument - class - 0" as the specified CompilerToken definition
'''

@dataclass
class VMCommand():
    type:       str = None
    value:      str = None

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
        writes expression symbols in order, so it can be postfixed later
    '''
    def write_expression(self, expression: ET):
        vm_commands = []
        
        for child in expression:
            if child.tag in ['expression','expressionList']:
                vm_commands.append(self.write_expression(child))
            if child.tag in ['integerConstant','identifier']:
                vm_commands.append(VMCommand('constant',child.text))
            if child.tag in ['operation']:
                vm_commands.append(VMCommand('operation',child.text))
            if child.tag in ['subroutineCall']:
                vm_commands.append(VMCommand('function',''.join([subroutine_call_name.text for subroutine_call_name in child])))
        
        return vm_commands

    '''
        rule:
            - when list is found, recursively uses function
                - when operator type is found, exp is either "exp1 op exp2" or "op exp"
                - when function is first element of expression, its "f(x1,x2,...)" type
            - when not list size is 1 and first element is constant, return constant
    '''
    def postfix_expression(self,expression):
        t = []
        
        if isinstance(expression,list):
            operation = list(filter(lambda x: isinstance(x,VMCommand),[self.compare_command(term,[VMCommand(type='operation')]) for term in expression if isinstance(term,VMCommand)]))
            if operation:                
                print(f"recursion for operation {operation}, at index {expression.index(operation[0])}")
                if expression.index(operation[0]):
                    print(f'exp1: {expression[0]}')
                    t.append(self.postfix_expression(expression[0]))
                    # provides context for exp1 op exp2, when not found, it's op exp
                    print(f'exp2: {expression[2]}')
                    t.append(self.postfix_expression(expression[2]))
                    print(f'op: {operation[0]}')
                    t.append(operation[0])
                else:
                    print('exp')
                    t.append(self.postfix_expression(expression[1]))
                    print('op')
                    t.append(operation[0])
            # no operation is found
            else:
                print('else')
                # consant
                if len(expression) == 1:
                    t.append(self.postfix_expression(expression[0]))
                function = list(filter(lambda x: isinstance(x,VMCommand),[self.compare_command(term,[VMCommand(type='function')]) for term in expression if isinstance(term,VMCommand)]))
                if function:
                    print(f"recursion for function {function}")
                    print(f'parameter list: {expression[1:]}')
                    # for each item (list item) in function parameter list
                    for param_list in expression[1:]:
                        t.append(self.postfix_expression(param_list))
                    t.append(self.postfix_expression(expression[0]))
        else:
            print(f'constant: {expression}')
            t.append(expression)

        return t

    '''
        compares two commands
    '''
    def compare_command(self, input: VMCommand, expectation: VMCommand):
        if any(
            [
                (input.type if command.type else None)==command.type and 
                (input.value if command.value else None)==command.value 
                for command in expectation
            ]
        ):
            return input
        else:
            return False


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
            # check for parameter list, to create entry in subroutine symbol table
            tmp_param = []

            print(f"Running '{subroutine_declaration.find('subroutineName').find('identifier').text}' function!")

            # creates parameters as a list, since comma separates them, ex: "int a, int b" -> ['int', 'a', 'int', 'b']
            for parameter in subroutine_declaration.find('parameterList'):
                if parameter.tag != 'symbol':
                    tmp_param.append(parameter.text)
            # writes parameters to symbol table
            if len(tmp_param):
                # rewrites tmp_param, since its appended as <type> <param_name>, ex: int x
                for key, value in {tmp_param[i*2+1]:tmp_param[i*2] for i in range(int(len(tmp_param)/2))}.items():
                    # updates the symbol table, since values are of dict type with values {'<variable_name>': '<variable_type'>} -> {'a': 'int', 'b': 'int'}
                    cw.symbol_tables['subroutine'].define(symbol_name=key, symbol_type=value, symbol_kind='argument')
                        
            # aggregates all local variables into a list
            all_local_var = []
            for variable_declaration in subroutine_declaration.find('subroutineBody').find('subroutineVarDec'):
                # if local variable, by tab varDec exists, append to all_local_var
                if variable_declaration:
                    # temporary list for containing each individual var set, ex: "var int length, teste; var char t;" -> [['var', 'int', 'length', 'teste'], ['var', 'char', 't']]
                    tmp_local_var = []
                    for local_variable in variable_declaration:
                        if local_variable.tag != 'symbol':
                            tmp_local_var.append(local_variable.text)
                    all_local_var.append(tmp_local_var)
            
            # writes parameters to subroutine symbol table
            for local_variable_declaration in all_local_var:
                # two first elements have "var" keyword and type of varialbe, rest of list has variable names
                for local_variable_name in local_variable_declaration[2::]:
                    cw.symbol_tables['subroutine'].define(symbol_name=local_variable_name, symbol_type=local_variable_declaration[1], symbol_kind='local')
                
            
            expression_vm_commands = []
            # writes expressions
            for statments_declaration in subroutine_declaration.find('subroutineBody').find('statements'):                
                for statement_dec in statments_declaration.findall('expression'):                    
                    expression_vm_commands += cw.write_expression(statement_dec)
            print(f"Formatted expression {expression_vm_commands}")            
            
            print(f"Push commands: {cw.postfix_expression(expression_vm_commands)}")                    
    else:
        for file in os.listdir(args.file_path):
            if file.endswith(".jack"):
                CompilationEngine(os.path.join(args.file_path,file))

if __name__ == '__main__':
    main()