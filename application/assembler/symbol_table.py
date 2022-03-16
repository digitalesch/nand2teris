from dataclasses import dataclass
import logging

logging.basicConfig(filename='symbol_table.log', level=logging.DEBUG)

#logging.info('So should this')
#logging.warning('And this, too')
#logging.error('And non-ASCII stuff, too, like Øresund and Malmö')

@dataclass
class SymbolTable():
    symbols:                dict = None
    variable_position:      int = 16
    initialized_position:   int = 0

    def __post_init__(self) -> None:
        self.symbols = {}
        self.initialize_symbols_table()

    def initialize_symbols_table(self) -> None:
        # creates R0 - R15 symbols
        for item in range(16):
            self.symbols[f"R{item}"] = item
        # creates SCREEN entry
        self.symbols["SCREEN"] = 16384
        # creates KBO entry
        self.symbols["KBO"] = 24576
        # creates SP entry
        self.symbols["SP"] = 0
        # creates LCL entry
        self.symbols["LCL"] = 1
        # creates ARG entry
        self.symbols["ARG"] = 2
        # creates THIS entry
        self.symbols["THIS"] = 3
        # creates THAT entry
        self.symbols["THAT"] = 4

        # gets final initialized count from symbols dict
        self.initialized_position = len(self.symbols)

    def entry_is_present(self,entry):
        return entry in self.symbols

    def update_symbol(self, entry: str, value: int):
        self.symbols[entry] = value
    
    def add_entry(self, type: str,entry: str,value = -1) -> None:
        if not self.entry_is_present(entry):                    # Only adds to symbols table if not present
            if type == 'label':
                self.symbols[entry] = value                     # Adds label with -1 for later processing
            else:
                logging.debug(f'Symbol {entry} added with value {self.variable_position}')
                self.symbols[entry] = self.variable_position    # Adds entry table for variables
                self.variable_position += 1
    
    def generate_variable_symbols(self):
        for item in list(self.symbols)[self.initialized_position:]:             # updates variables with -1 value
            if self.symbols[item] < 0: 
                logging.debug(f'Symbol {item} added with value {self.variable_position}')
                self.symbols[item] = self.variable_position
                self.variable_position += 1