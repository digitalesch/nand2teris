# built-in
from dataclasses import dataclass
import argparse, os
from multiprocessing.sharedctypes import Value
from threading import local
import xml.etree.ElementTree as ET

# symbol table custom code
from symbol_table import SymbolTable, VariableNotFound
from compilation_engine_without_tags import CompilationEngine, flatten_list

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
    class_name:     str # defines writer for class file passed as parameter
    label_counter:  int = 0

    '''
        creates class and subroutine symbol tables
    '''
    def __post_init__(self):
        self.symbol_tables = {
            'class': SymbolTable('class'), 
            'subroutine': SymbolTable('subroutine'), 
            'function':SymbolTable('subroutine')
        }
        self.translate = {
            '>': 'gt',
            '<': 'lt',
            '=': 'eq',
        }

    '''
        finds symbol in subroutine level and if not found, searches class symbol table. If both fail, error is thrown
    '''
    def search_symbol_table(self, symbol_name: str):
        # tries to find the symbol in the subroutine symbol table and if not found, in the class symbol table
        try:
            return self.symbol_tables['subroutine'].scope,self.symbol_tables['subroutine'].find_symbol(symbol_name)
        except ValueError:
            return self.symbol_tables['class'].scope,self.symbol_tables['class'].find_symbol(symbol_name)

    '''
        updates symbol tables
    '''
    def update_symbol_table(self, scope: str, symbol_name:str, symbol_type: str, symbol_kind: str):
        self.symbol_tables[scope].define(symbol_name=symbol_name, symbol_type=symbol_type, symbol_kind=symbol_kind)

    '''
        writes expression symbols in order, so it can be postfixed later
    '''
    def write_expression(self, expression: ET, type: str = None) -> list:
        vm_commands = []
        
        #print(f'E: {expression}')
        if expression:
            for child in expression:
                #print(child)
                if child.tag in ['expression','expressionList']:
                    vm_commands.append(self.write_expression(child))
                if child.tag in ['identifier']:
                    #print(type)
                    vm_commands.append(VMCommand('variable' if type not in ['assignVariable','assignVariableName'] else 'assignVariable',child.text))                    
                if child.tag in ['keyword']:
                    vm_commands.append(VMCommand('keyword',child.text))
                if child.tag in ['integerConstant']:
                    vm_commands.append(VMCommand('constant',child.text))
                if child.tag in ['operation']:
                    vm_commands.append(VMCommand('operation',child.text))
                if child.tag in ['subroutineCall']:
                    subroutine_call_values = [subroutine_call_name.text for subroutine_call_name in child]
                    # gets different value if its a built-in
                    vm_commands.append(VMCommand('function' if subroutine_call_values[0] not in ['Math','Array','Sys'] else 'systemFunction',''.join(subroutine_call_values)))
                if child.tag in ['arrayType']:
                    vm_commands.append(VMCommand('arrayType',child.find('identifier').text))
                    #pass

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
                #print(f"recursion for operation {operation}, at index {expression.index(operation[0])}")
                if expression.index(operation[0]):
                    t.append(self.postfix_expression(expression[0]))
                    # provides context for exp1 op exp2, when not found, it's op exp
                    t.append(self.postfix_expression(expression[2]))
                    t.append(operation[0])
                else:
                    t.append(self.postfix_expression(expression[1]))
                    t.append(operation[0])
            # no operation is found
            else:
                # consant
                if len(expression) == 1:
                    t.append(self.postfix_expression(expression[0]))
                function = list(filter(lambda x: isinstance(x,VMCommand),[self.compare_command(term,[VMCommand(type='function'),VMCommand(type='systemFunction')]) for term in expression if isinstance(term,VMCommand)]))
                if function:
                    # for each item (list item) in function parameter list
                    for param_list in expression[1:]:
                        t.append(self.postfix_expression(param_list))
                    t.append(self.postfix_expression(expression[0]))  
                assignment = list(filter(lambda x: isinstance(x,VMCommand),[self.compare_command(term,[VMCommand(type='arrayAssignment')]) for term in expression if isinstance(term,VMCommand)]))
                if assignment:
                    t.append(VMCommand(type='arrayAssignment',value=assignment[0].value))
                    t.append(self.postfix_expression(expression[1:]))
                array_type = list(filter(lambda x: isinstance(x,VMCommand),[self.compare_command(term,[VMCommand(type='arrayType')]) for term in expression if isinstance(term,VMCommand)]))
                if array_type:
                    pass
        else:
            #print(f'constant: {expression}')            
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
        returns compiled expression
    '''
    def treat_compiled_expression(self, statement: ET, tag: str):
        return self.postfix_expression(self.write_expression(statement.find(tag),tag))

    '''
        statement treatment
    '''
    def treat_statement(self, statement: ET):
        expression_vm_commands = []
        if statement.tag == 'whileStatement':
            '''
                label L1
                    compiled (expression)
                    not
                    if-goto L2
                    compiled (statements)
                    goto L1
                label L2                    
            '''
            expression_vm_commands.append(VMCommand(type='label',value=f'label_check'))
            expression_vm_commands += self.treat_compiled_expression(statement,'expression')
            expression_vm_commands.append(VMCommand(type='operation',value='~'))            
            expression_vm_commands.append(VMCommand(type='ifgoto',value=f'label_end'))
            for branch_statements_expression in statement.find('statements'):
                expression_vm_commands += self.treat_compiled_expression(branch_statements_expression,'expression')
            expression_vm_commands.append(VMCommand(type='ifgoto',value=f'label_check'))
            expression_vm_commands.append(VMCommand(type='label',value=f'label_end'))
        if statement.tag == 'letStatement':
            print('compiling letStatement')
            #print(statement.find('arrayAssignment'))

            array_assignment = statement.find('arrayAssignment')
            if array_assignment:
                expression_vm_commands += [
                    self.treat_compiled_expression(array_assignment,'assignVariableName'),
                    self.treat_compiled_expression(array_assignment,'expression'),
                    VMCommand(type='operation',value='+'),
                    self.treat_compiled_expression(statement,'expression'),
                    VMCommand(type='literal',value='pop temp 0'),
                    VMCommand(type='literal',value='pop pointer 1'),
                    VMCommand(type='literal',value='push temp 0'),
                    VMCommand(type='literal',value='pop that 0'),
                ]
                #print(expression_vm_commands)
            else:
                # gets expression compiled
                expression_vm_commands += self.treat_compiled_expression(statement,'expression')
                # assigns to variable
                expression_vm_commands += self.treat_compiled_expression(statement.find('assignVariable'),'assignVariableName')                
        if statement.tag == 'ifStatement':
            '''
                    compiled (expression)
                    not
                    if-goto L1
                    compiled (statements1)
                    goto L2
                label L1
                    compiled (statements2)
                label L2
            '''
            print('compiling ifStatement')
            # compiles condition
            expression_vm_commands += self.treat_compiled_expression(statement,'expression')
            expression_vm_commands.append(VMCommand(type='operation',value='~'))            
            expression_vm_commands.append(VMCommand(type='ifgoto',value=f'label_else'))
            for branch_statements_expression in statement.find('statements_if'):
                expression_vm_commands += self.treat_compiled_expression(branch_statements_expression,'statements_if')
            expression_vm_commands.append(VMCommand(type='goto',value=f'label_end'))
            expression_vm_commands.append(VMCommand(type='label',value=f'label_else'))
            for branch_statements_expression in statement.find('statements_else'):
                expression_vm_commands += self.treat_compiled_expression(branch_statements_expression,'statements_else')
            expression_vm_commands.append(VMCommand(type='label',value=f'label_end'))
        if statement.tag == 'returnStatement':
            print('compiling returnStatement')
            expression_vm_commands += self.treat_compiled_expression(statement,'expression')
            # null expression returned
            if len(expression_vm_commands)==0:
                expression_vm_commands.append(VMCommand(type='constant',value='0'))    
            expression_vm_commands.append(VMCommand(type='literal',value='return'))
        
        return expression_vm_commands

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

    processed_files = []

    if os.path.isfile(f'{os.path.join(os.getcwd(),args.file_path)}'):
        CompilationEngine(args.file_path)
        processed_files.append(os.path.join(os.getcwd(),args.file_path))
    else:
        for file in os.listdir(args.file_path):
            if file.endswith(".jack"):
                CompilationEngine(os.path.join(args.file_path,file))
                processed_files.append(os.path.join(args.file_path,file))

    for file in processed_files:
        file_path, file_full_name = os.path.split(file)
        file_name, file_extension = file_full_name.split('.')
        xml_tree = ET.parse(f"{os.path.join(os.getcwd(),file_path,file_name+'Syntax.xml')}")
        # update class variable table, by using "classVarDec" and "classVarDecList" tag
        class_name = [tag.text for tag in xml_tree.find('className')][0]
        print(f'Compiling {class_name}!')

        procedural_commands = []

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
            # check for parameter list, to create entry in subroutine symbol table
            tmp_param = []

            subroutine_type = subroutine_declaration.find('keyword').text
            subroutine_name = subroutine_declaration.find('subroutineName').find('identifier').text
            print(f"Running '{subroutine_name}' function of type {subroutine_type}!")
            cw.symbol_tables['function'].define(subroutine_name,subroutine_type,'local')

            cw.symbol_tables['subroutine'].start_subroutine(class_name,subroutine_type)
            
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

            vm_commands = []

            vm_commands.append(VMCommand(type='literal',value=f'function {class_name}.{subroutine_name}'))

            if subroutine_type == 'constructor':
                print(f'initializing constructor code for class {class_name}!')
                fields = [value for key, value in cw.symbol_tables['class'].symbol_table.items() if value['kind']=='field']
                #print(fields)
                vm_commands += [
                    VMCommand(type='literal', value=f'push {len(fields)}'),
                    VMCommand(type='literal', value=f'call Memory.alloc 1'),
                    VMCommand(type='literal', value=f'pop pointer 0'),
                ]
            if subroutine_type == 'method':
                vm_commands += [
                    VMCommand(type='literal', value=f'push argument 0'),
                    VMCommand(type='literal', value=f'pop pointer 0'),
                ]

            # writes expressions
            for statements_declaration in subroutine_declaration.find('subroutineBody').find('statements'):                
                vm_commands += cw.treat_statement(statements_declaration)

            #print(vm_commands)
            postfix_commands = list(flatten_list(vm_commands))
            print(postfix_commands)    
            print(cw.symbol_tables)

            for item in postfix_commands:
                #print(item)
                if item.type == 'literal':
                    procedural_commands.append(item.value)
                if item.type in ['constant']:
                    procedural_commands.append(f'push constant {item.value}')
                # gets variable index from symbol table
                if item.type in ['variable','assignVariable','arrayAssignment','arrayType']:
                    found_symbol = cw.search_symbol_table(item.value)
                    procedural_commands.append(f"{'push' if item.type in ['variable','arrayAssignment'] else 'pop'} {found_symbol[1]['kind'] if found_symbol[1]['kind'] != 'field' else 'this'} {found_symbol[1]['index']}")
                if item.type == 'operation':
                    operation_transalate = {
                        '=':'eq',
                        '~':'not',
                        '+':'add',
                        '-':'sub',
                        '*':'call Math.multiply 2'
                    }
                    procedural_commands.append(f'{operation_transalate[item.value]}')
                if item.type == 'function':
                    subroutine_call_object,subroutine_call_function = item.value.split('.')
                    print(item)
                    
                    try:
                        found_symbol = cw.search_symbol_table(subroutine_call_object)
                        #print(found_symbol)
                        procedural_commands += [
                            f"push {found_symbol[1]['kind']} {found_symbol[1]['index']}",
                            f"call {found_symbol[1]['type']}.{subroutine_call_function} 1"
                        ]
                    except ValueError as VE:
                        print(VE)
                        if subroutine_call_object not in ['Math','Array','Sys']:
                            procedural_commands += [
                                f"call {item.value}"
                            ]

                # compiles this / that
                if item.type == 'keyword':
                    procedural_commands.append(f"push pointer {0 if item.value == 'this' else 1}")

                if item.type == 'systemFunction':
                    procedural_commands.append(f"call {item.value}")

            print(procedural_commands)            
        
        with open(f"{os.path.join(os.getcwd(),file_path,file_name+'.vm')}",'w') as fp:
            fp.write('\n'.join(procedural_commands))

if __name__ == '__main__':
    main()