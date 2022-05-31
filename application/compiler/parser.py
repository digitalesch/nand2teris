from dataclasses import dataclass

from yaml import parse
from syntax_tokenizer import SyntaxTokenizer, MismatchedValueError
import xml.etree.ElementTree as ET
import argparse, os, sys

@dataclass
class Parser():
    file_path:  str

    '''
        Desc:
            Parses tokens into XML structure using xml.etree.ElementTree
        Params:
            code:
                type: string
                desc: code in string format to be parsed
        Return:
            XML tree containing tokens that were parsed
    '''
    def parse_tokens(self,code):
        xml = ET.Element('tokens')

        lex_tokenizer = SyntaxTokenizer(code)

        for token in lex_tokenizer.tokenize():            
            if token.type == 'mismatch':
                raise MismatchedValueError(f'Erro de token não especifica "{token.value}", verificar o código')
            if token.type not in ['skip','comments']:
                _tmp = ET.SubElement(xml,token.type)
                _tmp.text = token.value

        return xml

    '''
        Desc:
            Writes parsed tokens to file
        Params:
            xml:
                type: xml.etree.ElementTree
                desc: structure that contains the XML format hierarchy
        Return:
            None, saves the structure to file, with < token_type > token_value </ token_type > format
    '''
    def write_tags(self, xml: ET, file_name: str):
        translate = {
            "<": '&lt;',
            ">": '&gt;', 
            "'": '&quot;',
            "&": '&amp;'
        }

        all_descendants = ['<tokens>']+[f'<{child.tag}> {translate[child.text] if child.text in translate else child.text} </{child.tag}>' for child in list(xml.iter()) if child.text is not None]+['</tokens>']
        with open(f'{self.file_path}/{file_name}Tokens.xml','w') as fp:
            fp.write('\n'.join(all_descendants)+'\n')
        print(f'Saved content to {self.file_path}/{file_name}Tokens.xml')

    '''
        Desc:
            Parses ".jack" files into tokens, and writes output to file
        Params:            
        Return:
            None, saves the parsed tokens from file code into "< file_name >Tokens.xml"
    '''
    def parse_files(self) -> None:
        for file in os.listdir(self.file_path):            
            if file.endswith(".jack"):
                file_name = file.split('.')[0]
                with open(f'{self.file_path}/{file}','r') as input_fp:                    
                    code_lines = ''.join(input_fp.readlines())
                print(''.join(code_lines))
                xml = self.parse_tokens(code_lines)
                self.write_tags(xml=xml,file_name=file_name)

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
    parsed_tokens = Parser(file_path=os.path.join(os.getcwd(),args.file_path))
    parsed_tokens.parse_files()

if __name__ == '__main__':
    main()