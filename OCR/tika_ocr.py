from tika import parser
import os
import shutil
from multiprocessing import Pool
import regex as re
from .ocr_document import Document


class TikaOcr(Document):
    """Class to permorm text extraction that uses apache tika interface for textract.

    Parameters
    ----------
    Document : [type]
        [description]
    """    
    def __init__(self, file_path, ocr=False):
        super().__init__(file_path)
        self.ocr = ocr
        if ocr is True and self.extension == "pdf":
            self.img_folder = self.folder + self.filename.split(".")[0]
            if not os.path.exists(self.img_folder):
                os.mkdir(self.img_folder)
            self.num_pages = self._pdf_to_jpg()

    def pipeline_extraction(self):
        if self.ocr is True and self.extension == "pdf":
            self._process_ocr()
        else:
            self.num_pages, folder = self.split_pdf_in_pages()
            self.pages_text = []
            for filename in sorted(os.listdir(folder)):
                self.pages_text.append(self._tika_parse(folder + filename))
            self.text = '\n \n'.join(self.pages_text)
            shutil.rmtree(folder)

    def _process_ocr_parallel(self):
        paths = [
            (self.img_folder + "/" + str(k) + ".jpg",) for k in range(self.num_pages)
        ]
        with Pool() as p:
            self.pages_text = p.starmap(self._tika_parse, paths)
        self.text = "\n".join(self.pages_text)

    def _process_ocr(self):

        paths = [self.img_folder + "/" + str(k) + ".jpg" for k in range(self.num_pages)]
        self.text_per_page = []
        for path in paths:
            self.pages_text.append(self._tika_parse(path))
        self.text = "\n".join(self.text_per_page)

    def _tika_parse(self, file_path):
        content = parser.from_file(file_path)
        if "content" in content:
            text = content["content"]
        else:
            return ""
        # Convert to string
        text = re.sub(r"\t", " ", str(text))
        return re.sub(r"\n\s*\n", "\n", str(text))
