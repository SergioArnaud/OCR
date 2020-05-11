from .ocr_document import Document


class Camelot(Document):
    def __init__(self, file_path):
        super().__init__(file_path)


# metrics
# Función que automáticamente decida stream o latice
# función que maximice métrica con búsqueda de grid (parámetros)
