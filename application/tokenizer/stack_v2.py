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
    SP:     Pointer
    LCL:    Pointer
    ARG:    Pointer
    THIS:   Pointer
    THAT:   Pointer
    TEMP:   Pointer     # temp registers, from RAM[5] -> RAM[12], direct access
    STATIC: Pointer     # static variables, from RAM[16] -> RAM[255], direct access
    GPR:    int = 0     # general purpose registers, from RAM[13] -> RAM[15], direct access
    PC:     int = 0    

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
                #f"D=M",                                            # gets pointer memory value
                f"@0",                                              # code for selecting @SP
                f"A=M",                                             # gets *SP
                f"M=D",                                             # RAM[*SP] = offseted segment value                
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

        else:
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

        # other pointer based virtual segments
        elif token.segment_pointer not in ['TEMP']:
            print(token)
            desc = '// Get value to stack by accessing virtual segment offseted value'

            final_code += self.calculate_offset(token)

            final_code += [
                desc,                                   # comment on operation
                f"A=A-1",                               # RAM[A] = *SP-1
                f"D=M",                                 # D = RAM[*SP-1]
                f"A=A+1",                               # RAM[A] = *SP
                f"A=M",                                 # gets offseted address value put on stack
                f"M=D",                
                #f"@{attribute.index}",                  # code for selecting @SP
                #f"M=M-1",                               # gets *SP-1 pointer memory value
                #f"M=D"                                  # sets RAM[SP] = offseted value from virtual segment                
            ]

            self.PC += 3

            final_code += self.update_sp_code(0)
        else:
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

    def create_end_loop(self):
        return [
            '// Creates program end loop'
            '\n(END_PROGRAM_LOOP)\n',
            '@END_PROGRAM_LOOP\n',
            'A;JMP\n'
        ]

    def generate_operation(self, token: Token):
        definition = {
            # pop
            0: self.pop_to_segment(token),
            # push
            1: self.push_to_segement(token),
            2: [
                '// Subtracts two stack numbers *SP-2 = ADD(*SP-1+*SP-2)',              # comment
                '@0',                                                                   # gets SP
                'A=M-1',                                                                # gets *SP
                'D=M',                                                                  # gets D=*SP
                'A=A-1',                                                                # gets *SP-1
                f'M=D+M',                                                               # sets RAM[*SP-2] = SUB(*SP-1,*SP-2)
            ],
            3: [
                '// Adds up two numbers on the stack getting *SP-2 = ADD(*SP-1+*SP-2)', # comment
                '@0',                                                                   # gets SP
                'A=M-1',                                                                # gets *SP
                'D=M',                                                                  # gets D=*SP
                'A=A-1',                                                                # gets *SP-1
                f'M=D+M',                                                               # sets RAM[*SP-2] = ADD(*SP-1,*SP-2)
            ],
            4: [
                '// Subtracts up two numbers on the stack getting *SP-2 = ADD(*SP-1-*SP-2)', # comment
                '@0',                                                                   # gets SP
                'A=M-1',                                                                # gets *SP
                'D=M',                                                                  # gets D=*SP
                'A=A-1',                                                                # gets *SP-1
                f'M=D-M',                                                               # sets RAM[*SP-2] = SUB(*SP-1,*SP-2)
            ]
        }

        #final_code = definition[token.command_type] + self.update_sp_code(Token(None,None,'TESTE',0,None))

        try:
            return definition[token.command_type]                                       # update SP, *SP--
        except:
            return ''