from ast import arg
from .binary_encoder import BinaryEncoder
import argparse

def main():
    parser = argparse.ArgumentParser()

    arguments_list = [
        {'name':'file_name','type':str,'help':'specifies the file to be read'}
    ]

    for arg in arguments_list:
        parser.add_argument(
            arg['name'],type=arg['type'],help=arg['help']
        )

    args = parser.parse_args()

    encoded_tokens = []
    binary_encoder = BinaryEncoder()
    
    with open(f'{args.file_name}','r') as input_fp:
        code_lines = [line.strip() for line in input_fp.readlines()]

    for line in code_lines:
        token = binary_encoder.tokenize(line)
        if token.type is not None:
            encoded_tokens.append(token)

    binary_encoder.symbol_table.generate_variable_symbols()

    encoded_tokens = [token for token in binary_encoder.encode_variables(encoded_tokens) if token.type not in [-1,2]]       # second pass for variables

    with open(f"{args.file_name.split('.')[0]}.log",'w') as output_fp:
        output_fp.write(f"TOKENS\n")
        for token in encoded_tokens:
            output_fp.write(f"{token}\n")

        output_fp.write(f"VARIABLES\n")
        for key,value in binary_encoder.symbol_table.symbols.items():
            output_fp.write(f"{key} -> {value}\n")

    with open(f"{args.file_name.split('.')[0]}.hack",'w') as output_fp:
        for token in encoded_tokens:
            output_fp.write(f"{token.binary}\n")

    print(binary_encoder.symbol_table.symbols)

if __name__=='__main__':
    main()