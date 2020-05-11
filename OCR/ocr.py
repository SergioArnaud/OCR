from .aws_ocr import AwsOcr
from .tika_ocr import TikaOcr
from .google_ocr import GoogleOcr

actions = {
    "google": ["ocr_text"],
    "aws": ["ocr_text", "ocr_tables", "ocr_forms", "ocr_tables_forms"],
    "tika": ["ocr_text", "text"],
    "camelot": ["tables"],
}


class Ocr:
    def __init__(self, file_path, action, engine):

        self.file_path = file_path
        self.actions = actions

        self.engine = engine
        self._validate_engine()

        self.action = action
        self._validate_engine_action()

        if self.engine == "aws":
            print(
                """Set aws bucket, folder and region using the set functions
                if not default values (bucket = "ocr-deep-dive", region="us-east-1" 
                and no folder) will be used to stored the file in s3')"""
            )

            self.aws_bucket = "ocr-deep-dive"
            self.aws_folder = None
            self.aws_region = "us-east-1"

    def _validate_engine_action(self):
        if self.action not in self.actions[self.engine]:
            raise Exception(
                f""" Given action {self.action} can't be used with  
                    {self.engine} engine, the options you have are 
                    {str(self.actions[self.engine])} """
            )

    def _validate_engine(self):
        if self.engine not in self.actions.keys():
            raise Exception(
                f""" Given engine {self.engine} is not an opcion, use one from 
                {str(self.actions.keys())} """
            )

    def set_aws_folder(self, folder):
        self.aws_folder = folder

    def set_aws_bucket(self, bucket):
        self.aws_bucket = bucket

    def set_aws_region(self, region):
        self.aws_region = region

    def process_file(self):
        def _add_atributes(list_attributes):
            for attribute in list_attributes:
                val = (
                    getattr(self.Engine, attribute)
                    if attribute in dir(self.Engine)
                    else None
                )
                setattr(self, attribute, val)

        if self.engine == "aws":
            Engine = AwsOcr(
                self.file_path,
                self.action,
                self.aws_bucket,
                self.aws_folder,
                self.aws_region,
            )
        if self.engine == "tika":
            ocr = True if "ocr" in self.action else False
            Engine = TikaOcr(self.file_path, ocr)
        if self.engine == "google":
            Engine = GoogleOcr(self.file_path)

        Engine.pipeline_extraction()
        self.Engine = Engine

        list_attributes = [
            "pages_text",
            "text",
            "pages_response",
            "num_pages",
            "pages_tables",
            "forms",
            "blocks",
        ]

        _add_atributes(list_attributes)

        #self.pages_text = Engine.pages_text
        #self.text = Engine.text
        #self.pages_response = Engine.pages_response
        #self.num_pages = Engine.num_pages
        #self.pages_tables = (
        #    Engine.pages_tables if "pages_tables" in dir(Engine) else None
        #)
        #self.forms = Engine.forms if "forms" in dir(Engine) else None

