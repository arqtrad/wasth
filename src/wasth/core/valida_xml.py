"""
Módulo de validação do XML: roda em importação e exportação de dados

Verifica se a tradução de/para XML é válida e conforme à especificação LIDO e
ao perfil de aplicação a obras de arquitetura.
"""

import os
from pathlib import Path
import xmlschema
from rich import print
from wasth.core import models

def create_schema(
    schema_path: str = "data/xml/lido-v1.1-profile-architecture-v1.1.xsd"
) -> xmlschema.XMLSchema11 | None :
    """Mostra problemas de estrutura dos dados"""
    root_dir = Path(__file__).resolve().parent.parent
    abs_path = os.path.join(root_dir, schema_path)
    if not os.path.isfile(abs_path):
        # Usamos XMLSchema11 em vez de XMLSchema por causa deste problema de
        # validação do OpenGML:
        # https://github.com/sissaschool/xmlschema/issues/425
        xml_profile = xmlschema.XMLSchema11(
"https://lido-schema.org/profiles/v1.1/lido-v1.1-profile-architecture-v1.1.xsd"
        )
        xml_profile.export(target=os.path.dirname(abs_path), save_remote=True)
        return xml_profile
    xml_profile = xmlschema.XMLSchema11(abs_path)
    return xml_profile
    # type: <class 'xmlschema.validators.schemas.XMLSchema11'>

def valid_xml(
        doc_path: str | None = None,
        xml_profile: xmlschema.validators.schemas.XMLSchema11 = create_schema()
) -> bool | None:
    """Valida um arquivo XML contra especificação XSD"""
    if not doc_path or not Path(doc_path).is_file():
        doc_path = input("Informar um caminho de arquivo/ficheiro.")
        if not doc_path or not Path(doc_path).is_file():
            print(f":x:  {doc_path} não é um caminho válido, cancelando.")
            return None
    xml_profile = create_schema()
    if xml_profile.is_valid(doc_path):
        print(f":white_check_mark: O documento '{doc_path}' é válido.")
    else:
        xml_profile.validate(doc_path)
    return xml_profile.is_valid(doc_path)

def main(
    args: models.InOutPaths | None = None,
    ignore_output_dir: bool = True
) -> None:
    args = models.paths(overwrite=ignore_output_dir)
    if not args:
        return None
    files = args['filelist']
    for f in files:
        try:
            valid_xml(f)
        except Exception as e:
            print(f"""
-------------------------------------------------------------------------------
:prohibited: Não foi possível ler {f}: {e}
            """)

if __name__ == "__main__":
    raise SystemExit(main())
