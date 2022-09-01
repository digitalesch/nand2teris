from dataclasses import dataclass

'''
Will only need to mantain two symbol tables:
1 - Class variables
2 - Subroutine variables, being the first always "this - className - argument - class - 0" as the specified CompilerToken definition
'''

@dataclass
class CompilerToken():
    name:   str
    type:   str
    kind:   str
    scope:  str
    number: int