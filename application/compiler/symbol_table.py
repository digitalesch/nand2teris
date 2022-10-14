from dataclasses import dataclass, field
from typing import Dict

'''
Will only need to mantain two symbol symbol_tables:
1 - Class variables
2 - Subroutine variables, being the first always "this - className - argument - class - 0" as the specified CompilerToken definition
'''
@dataclass
class InvalidSymbolTableDefinition(Exception):   
    data: str

@dataclass
class VariableNotFound(Exception):   
    data: str

# defines the class symbol symbol_table
@dataclass
class SymbolTable():   
    scope:          str # defines if its a class or subroutine scope
    symbol_table:   Dict = field(default_factory=lambda: {})
    indexes:        Dict = field(default_factory=lambda: {})

    def __post_init__(self):
        # defines possibilities for symbol_table indexes
        self.indexes        = {'static':0,'field':0} if self.scope == 'class' else {'argument':0,'local':0}

    '''
        starts compilation of subroutine symbol table, by defining the "this" first argument with className type
    '''
    def start_subroutine(self, class_name: str, subroutine_type: str):
        if self.scope == 'subroutine':
            self.symbol_table = {}
            self.indexes = {'argument':0,'local':0}
            if subroutine_type == 'method':
                self.define(symbol_name='this', symbol_type=class_name, symbol_kind='argument')

    '''
        add entry to symbol symbol_table with:
        name (String),
        type (String),
        kind (STATIC, FIELD, ARG or VAR)
    '''
    def define(self, symbol_name: str, symbol_type: str, symbol_kind: str):
        if symbol_kind in self.indexes.keys():
            self.symbol_table[symbol_name] = {'name': symbol_name, 'kind': symbol_kind, 'type': symbol_type, 'index': self.indexes[symbol_kind]}
            self.indexes[symbol_kind] += 1
        else:
            # raises error based on scope of symbol table
            raise InvalidSymbolTableDefinition(f'Symbol of kind "{symbol_kind}" is invalid for scope {self.scope}, with {self.indexes.keys()} definition!')
    
    '''
        find element based on symbol name and feature type, kind, index
    '''
    def find_symbol(self,symbol_name: str, feature: str = 'total'):
        if symbol_name in self.symbol_table.keys():            
            return self.symbol_table[symbol_name][feature] if feature != 'total' else self.symbol_table[symbol_name]

        raise ValueError(f'Value "{symbol_name}" not found in symbol table {self.scope}!')

    '''
        find element based on symbol name and feature type, kind, index
    '''
    def find_type(self,symbol_kind: str):
        #print([key for key, value in self.symbol_table.items() if value['kind'] == symbol_kind])
        return [key for key, value in self.symbol_table.items() if value['kind'] == symbol_kind]

        '''
        if symbol_name in self.symbol_table.keys():            
            return self.symbol_table[symbol_name][feature] if feature != 'total' else self.symbol_table[symbol_name]

        raise ValueError(f'Value "{symbol_name}" not found in symbol table {self.scope}!')
        '''

def main():
    class_symbol_table = SymbolTable('class')
    class_symbol_table.define('aaa','local','field')
    class_symbol_table.define('aaa2','local','static')
    #print(class_symbol_table.find_symbol('aaa','kind'))

    subroutine_symbol_table = SymbolTable('subroutine')
    subroutine_symbol_table.start_subroutine('Point')
    subroutine_symbol_table.define('aaa2','local','local')
    #print(subroutine_symbol_table.symbol_table)

if __name__ == '__main__':
    main()