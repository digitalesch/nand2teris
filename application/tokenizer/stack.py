from dataclasses import dataclass, field
from .tokenizer import Token, Tokenizer
import argparse
import os

@dataclass
class Pointer():
    index:  int
    memory: int

@dataclass
class Stack():
    file_name:              str                                  # file name for creation of static segment with @<filename>.<variable value> format
    SP:                     Pointer
    LCL:                    Pointer                              # push / pop offseted value RULE: addr=LCL+<offset>, SP--, *addr=*SP
    ARG:                    Pointer                              # push / pop offseted value RULE: addr=ARG+<offset>, SP--, *addr=*SP
    THIS:                   Pointer                              # push / pop offseted value RULE: addr=THIS+<offset>, SP--, *addr=*SP
    THAT:                   Pointer                              # push / pop offseted value RULE: addr=THAT+<offset>, SP--, *addr=*SP
    TEMP:                   Pointer                              # push / pop offseted value RULE: addr=5+<offset>, SP--/ SP++, *addr=*SP
    POINTER:                Pointer                              # push / pop 0 / 1 should provide THIS / THAT respectively: PUSH -> *SP = THIS / THAT; SP++; POP -> SP--; *SP=THIS/THAT
    STATIC:                 int = 0                              # start position of created variable
    LABEL:                  int = 0                              # integer for label naming purposes
    FUNCTION_LABELS:        list = field(default_factory=list)   # list that contains function labels for return statement, LIFO on list to get current return statment needs
    FUNCTION_DEFINITION:    dict = field(default_factory=dict)   # defines dict with tuple of (function name, function local variable)

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
        
        return [
            type_def[operation]['desc'],                 # comment on operation
            f"@{self.SP.index}",                         # code for selecting @SP
            f"M=M{type_def[operation]['symbol']}1"       # code for setting the memory address the - / + 1
        ]

    '''
        Calculates offset based on variable value of Token passed
    '''
    def calculate_offset(self, token: Token):
        # only generates offset if LCL, ARG, THIS, THAT
        # RULE: addr=<virtual segment>+<offset>, SP--, *addr=*SP
        #if token.segment_pointer in ['LCL','ARG','THIS','THAT']:
        attribute = getattr(self,token.segment_pointer if token.segment_pointer is not None else 'SP')

        # defines simple structure
        desc = f'// Calculates offset from virtual memory space getting RAM[*SP]={attribute.memory}+{token.variable}'
                    
        # TEMP segment is direct access
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


    '''
        Push to segment
    '''
    def push_to_segement(self, token: Token):
        final_code      = []
        stack_pointer   = getattr(self,'SP').index

        if token.segment_pointer in ['STATIC']:
            final_code += [
                f'// Generates STATIC variable {token.file}.{token.variable}',
                f'@{token.file}.{token.variable}',
                'D=M',
                f'@{stack_pointer}',
                'A=M',
                'M=D'
            ]
        if token.segment_pointer in ['CONSTANT']:
            final_code += [
                f'// Push to stack, RAM[{stack_pointer}]',
                f'@{token.variable}',
                'D=A',
                f'@{stack_pointer}',
                'A=M',
                'M=D'                
            ]
        
        # *SP = THIS / THAT; SP++;
        if token.segment_pointer in ['POINTER']:
            variable_value = int(token.variable)
            choose_this_that = 'THIS' if variable_value + 3 == 3 else 'THAT'

            final_code += [
                f'// Push from {choose_this_that} to stack into RAM[{stack_pointer}]',
                f'@{variable_value+3}',
                'D=M',
                f'@{stack_pointer}',
                'A=M',
                'M=D'
            ]


        if token.segment_pointer in ['LCL','ARG','THIS','THAT','TEMP']:
            desc = '// Get value from stack by accessing virtual segment offseted value'

            final_code += self.calculate_offset(token)  # gets offseted value in D-Reg

            final_code += [
                desc,                                   # comment on operation
                f"A=D",                                 # RAM[A] = RAM[D]
                f"D=M",                                 # D = RAM[*SP-1]
                f"@{stack_pointer}",                    # code for selecting @SP
                f"A=M",                                 # gets *SP-1 pointer memory value
                f"M=D"                                  # sets RAM[SP] = offseted value from virtual segment                
            ]

        # updates SP, if constant *SP++, else *SP--
        final_code += self.update_sp_code(1)
        
        return final_code

    '''
        pop from segment
    '''
    def pop_from_stack(self, token: Token):
        stack_pointer   = getattr(self,'SP').index
        final_code      = []

        # RULE: addr=<segment base addr>+<offset>, *SP=*addr, SP++
        if token.segment_pointer in ['LCL','ARG','THIS','THAT','TEMP']:
            desc = f'// Get value to stack by accessing {token.segment_pointer} virtual segment offseted value'

            final_code += self.calculate_offset(token)  # gets offseted value in D-Reg
            
            final_code += [
                'A=A-1',                                # gets SP value -1
                'D=M',                                  # gets value pushed on stack
                f"@{stack_pointer}",                    # code for selecting @SP
                'A=M',                                  # gets offseted value on stack that consists of offseted value
                'A=M',                                  # RAM[A] = *<OFFSET_VALUE>
                'M=D'                                   # RAM[*<OFFSET_VALUE>] = value pushed on stack
            ]

        #POP -> SP--; THIS/THAT = *SP
        if token.segment_pointer in ['POINTER']:
            variable_value = int(token.variable)
            
            # chooses between THIS/THAT
            choose_this_that = 'THIS' if variable_value + 3 == 3 else 'THAT'
            this_that_pointer = getattr(self,choose_this_that).index

            final_code += [
                f'// Pop from stack into RAM[{this_that_pointer}]',                
                f'@{stack_pointer}',                    # SP
                'A=M-1',                                # A=*SP-1
                'D=M',                                  # D=*SP
                f'@{this_that_pointer}',                # Gets THIS/THAT value
                'M=D',                                  # D=THIS/THAT
            ]
            
        # *filename.var_name = *SP--; *SP-- 
        if token.segment_pointer in ['STATIC']:
            final_code += [
                f'// Pop from stack into STATIC variable: {token.file}.{token.variable}',
                f'@{stack_pointer}',                    # SP
                'A=M-1',                                # A=*SP--
                'D=M',                                  # D=*SP--
                f'@{token.file}.{token.variable}',  # get static variable defined by {file_name}.{token.variable}
                'M=D'                                   # *filename.var_name = D
            ]

            self.STATIC += 1
        
        # updates SP
        final_code += self.update_sp_code(0)

        return final_code

    def create_addition_or_subtraction_statement(self, token: Token) -> list:        
        stack_pointer = getattr(self,'SP').index
        # dict index is equal to dictionary defining operations
        type_def = {
            2: {'desc': '// Adds up two numbers on the stack getting *SP-2 = ADD(*SP-1+*SP-2)',         'symbol': '+'},
            3: {'desc': '// Subtracts up two numbers on the stack getting *SP-2 = ADD(*SP-1-*SP-2)',    'symbol': '-'},
        }

        choose_addition_subtraction = type_def[2] if token.command_type == 2 else type_def[3]

        return [
            choose_addition_subtraction['desc'],                                            # comment
            f"@{stack_pointer}",                                                            # code for selecting @SP
            'A=M-1',                                                                        # gets *SP
            'D=M',                                                                          # gets D=*SP
            'A=A-1',                                                                        # gets *SP-1
            f"M=M{choose_addition_subtraction['symbol']}D",                                 # sets RAM[*SP-2] = ADD(*SP-1,*SP-2)
        ]

    '''
        generates conditional directives, based on equality qualifier and stack top most value
        definition:
            get two top most stack values and verifies if they're equal, greater or lesser when subtracting them
    '''
    def create_conditional_statement(self,token):
        final_code = []
        stack_pointer = getattr(self,'SP').index

        jmp_directive = {
            4: {'desc': '// Creates JEQ statement, based on *SP-1 if *SP-1 is equal to zero',       'symbol': 'JEQ'},
            5: {'desc': '// Creates JGT statement, based on *SP-1 if *SP-1 is greater than zero',   'symbol': 'JGT'},
            6: {'desc': '// Creates JLT statement, based on *SP-1 if *SP-1 is lesser than zero',    'symbol': 'JLT'},            
        }

        # Jump directives
        if token.command_type in [4,5,6]:
            final_code += [
                jmp_directive[token.command_type]['desc'],                                  # comment
                f"@{stack_pointer}",                                                        # code for selecting @SP
                'A=M-1',                                                                    # A=*SP-1
                'D=M',                                                                      # gets D=*SP-1
            ]

            final_code += self.update_sp_code(0)                                            # *SP = *SP-1

            final_code += [
                f"@{stack_pointer}",                                                        # code for selecting @SP
                'A=M-1',                                                                    # A=*SP-1
                'D=M-D',                                                                    # D=*SP-1 - *SP-2
            ]
            
            final_code += [
                f"@ELSE_{jmp_directive[token.command_type]['symbol']}.{self.LABEL}",    # names interval
                f"D;{jmp_directive[token.command_type]['symbol']}",                     # creates dynamic JMP based on D value
                f"@{stack_pointer}",                                                    # A=SP
                'A=M-1',                                                                # A=*SP--
                'M=0',                                                                  # RAM[*SP--]=0 if JMP_DIRECTIVE
                f"@END_IF_{jmp_directive[token.command_type]['symbol']}.{self.LABEL}",  # A=end_if label
                '1;JMP',                                                                # Unconditional jmp
                f"(ELSE_{jmp_directive[token.command_type]['symbol']}.{self.LABEL})",   # Creates ELSE_IF label
                f"@{stack_pointer}",                                                    # A=*SP
                'A=M-1',                                                                # A=*SP--
                'M=-1',                                                                  # RAM[*SP--]=1 if JMP_DIRECTIVE
                f"(END_IF_{jmp_directive[token.command_type]['symbol']}.{self.LABEL})",
            ]
            
            self.LABEL += 1

            return final_code

    '''
        negates stack top element, does not require to decrement SP, because it's "in-place" operation
    '''
    def create_negate_not_statement(self, token: Token) -> list:
        stack_pointer = getattr(self,'SP').index
        # dict index is equal to dictionary defining operations
        type_def = {
            7:  {'desc': '// Negates *SP--',            'symbol': '-'},
            10: {'desc': '// Not operation on *SP--',   'symbol': '!'},
        }

        choose_negate_not = type_def[7] if token.command_type == 7 else type_def[10]

        return [
            choose_negate_not['desc'],
            f"@{stack_pointer}",                                                            # code for selecting @SP
            'A=M-1',                                                                        # RAM[A] = *SP-1
            f"M={choose_negate_not['symbol']}M"                                             # chooses between negate / not statement
        ]

    '''
        creates AND / OR statements
    '''
    def create_and_or_statement(self, token: Token) -> list:
        final_code = []
        stack_pointer = getattr(self,'SP').index
        # dict index is equal to dictionary defining operations
        type_def = {
            8:  {'desc': '// And operation on *SP-1 and *SP-2',  'symbol': '&'},
            9:  {'desc': '// Or operation on *SP-1 and *SP-2',   'symbol': '|'},
        }

        choose_and_or = type_def[8] if token.command_type == 8 else type_def[9]

        final_code += self.update_sp_code(0)

        return final_code + [
            choose_and_or['desc'],
            f"@{stack_pointer}",                                                            # code for selecting @SP
            'A=M',                                                                          # A = SP
            'D=M',                                                                          # D = *SP
            f"@{stack_pointer}",                                                            # SP
            'A=M-1',                                                                        # A = SP
            'A=M',                                                                          # A = *SP
            f"D=D{choose_and_or['symbol']}A",                                               # D = D AND/OR M
            f"@{stack_pointer}",                                                            # SP
            'A=M-1',                                                                        # A = SP
            'M=D'
        ]

    '''
        generates label <label_name> statement
    '''
    def create_label_statement(self, token: Token) -> list:
        return [
            '// Creates label',
            f'({token.variable})',
        ]

    '''
        generates if-goto <label_name> statement, consumes stack value when checking
        rule:
            if topmost value of stack is equal to -1 (true), jump, else continue
    '''
    def create_if_goto_statement(self, token: Token) -> list:
        stack_pointer = getattr(self,'SP').index
        
        return [
            '// Creates if-goto <label_name> statement',
            f'@{stack_pointer}',                                        # A=SP
            'A=M-1',                                                    # A=*SP--
            'D=M',                                                      # D=*SP-- (some condition)
            f'@{stack_pointer}',                                        # A=SP
            'M=M-1',                                                    # M=M-1
            f'@{token.variable}',                                       # A=LABEL
            'D;JLT'                                                     # if value == -1 (true) jump            
        ]

    '''
        generates unconditional goto <label_name> statement
    '''
    def create_goto_statement(self, token: Token) -> list:        
        return [
            '// Creates unconditional goto <label_name> statement',
            f'@{token.variable}',                                       # A=LABEL
            '1;JMP'                                                     # if *LABEL equal to zero continue, else JMP
        ]

    '''
        generates bootstrap code
    '''
    def create_bootstrap_statment(self) -> list:
        stack_pointer   = getattr(self,'SP')
        arg_pointer     = getattr(self,'ARG')
        lcl_pointer     = getattr(self,'LCL')
        this_pointer    = getattr(self,'THIS')
        that_pointer    = getattr(self,'THAT')
        saved_frame     = [stack_pointer,lcl_pointer,arg_pointer,this_pointer,that_pointer]            
        final_code      = []

        for pointer in saved_frame:
            final_code += [
                f'// Starts bootstrap code by setting {pointer.index} to value {pointer.memory}',
                f'@{pointer.memory}',
                'D=A',                                                      # D=Initialized memory value
                f'@{pointer.index}',                                        # A=SP
                'M=D',                                                      # SP=Memory value            
            ]

        return final_code

    '''
        generates function statement
        command: function <function_name> <number_of_parameters>
        rule: 
            must push <number_of_parameters> to stack so the function works on them,
            once finished, push result to stack
            only function definition, not execution
            <number_of_parameters> are local arguments created on stack prior to starting code
        example code:
            function Sys.init 0
                push constant 4000	// test THIS and THAT context save
                pop pointer 0
                push constant 5000
                pop pointer 1
                call Sys.main 0
                pop temp 1
                label LOOP
                goto LOOP
    '''
    def create_function_statement(self, token: Token) -> list:
        self.FUNCTION_LABELS.append(token.segment_pointer)                                      # adds labels to last called function, so when "return" is called, it has the last label to jump
        self.FUNCTION_DEFINITION[token.segment_pointer] = int(token.variable)                   # creates dict definition of how many local variables need to be created

        final_code = []
        
        final_code = [
            f'// Creates code for {token.segment_pointer} function',
            f'({token.segment_pointer})'                                                    # sets start LABEL of function, when call <function_name> is used
        ]
        
        # creates rule that push to stack nArgs (n+1) times 0 constant for LCL segment
        # based on function definition: function <functioName> <localVariables>
        for i in range(int(token.variable)):
            final_code += self.push_to_segement(
                Token(
                    command='push constant 0',
                    tokens=['push','constant','0'],
                    segment_pointer='CONSTANT',
                    command_type=1,
                    variable='0'
                )
            )

        return final_code

    '''
        creates call,
        call <functionName> <nArgs>
        <nArgs> are arguments that were pushed to stack prior to calling, in which function will operate on
    '''
    def create_call_statement(self, token: Token) -> list:
        stack_pointer   = getattr(self,'SP').index
        arg_pointer     = getattr(self,'ARG').index
        lcl_pointer     = getattr(self,'LCL').index
        this_pointer    = getattr(self,'THIS').index
        that_pointer    = getattr(self,'THAT').index
        saved_frame     = [lcl_pointer,arg_pointer,this_pointer,that_pointer]
        final_code      = []
        
        # temp, save return address to stack, will be saved in @13, since RAM[13~15] are temp registers
        final_code += [                
            f'// Saves return address to stack',
            f'@{token.segment_pointer}${self.LABEL}',                                           # A=returnAddress
            'D=A',                                                                              # D=*pointer
            f'@{stack_pointer}',                                                                # A=SP
            'A=M',                                                                              # A=*SP
            'M=D',                                                                              # RAM[*SP]=*SP
        ]

        final_code += self.update_sp_code(1)                                                    # SP = *SP+1

        for pointer in saved_frame:
            final_code += [
                f'// Code to pointer index at {pointer} to stack',
                f'@{pointer}',                                                                  # A=pointer
                'D=M',                                                                          # D=*pointer
                f'@{stack_pointer}',                                                            # A=SP
                'A=M',                                                                          # A=*SP
                'M=D',                                                                          # RAM[*SP]=*SP
            ]

            final_code += self.update_sp_code(1)                                                # SP = *SP+1

        # sets ARG pointer to SP-5-nArgs
        final_code += [
            f'// Code to set ARG pointer',
            f'@{stack_pointer}',                                                                # A=SP
            'D=M',                                                                              # A=*SP
            f'@{token.variable}',                                                               # A=token.variable (nArgs)
            'D=D-A',                                                                            # D=SP-nArgs
            f'@5',                                                                              # A=savedFrameSize
            'D=D-A',                                                                            # D=SP-nArgs-savedFrameSize
            f'@{arg_pointer}',                                                                  # A=ARG
            'M=D'                                                                               # RAM[ARG]=SP-nArgs
        ]

        # sets LCL pointer to SP
        final_code += [
            f'// Code to set LCL pointer to SP value',
            f'@{stack_pointer}',                                                                # A=SP
            'D=M',                                                                              # D=*SP
            f'@{lcl_pointer}',                                                                  # A=LCL            
            'M=D'                                                                               # RAM[LCL]=SP
        ]

        # jumps to function code, no need to create label when return, because return address is saved
        final_code += [
            f'@{token.segment_pointer}',                                                        # A=LABEL_NAME
            '1;JMP',                                                                            # jump to function code
            f'({token.segment_pointer}${self.LABEL})'
        ]

        self.LABEL += 1

        return final_code

    def create_return_statement(self, token: Token) -> list:
        stack_pointer   = getattr(self,'SP').index
        arg_pointer     = getattr(self,'ARG').index
        lcl_pointer     = getattr(self,'LCL').index
        this_pointer    = getattr(self,'THIS').index
        that_pointer    = getattr(self,'THAT').index
        saved_frame     = [lcl_pointer,arg_pointer,this_pointer,that_pointer]
        final_code      = []        

        # will be saved in R13, since RAM[13-15] are temp registers, instead of @endFrame which uses static segment
        final_code += [
            '// Creates endFrame static variable',
            f'@{lcl_pointer}',                                                              # A=LCL
            'D=M',                                                                          # D=*LCL
            #f'@endFrame',                                                                   # A=SP
            '@13',                                                                          # A=R13
            'M=D',                                                                          # SP=*LCL
        ]

        # will be saved in R14, since RAM[13-15] are temp registers, instead of @endFrame which uses static segment
        final_code += [
            '// Creates retAddr static variable',
            #f'@endFrame',                                                                   # A=endFrame
            '@13',                                                                          # A=R13
            'D=M',                                                                          # D=*endFrame
            '@5',                                                                           # A=5
            'A=D-A',                                                                        # A=*endFrame-6
            'D=M',                                                                          # D=*(endFrame-6)
            '@14',                                                                          # A=R14
            #f'@retAddr',                                                                    # A=SP
            'M=D',                                                                          # SP=*LCL
        ]

        # creates rule that pops stack to argument 0
        final_code += self.pop_from_stack(
            Token(
                command='pop argument 0',
                tokens=['pop','argument','0'],
                segment_pointer='ARG',
                command_type=0,
                variable='0'
            )
        )

        # SP = *ARG+1
        final_code += [
            '// Changes SP value to *(ARG+1) value',
            f'@{arg_pointer}',                                                              # A=ARG
            'D=M',                                                                          # D=*ARG
            f'@{stack_pointer}',                                                            # A=SP
            'M=D+1',                                                                        # SP=*ARG+1
        ] 

        # returns saved frame to stack and jmps to saved address
        for pointer in saved_frame:
            final_code += [
                f'// Code to return saved pointer {pointer} to original positions on stack',
                #f'@endFrame',                                                               # A=endFrame
                '@13',                                                                      # A=R13 == endFrame
                'D=M',                                                                      # D=endFrame
                f'@{5-pointer}',                                                            # A=pointerIndex
                'D=D-A',                                                                    # D=endFrame-pointerIndex
                f'@{5-pointer}',                                                            # A=pointerIndex
                'A=D',                                                                      # D=pointer                
                'D=M',                                                                      # D=*pointer
                f'@{pointer}',                                                              # A=pointerIndex
                'M=D',                                                                      # D=pointer
            ]

        # Jumps to retAddr
        final_code += [
            '// Jumps to retAddr stored in static variable',
            #f'@retAddr',                                                                    # A=retAddr
            '@14',                                                                          # A=R14 == retAddr
            'A=M',                                                                          # D=*ARG
            '1;JMP'                                                                         # Jump to retAddr
        ]

        return final_code

    '''
        generates end function code. created to finish function code
    '''
    def create_end_statement(self, token: Token) -> list:
        return_label    = self.FUNCTION_LABELS.pop(-1)

        # errado, visto que pode ter mais de um return dentro da função
        return [
            '// Creates pass through code label, for function definition only',
            f'(END_FUNCTION_{return_label})',                                                # creates end_function label, so code isn't executed when defined
        ]

    def generate_operation(self, token: Token) -> list:
        final_code = []
                
        if token.command_type == 0:                 # pop
            final_code += self.pop_from_stack(token)
        if token.command_type == 1:                 # push
            final_code += self.push_to_segement(token)            
        if token.command_type == 2:                 # add
            final_code += self.create_addition_or_subtraction_statement(token)
        if token.command_type == 3:                 # sub
            final_code += self.create_addition_or_subtraction_statement(token)
        if token.command_type == 4:                 # eq
            final_code += self.create_conditional_statement(token)
        if token.command_type == 5:                 # gt
            final_code += self.create_conditional_statement(token)
        if token.command_type == 6:                 # lt
            final_code += self.create_conditional_statement(token)
        if token.command_type == 7:                 # negate
            final_code += self.create_negate_not_statement(token)
        if token.command_type == 8:                 # and
            final_code += self.create_and_or_statement(token)
        if token.command_type == 9:                 # or
            final_code += self.create_and_or_statement(token)
        if token.command_type == 10:                # not
            final_code += self.create_negate_not_statement(token)
        if token.command_type == 11:                # label
            final_code += self.create_label_statement(token)
        if token.command_type == 12:                # if-goto
            final_code += self.create_if_goto_statement(token)
        if token.command_type == 13:                # goto
            final_code += self.create_goto_statement(token)
        if token.command_type == 14:                # function
            final_code += self.create_function_statement(token)
        if token.command_type == 15:                # call
            final_code += self.create_call_statement(token)
        if token.command_type == 16:                 # return
            final_code += self.create_return_statement(token)
        if token.command_type == 17:                 # end
            final_code += self.create_end_statement(token)

        if token.command_type in [2,3]:
            final_code += self.update_sp_code(0)

        return final_code

