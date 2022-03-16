# std-lib import
from dataclasses import dataclass
from distutils import command
import re

@dataclass
class Token():
    file:               str     = None
    command:            str     = None
    tokens:             list    = None
    segment_pointer:    str     = None
    command_type:       int     = 0
    variable:           str     = None

@dataclass
class Tokenizer:
    file:               str
    command:            str
    tokens:             list = None
    token:              Token   = None

    def __post_init__(self):
        self.clean_code()
        self.tokenize()
        #print(f'Token: {self.token} is {self.expression_type()}')
        # creates push / pop tokens
        if self.expression_type() == 1:
            self.token = Token(
                file=self.file,
                command=self.command,
                tokens=self.tokens,
                segment_pointer=self.get_memory_segment(self.tokens[1]),
                command_type=self.get_command_type(self.tokens[0]),
                variable=self.tokens[2],
            )
        # creates expression tokens
        if self.expression_type() == 2:
            self.token = Token(
                file=self.file,
                command=self.command,
                tokens=self.tokens,
                segment_pointer=None,
                command_type=self.get_command_type(self.tokens[0]),
                variable=None,
            )
        # creates branchin / label / function tokens
        if self.expression_type() == 3:            
            self.token = Token(
                file=self.file,
                command=self.command,
                tokens=self.tokens,
                segment_pointer=None,
                command_type=self.get_command_type(self.tokens[0]),
                variable=self.tokens[1],
            )
        # creates function tokens
        if self.expression_type() == 4:
            self.token = Token(
                file=self.file,
                command=self.command,
                tokens=self.tokens,
                segment_pointer=self.tokens[1] if len(self.tokens)>1 else None,
                command_type=self.get_command_type(self.tokens[0]),
                variable=self.tokens[2] if len(self.tokens)>2 else None,
            )

    '''
        Cleans code, by removing spaces and comments
        param: 
            code: str
        return:
            str -> cleaned string
    '''
    def clean_code(self):
        regex_return = re.findall(r'(.*(?=\/{2})|(?<=\/{2}).*|.*(?!\/{2}))',self.command)
        if len(regex_return) > 0:
            self.tokens = [item.strip() for item in regex_return]
        else:
            self.tokens = []
            
    '''
        0 - expressions like eq, lt, and so on
        1 - push / pop command
    '''
    def expression_type(self):
        # no command parsed
        if len(self.tokens) == 0 or self.tokens[0] == '':
            return 0
        # if push/pop
        if self.tokens[0] in ['push','pop']:
            return 1
        # if command is some expression
        if self.tokens[0] in ['add','sub','eq','gt','lt','neg','and','or','not']:
            return 2
        # if branching operation
        if self.tokens[0] in ['label','if-goto','goto']:
            return 3
        # if function related operations
        if self.tokens[0] in ['function','call','return','end']:
            return 4

    def tokenize(self):
        self.tokens = re.findall(r'(\S+)',self.tokens[0])

    def get_command_type(self, command: str) -> int:
        # only available commands, else error
        mapping = {            
            'pop':      0,
            'push':     1,            
            'add':      2,
            'sub':      3,
            'eq':       4,
            'gt':       5,
            'lt':       6,
            'neg':      7,
            'and':      8,
            'or':       9,
            'not':      10,
            'label':    11,
            'if-goto':  12,
            'goto':     13,
            'function': 14,
            'call':     15,
            'return':   16,
            'end':      17
        }
        return mapping[command]

    def get_memory_segment(self, segment: str):
        mapping = {
            'local':    'LCL',
            'constant': 'CONSTANT',
            'argument': 'ARG',
            'this':     'THIS',
            'that':     'THAT',
            'temp':     'TEMP',
            'static':   'STATIC',
            'pointer':  'POINTER'
        }

        return mapping[segment]