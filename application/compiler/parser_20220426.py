from dataclasses import dataclass
from syntax_tokenizer import SyntaxTokenizer, MismatchedValueError
import xml.etree.ElementTree as ET
import argparse, os, sys

@dataclass
class Parser():
    file_path:  str
    file_name:  str
    xml:        ET = None

    def __post_init__(self):
        self.xml = ET.Element('tokens')

    def parse_tokens(self,code):
        lex_tokenizer = SyntaxTokenizer(code)

        for token in lex_tokenizer.tokenize():            
            if token.type == 'mismatch':
                raise MismatchedValueError(f'Erro de token não especifica "{token.value}", verificar o código')
            if token.type not in ['skip','comments']:
                _tmp = ET.SubElement(self.xml,token.type)
                _tmp.text = token.value

    def write_tags(self):
        translate = {
            "<": '&lt;',
            ">": '&gt;', 
            "'": '&quot;',
            "&": '&amp;'
        }

        all_descendants = ['<tokens>']+[f'<{child.tag}> {translate[child.text] if child.text in translate else child.text} </{child.tag}>' for child in list(self.xml.iter()) if child.text is not None]+['</tokens>']
        with open(f'{self.file_path}/{self.file_name}OutText.xml','w') as fp:
            fp.write('\n'.join(all_descendants)+'\n')
        print(f'Saved content to {self.file_path}/{self.file_name}OutText.xml')

    def write_xml(self):
        with open(f'{self.file_path}/{self.file_name}Out.xml','wb') as fp:
            fp.write(ET.tostring(self.xml, encoding='us-ascii', method='xml'))

    def parse_files(self, path: str) -> None:
        for file in os.listdir(path):            
            if file.endswith(".jack"):
                file_name = file.split('.')[0]
                with open(f'{path}/{file}','r') as input_fp:                    
                    code_lines = ''.join(input_fp.readlines())
                print(''.join(code_lines))
                #parsed_tokens = Parser(file_path=os.path.join(os.getcwd(),path),file_name=file_name)
                self.parse_tokens(code_lines)
                self.write_tags()


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

    print(repr(sys.argv[0]),os.path.join(os.getcwd(),args.file_path))

    for file in os.listdir(args.file_path):            
        if file.endswith(".jack"):
            file_name = file.split('.')[0]
            with open(f'{args.file_path}/{file}','r') as input_fp:                    
                code_lines = input_fp.readlines()
                print(''.join(code_lines))
                parsed_tokens = Parser(file_path=os.path.join(os.getcwd(),args.file_path),file_name=file_name)
                parsed_tokens.parse_tokens(''.join(code_lines))
                parsed_tokens.write_tags()

if __name__ == '__main__':
    main()