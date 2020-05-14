
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

        # Get all response blocks
        if 'Blocks' not in self.response:
            print(self.response)
            raise 
        self.blocks = self.response["Blocks"]

        # Get blocks mapping
        self.blocks_map = {block["Id"]: block for block in self.blocks}

        # Get key mapping (for forms)
        self.key_map = {
            block["Id"]: block
            for block in self.blocks
            if block["BlockType"] == "KEY_VALUE_SET" and "KEY" in block["EntityTypes"]
        }
        # Get value mapping (for forms)
        self.value_map = {
            block["Id"]: block
            for block in self.blocks
            if block["BlockType"] == "KEY_VALUE_SET"
            and "KEY" not in block["EntityTypes"]
        }

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
            self._get_kv_relationship()

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

    def _get_block_text(self, block):
        text = ""
        if "Relationships" in block:
            for relationship in block["Relationships"]:
                if relationship["Type"] == "CHILD":
                    for child_id in relationship["Ids"]:
                        word = self.blocks_map[child_id]
                        if word["BlockType"] == "WORD":
                            text += word["Text"] + " "
                        if word["BlockType"] == "SELECTION_ELEMENT":
                            if word["SelectionStatus"] == "SELECTED":
                                text += "X "
        return text

    def _get_table(self, table):
        dict_table = {}
        page = table["Page"] if "Page" in table else 1
        for relationship in table["Relationships"]:
            if relationship["Type"] == "CHILD":
                for child_id in relationship["Ids"]:
                    cell = self.blocks_map[child_id]
                    if cell["BlockType"] == "CELL":
                        dict_table.setdefault(cell["RowIndex"], {})[
                            cell["ColumnIndex"]
                        ] = self._get_block_text(cell)
        return {"page": page, "table": dict_table}

    def _get_kv_relationship(self):
        def _find_value_block(key_block, value_map):
            for relationship in key_block["Relationships"]:
                if relationship["Type"] == "VALUE":
                    for value_id in relationship["Ids"]:
                        value_block = value_map[value_id]
            return value_block

        self.forms = {}
        for block_id, key_block in self.key_map.items():
            value_block = _find_value_block(key_block, self.value_map)
            key = self._get_block_text(key_block)
            val = self._get_block_text(value_block)
            self.forms[key] = val
