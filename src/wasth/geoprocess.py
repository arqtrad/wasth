"""Processa entradas de georreferenciamento

Gera ID no formato Open Location Code a partir da latitude e longitude
inseridas na ficha ou na interface.
"""

import openlocationcode.openlocationcode as openlocationcode

class OpenLocation:
    def __init__(self, id: str | None, lat: int | float, lon: int | float) -> None:
        self.id = id
        self.lat = lat
        self.lon = lon

    def encode(self) -> str:
        code = openlocationcode.encode(self.lat, self.lon, 11)
        if self.id:
            if openlocationcode.isValid(self.id):
                if self.id == code:
                    return code
                else:
                    raise ValueError(f"Já existe um código '{self.id}' que difere do novo código '{code}'!")
        return code
