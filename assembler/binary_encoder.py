from dataclasses import dataclass
from dis import Instruction
from typing import List
import re
from symbol_table import SymbolTable

@dataclass
class Token:
    type:       int                                                                                             # A-instruction or C-instruction
    binary:     str                                                                                             # Encoded binary value
    code:       str                                                                                             # Original code
    variable:   str                                                                                             # variable name
    line:       int                                                                                             # Line number

@dataclass
class BinaryEncoder:
    tokens:                 List[Token] = None
    symbol_table:           SymbolTable = SymbolTable()    
    line_number:            int = 0
    code:                   str = None
    

    '''
        Removes all spaces of given code line
        param: 
            code: str
        return:
            str -> string without spaces
    '''
    def remove_spaces(self):
        self.code = re.sub(r'\s+','',self.code)
    
    '''
        Cleans code, by removing spaces and comments
        param: 
            code: str
        return:
            str -> cleaned string
    '''
    def clean_code(self):
        regex_return = re.findall(r'(.*)(?=\/\/)',self.code)                                                    # tries to remove comments
        self.code = regex_return[0] if len(regex_return) > 0 else self.code                                     # if no comment is found, regex will return null list and code must be trimed
        self.remove_spaces()                                                                                    # removes spaces from code

    '''
        Cleans out code and checks if its a command
        param: 
            code: str
        return:
            int
                False: command line is either a comment or empty line
                True: command line is C or A instruction                
    '''
    def is_command(self):
        self.clean_code()                                                                                       # cleans up code
        return True if len(self.code) else False                                                                # returns True if cleaned string has length > 0

    '''
        Returns instruction set for self.code after cleaned
        param: 
            code: str
        return:
            int
                0: A-Instruction
                1: C-Instruction
                2: L-Instruction -> Label instruction, defined by (<VAR_NAME>)
    '''
    def define_instruction_set(self):
        instruction_set = {
            '@': 0,
            '(': 2
        }
        if self.is_command():                                                                                   # checks if it's a command
            return instruction_set[self.code[0]] if self.code[0] in instruction_set.keys() else 1               # returns type based on instruction_set or 1 since its a C-Instruction
        else:
            return -1                                                                                           # returns -1 when empty / comment lines

    '''
        C-Instruction is comprised of:
        dest = comp ; jump
        111 a c1 c2 c3 c4 c5 c6 d1 d2 d3 j1 j2 j3
    '''
    def parse_c_instruction(self):
        c_instruction_part  = '111'
        destination_part    = '000'
        jump_part           = '000'

        dest_codes = {
            'M':    '001',
            'D':    '010',
            'MD':   '011',
            'A':    '100',
            'AM':   '101',
            'AD':   '110',
            'AMD':  '111'
        }

        jmp_codes = {
            'JGT':   '001',
            'JEQ':   '010',
            'JGE':   '011',
            'JLT':   '100',
            'JNE':   '101',
            'JLE':   '110',
            'JMP':   '111'
        }

        comp_codes = {
            '0':    '0101010',
            '1':    '0111111',
            '-1':   '0111010',
            'D':    '0001100',
            'A':    '0110000',
            'M':    '1110000',
            '!D':   '0001101',
            '!A':   '0110011',
            '!M':   '1110001',
            'D+1':  '0011111',
            'A+1':  '0110111',
            'M+1':  '1110111',
            'D-1':  '0001110',
            'A-1':  '0110010',
            'M-1':  '1110010',
            'D+A':  '0000010',
            'D+M':  '1000010',
            'D-A':  '0010011',
            'D-M':  '1010011',
            'A-D':  '0000111',
            'M-D':  '1000111',
            'D&A':  '0000000',
            'D&M':  '1000000',
            'D|A':  '0010101',
            'D|M':  '1010101',
        }

        # splits string into command parts
        split_parts = re.findall(r'(([AMD]*)=+)?([01AMD\+\-&|!]+);*(.*)?',self.code)[0]
        
        generate_dest = False
        generate_jmp = False

        if split_parts[1] != '':
            generate_dest = True
        if split_parts[3] != '':
            generate_jmp = True
        
        return f"{c_instruction_part}{comp_codes[split_parts[2]]}{dest_codes[split_parts[1]] if generate_dest else destination_part}{jmp_codes[split_parts[3]] if generate_jmp else jump_part}"

    '''
        Returns the encoded instruction to binary
        return:
            string
                binary-encoded string
    '''
    def encode_instruction(self):
        if self.is_command():
            instruction_set = self.define_instruction_set()

            if instruction_set == 0:                                                                            # A-instruction                
                temp_code = self.code[1:]                                                                       # removes ";" from code line
                try:
                    return "{0:016b}".format(int(temp_code))                                                    # checks if it's a value
                except ValueError:                                                                              # parsed value is a label
                    if not self.symbol_table.entry_is_present(temp_code):                                       # if value is already in symbols_table
                        self.symbol_table.add_entry('label',temp_code,-1)                                       # adds variable to symbols table
    

            if instruction_set == 1:                                                                            # C-Instruction
                return self.parse_c_instruction()

            if instruction_set == 2:                                                                            # L-Instruction                
                temp_code = re.findall(r'\((.*)\)',self.code)[0]
                if self.symbol_table.entry_is_present(temp_code):                       
                    self.symbol_table.update_symbol(temp_code,self.line_number)
                else:
                    self.symbol_table.add_entry('label', temp_code, self.line_number)                           # adds variable to symbols table

    '''
        Return variable / label name
    '''
    def get_variable_label_name(self):
        if self.define_instruction_set() != 1:
            self.clean_code()                                                                                   # cleans code
            lookup_name = re.findall(r'@(.*)|\((.*)\)',self.code)
            return (
                (lookup_name[0][0] if lookup_name[0][0] != '' else lookup_name[0][1]) 
                    if len(lookup_name) > 0 else None                                                           # gets alpha-numeric value from either @1, @i or (LOOP) type of statments 
            )

    '''
        Encodes variabels to values after the passed encoding returns null, 
        by searching the symbol table and encoding the variable dict value
    '''
    def encode_variables(self, tokens):
        for token in tokens:
            if token.type >= 0 and token.binary is None:                                                        # A-instruction with label / variable name               
                token.binary = "{0:016b}".format(int(self.symbol_table.symbols[token.variable]))

        return tokens                

    def tokenize(self,code):
        self.code = code                                                                                        # sets internal class code to passed string        
        self.clean_code()                                                                                       # cleans out code
        
        tmp_token = Token(
            self.define_instruction_set(),
            self.encode_instruction(),
            self.code,
            self.get_variable_label_name(),
            self.line_number
        )

        print(tmp_token)
        self.line_number += 1 if self.define_instruction_set() in [0,1] else 0                                  # gets line number for code, ignores empty lines or comments
        return tmp_token