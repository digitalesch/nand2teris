from dataclasses import dataclass

@dataclass
class Stack():
    SP:     int = 0
    LCL:    int = 0
    ARG:    int = 0
    THIS:   int = 0
    THAT:   int = 0
    TEMP:   int = 0 # temp registers, from RAM[5] -> RAM[12]
    GPR:    int = 0 # general purpose registers, from RAM[13] -> RAM[255]
    
    '''
        calculates segment offset
    '''
    def segment_offset_code(self,segment):
        # step description
        desc = f'// Offset from {segment}, based on pointer'

        if self.get_memory_segment(segment) != 1:
            # calculates offset based on pointer arithmetic, 
            generated_code = []
        else:
            # no code for constant
            generated_code = []
        return generated_code

    '''
        sets value pointed by specified {pointer} variable
    '''
    def set_pointer_value_code(self, pointer: str, set_value_to: int):
        # gets pointer attribute from class
        pointer_value = getattr(self,pointer)

        # defines simple structure
        desc = f'// Sets value pointed by {pointer}, with value {set_value_to}'
        return [
            desc,
            f"@{set_value_to}",             # gets value loaded into A-Register
            f"D=A",                         # sets value to D-Register from A-Register
            f"@{pointer_value}",            # sets RAM[{pointer_value}]=D
            f"A=M",                         # gets 
            f"M=D",                         # sets RAM[{pointer_value}]=D
        ]

    '''
        gets value pointer by {pointer} variable, returning it in D-Register
    '''
    def get_pointer_value_code(self, pointer: str):
        # gets pointer attribute from class
        pointer_value = getattr(self,pointer)

        # defines simple structure
        desc = f'// Returns value pointed by {pointer}, with value {pointer_value}'
        return [
            desc,
            f"@{pointer_value}",
            f"A=M",
            f"D=M",
        ]

    '''
        generates code for incrementing / decrementing Stack Pointer (SP)
        arguments:
            name:           type
            type:           int
            description:    0 if decrementing, 1 if incrementing SP
        return:
            type:           list[str]
            description:    list with string values with .asm code
    '''
    def update_sp_code(self, type):
        # defines simple structure
        type_def = {
            0: {'desc': '// Updates Stack Pointer, by decrementing it by 1', 'symbol': '-'},
            1: {'desc': '// Updates Stack Pointer, by incrementing it by 1', 'symbol': '+'},
        }

        return [
            type_def[type]['desc'],                 # comment on operation
            f"@{self.SP}",                          # code for selecting @SP
            f"M=M{type_def[type]['symbol']}1"       # code for setting the memory address the - / + 1
        ]

    '''
        generates code for constant incrementing / decrementing Stack Pointer (SP)
        return:
            type:           list[str]
            description:    list with string values with .asm code
    '''
    def local_segment_integer_code_gen(self):
        # defines simple structure
        desc = '// Loads integer to stack, through the A-Register'
        
        return [
            desc,                                   # comment on operation
            f"@{self.SP}",                          # code for selecting @SP            
        ]

    def get_memory_segment(self, segment: str):
        mapping = {
            'local':    1,
            'constant': 2,
            'argument': 3,
            'this':     4,
            'that':     5,
            'temp':     6
        }

        return mapping[segment]

    # push to given segment
    # if segment is "local", gets value and puts it in the stack
    # otherwise, gets value from stack and 
    def push(self, segment: str, value: int):
        tmp_code = []

        # add to local stack
        if self.get_memory_segment() == 1:
            # generates code before SP update, so SP has the next free memory address
            tmp_code += self.local_segment_integer_code_gen()
            self.SP += 1
            tmp_code += self.update_sp_code(1)
        else:
            self.SP -= 1
            self.update_sp_code(0)

    # pop from given segment
    # if segment is "local", removes value from stack, decrements SP
    # otherwise, gets value from segment i location and pushes to stack
    def pop(self, segment: str):
        # add to local stack
        if segment == 'local':
            self.SP -= 1
        else:
            self.SP += 1

stack = Stack(0,1,2,3,4,5,13)

print(stack.update_sp_code(1))
print(stack.get_pointer_value_code('SP'))
print(stack.set_pointer_value_code('SP',100))
print(stack.update_sp_code(0))