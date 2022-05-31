from dataclasses import dataclass
from .tokenizer import Token
#from application.assembler.binary_encoder import BinaryEncoder

@dataclass
class Pointer():
    index:  int
    memory: int

    '''
        Updates pointer value
    '''
    def update_pointer(self):
        pass

@dataclass
class Stack():
    SP:         Pointer
    LCL:        Pointer     # push / pop offseted value RULE: addr=LCL+<offset>, SP--, *addr=*SP
    ARG:        Pointer     # push / pop offseted value RULE: addr=ARG+<offset>, SP--, *addr=*SP
    THIS:       Pointer     # push / pop offseted value RULE: addr=THIS+<offset>, SP--, *addr=*SP
    THAT:       Pointer     # push / pop offseted value RULE: addr=THAT+<offset>, SP--, *addr=*SP
    TEMP:       Pointer     # # push / pop offseted value RULE: addr=5+<offset>, SP--/ SP++, *addr=*SP
    STATIC:     Pointer     # static variables, from RAM[16] -> RAM[255], direct access, created by making @<File Name>.i, which will be translated to RAM[16], RAM[17] ... RAM[255]
    POINTER:    Pointer     # push / pop 0 / 1 should provide THIS / THAT respectively: PUSH -> *SP = THIS / THAT; SP++; POP -> SP--; *SP=THIS/THAT 
    GPR:        int = 0     # general purpose registers, from RAM[13] -> RAM[15], direct access
    PC:         int = 0
    LABEL:      int = 0

    '''
        generates code for incrementing / decrementing Stack Pointer (SP)
        0: decrements
        1: increments
    '''
    def update_sp_code(self, operation: int):
        # defines simple structure
        type_def = {
            0: {'desc': '// Updates Stack Pointer by decrementing it by 1', 'symbol': '-'},
            1: {'desc': '// Updates Stack Pointer by incrementing it by 1', 'symbol': '+'},
        }
        '''
        # push to stack 
        if token.segment_pointer == 'CONSTANT' and token.command_type == 1:
            type = 1
        
        # pop from stack or;
        # push from stack to virtual segment, decrementing SP
        if token.segment_pointer != 'CONSTANT':
            type = 0
        '''
        self.PC += 2

        return [
            type_def[operation]['desc'],                 # comment on operation
            f"@{self.SP.index}",                         # code for selecting @SP
            f"M=M{type_def[operation]['symbol']}1"       # code for setting the memory address the - / + 1
        ]

    '''
        Calculates offset based on variable value of Token passed
    '''
    def calculate_offset(self, token: Token):
        # only generates offset if LCL, ARG< THIS, THAT or STATIC virtual segments
        # since SP is direct acess memory, by *SP
        # others are *<POINTER> = *(<BASE_MEMORY>+<TOKEN.VARIABLE>)
        if token.segment_pointer != 'CONSTANT':
            if token.segment_pointer != 'POINTER':
                attribute = getattr(self,token.segment_pointer if token.segment_pointer is not None else 'SP')

                # defines simple structure
                desc = f'// Calculates offset from virtual memory space getting RAM[A]={attribute.memory}+{token.variable}'
                
                self.PC += 5

                select_direct_memory_or_pointer = 'M' if token.segment_pointer not in ['TEMP'] else 'A'

                tmp_code = [
                    desc,                                               # comment on operation
                    f"@{token.variable}",                               # code for selecting *segment_pointer
                    f"D=A",                                             # sets D-Reg to loaded A-Reg
                    f"@{attribute.index}",                              # code for selecting @SP
                    f"D=D+{select_direct_memory_or_pointer}",           # calculates *<POINTER> = *(<BASE_MEMORY>|<DIRECT_MEMORY>+<TOKEN.VARIABLE>)                
                    f"@0",                                              # code for selecting @SP
                    f"A=M",                                             # gets *SP
                    f"M=D",                                             # RAM[*SP] = offseted segment value                
                ]

                return tmp_code
            else:
                memory_access = {
                    '0': 3,
                    '1': 4
                }

                desc = f'// Gets direct memory access for pointer segment RAM[A]=*{memory_access[token.variable]}'

                tmp_code = [
                    desc,                                               # comment on operation
                    f"@{memory_access[token.variable]}",                # code for selecting *segment_pointer
                    f"D=M",                                             # RAM[*SP] = offseted segment value                
                ]

                return tmp_code


    '''
        Push to segment
    '''
    def push_to_segement(self, token: Token):
        final_code = []

        attribute = getattr(self,'SP')

        # push constant to stack and updates SP
        if token.segment_pointer == 'CONSTANT':
            desc = '// Get value to stack by accessing *SP'
            
            final_code += [
                desc,                                   # comment on operation
                f"@{token.variable}",                   # code for selecting *segment_pointer
                f"D=A",                                 # gets value from variable token
                f"@{attribute.index}",                  # code for selecting @SP
                f"A=M",                                 # gets pointer memory value
                f"M=D"                                  # sets RAM[SP]=token.variable   
            ]

            final_code += self.update_sp_code(1)

        if token.segment_pointer == 'POINTER':
            desc = '// Get value by returning pointer value'

            memory_access = {
                '0': 3,
                '1': 4
            }
            
            final_code += [
                desc,                                   # comment on operation
                f"@{memory_access[token.variable]}",    # code for selecting @POINTER
                f"A=M",                                 # A-Reg = POINTER_ADDRESS
                f"D=M",                                 # D-Reg = *POINTER_ADDRESS
                f"@{attribute.index}",                  # code for selecting @SP
                f"A=M",                                 # gets *SP-1 pointer memory value
                f"M=D"                                  # sets RAM[SP] = offseted value from virtual segment                
            ]

            self.PC += 5

            final_code += self.update_sp_code(1)

        # other pointer based virtual segments
        if token.segment_pointer not in ['TEMP','POINTER','CONSTANT']:
            desc = '// Get value to stack by accessing virtual segment offseted value'

            final_code += self.calculate_offset(token)  # gets offseted value in D-Reg

            final_code += [
                desc,                                   # comment on operation
                f"A=D",                                 # RAM[A] = RAM[D]
                f"D=M",                                 # D = RAM[*SP-1]
                f"@{attribute.index}",                  # code for selecting @SP
                f"A=M",                                 # gets *SP-1 pointer memory value
                f"M=D"                                  # sets RAM[SP] = offseted value from virtual segment                
            ]

            self.PC += 3

            final_code += self.update_sp_code(1)
        
        if token.segment_pointer == 'TEMP':
            final_code += self.calculate_offset(token)
            
            final_code += [
                '// Pops from static segments',
                'A=D',                                  # Gets value from offseted value
                'D=M',                                  #
                f"@{attribute.index}",                  # code for selecting @SP
                'A=M',                                  # *SP
                'M=D'                                   # *SP = offseted value
            ]

            final_code += self.update_sp_code(1)

        return final_code

    '''
        pop from segment
    '''
    def pop_to_segment(self, token: Token):
        attribute = getattr(self,'SP')

        final_code = []
        # decrement SP, and value can continue on stack as "garbage"
        if token.segment_pointer == 'CONSTANT':
            final_code += self.update_sp_code(0)
        elif token.segment_pointer != 'POINTER':
        #else:
            # push from stack to offseted virtual segment
            final_code += self.calculate_offset(token)

            final_code += [
                'A=A-1',                                # gets SP value -1
                'D=M',                                  # gets value pushed on stack
                f"@{attribute.index}",                  # code for selecting @SP
                'A=M',                                  # gets offseted value on stack that consists of offseted value
                'A=M',                                  # RAM[A] = *<OFFSET_VALUE>
                'M=D'                                   # RAM[*<OFFSET_VALUE>] = value pushed on stack
            ]

            final_code += self.update_sp_code(0)

        else:
            # push from stack to offseted virtual segment
            final_code += self.calculate_offset(token)

            final_code += [
                f"@{attribute.index}",                  # code for selecting @SP
                'A=M',                                  # gets offseted value on stack that consists of offseted value
                'M=D',                                  # RAM[*<OFFSET_VALUE>] = value pushed on stack
                'A=A-1',                                # gets SP value -1
                'D=M',                                  # gets value pushed on stack
                'A=A+1',
                'A=M',
                'M=D'
            ]

            final_code += self.update_sp_code(0)

        return final_code

    def create_end_loop(self):
        return [
            '// Creates program end loop'
            '\n(END_PROGRAM_LOOP)\n',
            '@END_PROGRAM_LOOP\n',
            'A;JMP\n'
        ]

    def generate_operation(self, token: Token):
        attribute = getattr(self,'SP')
        
        jmp_directive = {
            0: None,
            1: None,
            2: None,
            3: None,
            4: 'JEQ',
            5: 'JGT',
            6: 'JLT',
            7: None,
            8: None,
            9: None,
            10: None
        }

        definition = {
            # pop
            0: self.pop_to_segment(token),
            # push
            1: self.push_to_segement(token),            
            2: [
                '// Adds up two numbers on the stack getting *SP-2 = ADD(*SP-1+*SP-2)',         # comment
                f"@{attribute.index}",                                                          # code for selecting @SP
                'A=M-1',                                                                        # gets *SP
                'D=M',                                                                          # gets D=*SP
                'A=A-1',                                                                        # gets *SP-1
                f'M=D+M',                                                                       # sets RAM[*SP-2] = ADD(*SP-1,*SP-2)
            ],
            3: [
                '// Subtracts up two numbers on the stack getting *SP-2 = ADD(*SP-1-*SP-2)',    # comment
                f"@{attribute.index}",                                                          # code for selecting @SP
                'A=M-1',                                                                        # gets *SP
                'D=M',                                                                          # gets D=*SP
                'A=A-1',                                                                        # gets *SP-1
                f'M=M-D',                                                                       # sets RAM[*SP-2] = SUB(*SP-1,*SP-2)
            ],            
            4: [
                '// Equality',                                                                  # comment
                f"@{attribute.index}",                                                          # code for selecting @SP
                'A=M-1',                                                                        # gets *SP
                'D=M',                                                                          # gets D=*SP
                'A=A-1',                                                                        # gets *SP-1
                'M=M-D',                                                                        # sets RAM[*SP-2] = SUB(*SP-1,*SP-2)
                'D=M',
                f"@{attribute.index}",                                                          # code for selecting @SP
                'M=M-1',
                f'@ELSE.{self.LABEL}',
                f'D;{jmp_directive[token.command_type]}',
                f"@{attribute.index}",                                                          # code for selecting @SP
                'A=M',
                'A=A-1',
                'M=0',
                f'@END_IF.{self.LABEL}',
                'A;JMP',                
                f'(ELSE.{self.LABEL})',
                f"@{attribute.index}",                                                          # code for selecting @SP
                'A=M-1',
                'M=1',
                f'(END_IF.{self.LABEL})',
            ],
            # negate
            7: [
                f"@{attribute.index}",                                                          # code for selecting @SP
                'A=M-1',                                                                        # RAM[A] = *SP-1
                'M=-M'
            ],
            # and
            8: [
                '// And operation',
                f"@{attribute.index}",                                                          # code for selecting @SP
                'A=M-1',                                                                        # RAM[A] = *SP-1
                'D=M',                                                                          # D-Reg = RAM[*SP-1]
                f"@{attribute.index}",                                                          # code for selecting @SP
                'M=M-1',                                                                        # *SP = *SP-1
                'A=M-1',                                                                        # A-Reg = RAM[*SP-2]
                'A=M',                                                                          # 
                'D=D&A',
                f"@{attribute.index}",                                                          # code for selecting @SP
                'A=M-1',
                'M=D'
            ],
            9: [
                '// Or operation',
                f"@{attribute.index}",                                                          # code for selecting @SP
                'A=M-1',                                                                        # RAM[A] = *SP-1
                'D=M',                                                                          # D-Reg = RAM[*SP-1]
                f"@{attribute.index}",                                                          # code for selecting @SP
                'M=M-1',                                                                        # *SP = *SP-1
                'A=M-1',                                                                        # A-Reg = RAM[*SP-2]
                'A=M',                                                                          # 
                'D=D|A',
                f"@{attribute.index}",                                                          # code for selecting @SP
                'A=M-1',
                'M=D'
            ],
            10: [
                '// Not operation'
                f"@{attribute.index}",                                                          # code for selecting @SP
                'A=M-1',                                                                        # RAM[A] = *SP-1
                'M=!M',                                                                         # D-Reg = RAM[*SP-1]
            ]
        }

        # code to get always the same code for JMP operations, using token.command_type to check which JMP
        if token.command_type in [4,5,6]:
            command_index = 4
        else:
            command_index = token.command_type


        final_code = definition[command_index]
        if token.command_type in [2,3]:
            final_code += self.update_sp_code(0)

        try:
            return final_code
        except:
            return ''