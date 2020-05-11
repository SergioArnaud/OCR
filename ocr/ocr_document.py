import subprocess
from pdf2image import convert_from_path
from PyPDF2 import PdfFileWriter, PdfFileReader
from pathlib import Path


class Document:
    def __init__(self, file_path):
        self.file_path = file_path
        self.filename = file_path.split("/")[-1]
        self.folder = "/".join(file_path.split("/")[:-1]) + "/"
        self.extension = file_path.split(".")[-1]
        self.name = self.filename.replace(f'.{self.extension}','')

        self.num_pages = self._get_num_pages()
        self.pages_text = None
        self.text = None
        self.pages_response = None
        self.pages_tables = None

    def open_file(self):
        """Open current file."""
        subprocess.call(["open", self.file_path])

    def _pdf_to_jpg(self, folder="img/"):
        pages = convert_from_path(self.file_path, 500)
        for k, page in enumerate(pages):
            page.save(self.img_folder + "/" + str(k) + ".jpg")
        return len(pages)

    def _get_num_pages(self):
        if self.extension == '.pdf':
            return PdfFileReader(open(self.file_path, "rb")).numPages
        else:
            return 1

    def split_pdf_in_pages(self):
        def add_ceros(num, total):
            return '0'*(len(total) - len(num)) + num
        
        folder = f'{self.name}/'

        Path(folder).mkdir(parents=True, exist_ok=True)
        inputpdf = PdfFileReader(open(self.file_path, "rb"))
        for page in range(inputpdf.numPages):
            output = PdfFileWriter()
            output.addPage(inputpdf.getPage(page))

            num_page = add_ceros(str(page), str(inputpdf.numPages))
            with open(f'{folder}{num_page}.pdf', "wb") as outputStream:
                output.write(outputStream)

        return inputpdf.numPages, folder