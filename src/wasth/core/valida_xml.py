"""
Módulo de validação do XML: roda em importação e exportação de dados

Verifica se a tradução de/para XML é válida e conforme à especificação LIDO e
ao perfil de aplicação a obras de arquitetura.
"""

import os
import xmlschema
from rich import print
from wasth.core import models

def create_schema(
        schema_path="src/wasth/data/lido-v1.1-profile-architecture-v1.1.xsd"
):
    """Mostra problemas de estrutura dos dados"""
    schema_path = "src/wasth/data/lido-v1.1-profile-architecture-v1.1.xsd"
    if not os.path.isfile(schema_path):
        # Usamos XMLSchema11 em vez de XMLSchema por causa deste problema de
        # validação do OpenGML:
        # https://github.com/sissaschool/xmlschema/issues/425
        xml_profile = xmlschema.XMLSchema11(
"https://lido-schema.org/profiles/v1.1/lido-v1.1-profile-architecture-v1.1.xsd"
        )
        xml_profile.export(target='src/wasth/data', save_remote=True)
    xml_profile = xmlschema.XMLSchema11(schema_path)
    return xml_profile
    # type: <class 'xmlschema.validators.schemas.XMLSchema11'>

def valid_xml(doc_path) -> int | None:
    """Valida um arquivo XML contra especificação XSD"""
    if os.path.isfile(doc_path):
        xml_profile = create_schema()
        if xml_profile.is_valid(doc_path):
            print(f":white_check_mark: O documento '{doc_path}' é válido.")
            return 0
        xml_profile.validate(doc_path)
        return 1
    print("Documento não encontrado.")
    return None

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
