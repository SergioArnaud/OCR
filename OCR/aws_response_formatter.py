import pandas as pd


class ResponseFormatter:
    def __init__(self, Aws_ocr):
        self.Aws_ocr = Aws_ocr

        if self.Aws_ocr.analysis_response is not None:
            self.response = self.Aws_ocr.analysis_response
            self.response_type = "analysis"
        elif self.Aws_ocr.text_response is not None:
            self.response = self.Aws_ocr.text_response
            self.response_type = "text"
        else:
            raise Exception(
                """You have to execute `get_text` or `get_analysis` in the AWS_OCR 
                class before building a response formatter object"""
            )

        self.blocks = self.response["Blocks"]
        self.blocks_map = {block["Id"]: block for block in self.blocks}

        self.pages_text = []
        self.pages_response = []
        self.pages_tables = []

        self._get_per_page()
        self.num_pages = self.response["DocumentMetadata"]["Pages"]

        if self.response_type == "analysis":

            self.tables = [
                self._get_table(block)
                for block in self.blocks
                if block["BlockType"] == "TABLE"
            ]

            self.pages_tables = [[] for _ in range(self.num_pages)]
            for table in self.tables:
                self.pages_tables[table["page"] - 1].append(table["table"])

            self.num_tables = len(self.tables)

            # Falta añadir formas

    def _get_per_page(self):
        text, blocks = "", []

        first_iteration = True
        for block in self.blocks:
            if block["BlockType"] == "PAGE":
                if not first_iteration:
                    self.pages_text.append(text)
                    self.pages_response.append(blocks)
                    text = ""
                    blocks = []
            elif "Text" in block:
                text += block["Text"] + " "
                blocks.append(block)
            first_iteration = False
        self.pages_text.append(text)
        self.pages_response.append(blocks)

    def _get_blocks_per_page(self):
        text = []
        for block in self.blocks:
            if block["BlockType"] == "PAGE":
                if text != "":
                    self.pages_text.append(text)
                    text = ""
            elif "Text" in block:
                text += block["Text"] + " "

    def _get_table(self, table):
        dict_table = {}
        page = table["Page"] if 'Page' in table else 1
        for relationship in table["Relationships"]:
            if relationship["Type"] == "CHILD":
                for child_id in relationship["Ids"]:
                    cell = self.blocks_map[child_id]
                    if cell["BlockType"] == "CELL":
                        dict_table.setdefault(cell["RowIndex"], {})[
                            cell["ColumnIndex"]
                        ] = self._get_block_text(cell)
        return {"page": page, "table": dict_table}

    def _get_block_text(self, block):
        text = ""
        if "Relationships" in block:
            for relationship in block["Relationships"]:
                if relationship["Type"] == "CHILD":
                    for child_id in relationship["Ids"]:
                        word = self.blocks_map[child_id]
                        if word["BlockType"] == "WORD":
                            text += word["Text"] + " "
        return text

    def table_to_pandas(self, num_table):
        return pd.DataFrame.from_dict(self.tables[num_table], orient="index")

    def tables_to_xlsx(self, filename="tables_found.xlsx"):
        writer = pd.ExcelWriter(filename, engine="xlsxwriter")
        for k, table in enumerate(self.tables):
            df = self.table_to_pandas(k)
            df.to_excel(writer, sheet_name="Table_{}".format(str(k)))
        writer.save()
