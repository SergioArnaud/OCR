"""Module with the AWS OCR tools to perform text, table and form extraction,

>>> doc_a = AwsOcr(file_path, 'ocr_tables')
>>> doc_a.pipeline_extraction()
>>> doc_a.pages_tables[1]
"""

# Standart python libraries
import json
import copy
import sys
import time

# 3rd party libraries
import boto3
import pandas as pd

# Own
from .aws_response_formatter import ResponseFormatter
from .ocr_document import Document

admitted_extensions = ["pdf", "jpg", "jpeg", "png"]


class AwsOcr(Document):
    """Class with AWS OCR functions to extract text, tables and forms from documents in s3.

    Once you've given the action ("ocr_text", "ocr_tables", "forms", "tables-forms")
    yoy can call the pipeline_extraction() function that will perform the exection.

    Finally: the variables pages_text, text, pages_response and pages_tables contain
    all the output information you may need.

    You can use pdf, jpg, jpeg and png file extensions in both functions.

    Parameters
    ----------
    Document : Object 
        super class with the basic atributes to handle a document

    Attributes
    ----------
    file_path : str
        local path to the file that will be processed 
    action : str
        action to perform ("ocr_text", "ocr_tables", "ocr_forms", "tables-forms")
    bucket_name : str
        bucket in s3 in which files will be stored
    folder : str
        folder inside s3 bucket in which the file will be stored
    region : str
        aws region of the bucket (verify that textract is available in that region)
    filename : str
        name of the file to be processed
    s3 : boto3.resource
        s3 resource
    textract : boto3.client
        textract client
    sqs : boto3.client
        sqs client
    text_response : dict
        after using `get_text` function, the result goes to this atribute
    analysis_response : dict
        after using `get_analysis` function, the result goes to this atribute
    pages_text : list
        list with the text of the page i at the ith position
    text : str
        full text of the document
    pages_response: list
        list with the full aws response of the page i at the ith position
    num_pages: int
        number of pages of the document
    pages_tables: list
        ist with the tables of the page i at the ith position

    Raises
    ------
    Exception
        [description]
    TypeError
        If your file extension isn't supporter. Supported files are pdf and images.
    """

    def __init__(
        self,
        file_path,
        action,
        bucket_name="ocr-deep-dive",
        folder=None,
        region="us-east-1",
    ):
        """Initialize the AWSOCR class.
        
        Parameters
        ----------
        file_path : str
            local path to the file that will be processed 
        action : str
            action to perform ("ocr_text", "ocr_tables", "forms", "tables-forms")
        bucket_name : str
            bucket in s3 in which files will be stored by default "ocr-deep-dive"
        folder : str
            folder inside s3 bucket in which the file will be stored by default None
        region : str
            aws region of the bucket (verify that textract is available in that region 
            and your bucket is in the same region)by default "us-east-1"
        
        Raises
        ------
        TypeError
            If your file extension isn't supporter. Supported files are pdf and images.
        """
        super().__init__(file_path)
        self._validate_extension()

        self.action = action
        self._validate_action()

        self.bucket = bucket_name
        self.region = region
        self.document = {"S3Object": {"Bucket": self.bucket, "Name": self.filename}}

        self.s3 = self._get_resource_aws("s3")
        self.textract = self._get_client_aws("textract")
        self.sqs = self._get_client_aws("sqs")

        if folder is not None:
            self.filename = folder + "/" + self.filename

        self.text_response = None
        self.analysis_response = None

        self._upload_to_s3()

    def _validate_action(self):
        if self.action not in ["ocr_text", "ocr_tables", "ocr_forms", "ocr_tables_forms"]:
            raise Exception(
                f"""Action {self.action} isn't supported, use one from 
                {str(["text", "tables", "forms", "tables-forms"])}"""
            )

    def _validate_extension(self):
        if self.extension not in admitted_extensions:
            raise TypeError("File extension {} isn't supported".format(self.extension))

    def _get_client_aws(self, service):
        return boto3.client(service, region_name=self.region)

    def _get_resource_aws(self, service):
        return boto3.resource(service, region_name=self.region)

    def _upload_to_s3(self):
        return self.s3.Object(self.bucket, self.filename).put(
            Body=open(self.file_path, "rb"), ACL="public-read"
        )

    def pipeline_extraction(self):
        """Main function to perform the extraction
        """
        self._process_ocr()
        self._process_response()

    def _process_ocr(self):
        if self.action == "text":
            self._ocr_text()
        else:
            FeatureTypes = ["TABLES", "FORMS"]
            if self.action == "ocr_tables":
                FeatureTypes = ["TABLES"]
            if self.action == "orc_forms":
                FeatureTypes = ["FORMS"]
            self._ocr_analysis(FeatureTypes)

    def _process_response(self):
        """Uses the ResponseFormatter to format the response to a nice common format.
        """
        Formatter = ResponseFormatter(self)

        self.pages_text = Formatter.pages_text
        self.text = " ".join(self.pages_text)
        self.pages_response = Formatter.pages_response
        self.num_pages = Formatter.num_pages
        self.pages_tables = Formatter.pages_tables
        self.forms = Formatter.forms

    def _ocr_text(self):
        """Return the text from the current file.

        Notes
        -----
        It overrides the parameter `self.text_response` of the class adding 
        the response of aws api
        """
        if self.extension == "pdf":
            response = self.textract.start_document_text_detection(
                DocumentLocation=self.document,
                NotificationChannel={
                    "SNSTopicArn": "arn:aws:sns:us-east-1:401913772240:AmazonTextractTopic",
                    "RoleArn": "arn:aws:iam::401913772240:role/Textract_test_role",
                },
            )

            print("Start Job Id: " + response["JobId"])
            self.text_response = self._get_job_textract(
                response, self.textract.get_document_text_detection
            )

        if self.extension in ["jpg", "jpeg", "png"]:
            self.text_response = self.textract.detect_document_text(
                Document=self.document
            )

    def _ocr_analysis(self, FeatureTypes=["TABLES", "FORMS"]):
        """Return the analysis (text, tables and forms).
        
        Parameters
        ----------
        FeatureTypes : list, optional
            You can query only for tables or forms, by default ["TABLES", "FORMS"]
        """
        if self.extension == "pdf":
            response = self.textract.start_document_analysis(
                DocumentLocation=self.document,
                FeatureTypes=FeatureTypes,
                NotificationChannel={
                    "SNSTopicArn": "arn:aws:sns:us-east-1:401913772240:AmazonTextractTopic",
                    "RoleArn": "arn:aws:iam::401913772240:role/Textract_test_role",
                },
            )

            print("Start Job Id: " + response["JobId"])
            self.analysis_response = self._get_job_textract(
                response, self.textract.get_document_analysis
            )

        if self.extension in ["jpg", "jpeg", "png"]:
            self.analysis_response = self.textract.analyze_document(
                Document=self.document, FeatureTypes=FeatureTypes
            )

    def _get_job_textract(self, response, get_function):
        """Process a pdf ocr job in aws.
        
        A job to do OCR is sent in the `get_analysis`  and in the `get_text` functions 
        when the processing is finished a message is published in a queue 
        (we use amazon SQS simple queue service to receive  the response). 
        This function waits until the job is finished and returns it.
        
        Parameters
        ----------
        response : dict
            textract start_document response
        get_function : function
            depending on the case, `textract.get_document_analysis` if we are doing 
            analysis of `get_document_text_detection` if we're only getting the text.   
        
        Returns
        -------
        dict
            response of the job
        """

        def wait(dot_line):

            if dot_line % 20 == 0:
                print()
            for _ in range(5):
                print(".", end="")
                sys.stdout.flush()
                time.sleep(0.5)
            return dot_line + 5

        def build_response(response):
            aux = get_function(JobId=response["JobId"])
            ans = copy.deepcopy(aux)
            while "NextToken" in aux:
                aux = get_function(JobId=response["JobId"], NextToken=aux["NextToken"])
                ans["Blocks"].extend(aux["Blocks"])
            return ans

        url_queue = "https://sqs.us-east-1.amazonaws.com/401913772240/Textract_queue"
        dot_line = 0
        jobFound = False

        while jobFound is False:
            sqsResponse = self.sqs.receive_message(
                QueueUrl=url_queue,
                MessageAttributeNames=["ALL"],
                MaxNumberOfMessages=10,
            )

            if sqsResponse:
                if "Messages" not in sqsResponse:
                    dot_line = wait(dot_line)
                    continue

                for message in sqsResponse["Messages"]:

                    notification = json.loads(message["Body"])
                    if "Message" not in notification:
                        continue
                    textMessage = json.loads(notification["Message"])

                    if str(textMessage["JobId"]) == response["JobId"]:
                        ans = build_response(response)
                        self.sqs.delete_message(
                            QueueUrl=url_queue, ReceiptHandle=message["ReceiptHandle"]
                        )
                        jobFound = True

        return ans

    def table_to_pandas(self, num_table):
        return pd.DataFrame.from_dict(self.tables[num_table], orient="index")

    def tables_to_xlsx(self, filename="tables_found.xlsx"):
        writer = pd.ExcelWriter(filename, engine="xlsxwriter")
        for k, table in enumerate(self.tables):
            df = self.table_to_pandas(k)
            df.to_excel(writer, sheet_name="Table_{}".format(str(k)))
        writer.save()
