# implemented libs
from tokenizer import tokenizer, stack

# std-libs
import argparse
import os


def main():
    arguments_list = [
        {'name':'file_path','type':str,'help':'specifies the file / directory to be read'}        
    ]

    parser = argparse.ArgumentParser()

    for arg in arguments_list:
        parser.add_argument(
            arg['name'],type=arg['type'],help=arg['help']
        )

    args = parser.parse_args()

    path = os.path.split(args.file_path)    
    code_lines = []

    stack_operation = stack.Stack(
        file_name   = os.path.splitext(path[-1])[0] if not os.path.isdir(args.file_path) else path[1],                      # file_path for STATIC segment
        SP          = stack.Pointer(0,256),             # SP
        LCL         = stack.Pointer(1,300),             # LCL
        ARG         = stack.Pointer(2,400),             # ARG
        THIS        = stack.Pointer(3,3000),            # THIS
        THAT        = stack.Pointer(4,3010),            # THAT
        TEMP        = stack.Pointer(5,5),               # TEMP
        POINTER     = stack.Pointer(3,3)                # POINTER
    )

    code_lines = []

    #print(path,os.path.isdir(args.file_path),os.path.splitext(path[-1]))
    if not os.path.isdir(args.file_path):
        with open(f'{args.file_path}','r') as input_fp:
            code_lines = [line.strip() for line in input_fp.readlines()]
        file_output = os.path.splitext(path[-1])[0]
        output_path = f'{path[0]}/{file_output}.asm'
        generated_code = []
    else:
        for file in os.listdir(args.file_path):            
            if file.endswith(".vm"):
                print(f"AAA: {file},{file.split('.')[0]}")
                file_name = file.split('.')[0]
                with open(f'{args.file_path}/{file}','r') as input_fp:                    
                    code_lines += [(file_name,line.strip()) for line in input_fp.readlines()]
        file_output = path[1]
        path = os.path.splitext(path[-1])
        output_path = f'{args.file_path}/{path[0]}.asm'
        # generates bootstrap code, if folder is passed
        generated_code = stack_operation.create_bootstrap_statment()
        generated_code += stack_operation.create_call_statement(stack.Token(file="Sys.init",command='call Sys.init 0', tokens=['call', 'Sys.init', '0'], segment_pointer='Sys.init', command_type=15, variable='0'))

    print(code_lines)

    tokens = []
    for code in code_lines:        
        tmp_token = tokenizer.Tokenizer(file=code[0],command=code[1])
        # if some token is found, not being comment or empty spaces
        if tmp_token.token is not None:
            tokens.append(tmp_token)
    
    for token in tokens:
        generated_operation = stack_operation.generate_operation(token.token)
        generated_code += generated_operation
        print(f'{token.token}\n{generated_operation}')
    
    #print(generated_code)

    with open(f"{output_path}",'w') as output_fp:
        output_fp.write('\n'.join(generated_code))
    
if __name__ == '__main__':
    main()