def main():
    arguments_list = [
        {'name':'file_name','type':str,'help':'specifies the file to be read'}
    ]

    parser = argparse.ArgumentParser()

    for arg in arguments_list:
        parser.add_argument(
            arg['name'],type=arg['type'],help=arg['help']
        )

    args = parser.parse_args()

    path = os.path.splitext(args.file_name)
    file_name = os.path.split(path[0])[1]

    print(path,file_name)

    with open(f'{args.file_name}','r') as input_fp:
        code_lines = [line.strip() for line in input_fp.readlines()]
    
    stack = Stack(
        file_name=file_name,            # file_name for STATIC segment
        SP=Pointer(0,20),               # SP
        LCL=Pointer(1,30),              # LCL
        ARG=Pointer(2,35),              # ARG
        THIS=Pointer(3,40),             # THIS
        THAT=Pointer(4,50),             # THAT
        TEMP=Pointer(5,5),              # TEMP
        POINTER=Pointer(3,3)            # POINTER
    )

    tokens = []
    for code in code_lines:
        tmp_token = Tokenizer(code)
        # if some token is found, not being comment or empty spaces
        if tmp_token.token is not None:
            tokens.append(tmp_token)
    
    generated_code = []

    for token in tokens:
        generated_code += stack.generate_operation(token.token)        
        print(f'{token.token}, {stack.generate_operation(token.token)}')

    generated_code += stack.create_end_loop()

    with open(f"{args.file_name.split('.')[0]}.asm",'w') as output_fp:
        output_fp.write('\n'.join(generated_code))
    
if __name__ == '__main__':
    main()