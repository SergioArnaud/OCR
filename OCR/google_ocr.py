"""Modulito."""

# Google
from google.cloud import vision, storage
from google.cloud.vision import types
from google.protobuf import json_format

# Utils
import os
import io
import math

# Credentials
from .ocr_document import Document

CREDENTIALS_LOC = (
    os.path.dirname(os.path.abspath(__file__)) + "/keys/google_credentials.json"
)
admitted_extensions = ["pdf", "jpg", "jpeg", "png"]


class GoogleOcr(Document):
    """Help to execute google vision tasks.
    
    Returns
    -------
    [type]
        [description]
    
    Raises
    ------
    TypeError
        [description]
    """

    def __init__(self, file_path):
        """Initialize GoogleVision Class.
        
        Parameters
        ----------
        file_path : str
            path to file
        """
        super().__init__(file_path)
        self._validate_extension()

        # Loads credentials and instanciates client
        self.vision_client = vision.ImageAnnotatorClient.from_service_account_json(
            CREDENTIALS_LOC
        )
        self.storage_client = storage.Client.from_service_account_json(CREDENTIALS_LOC)

        # Google buckets and paths
        self.bucket_name = "hercules_demos"
        self.blob_path = "temp_folder/"
        self.blob_filename = "temporary.pdf"
        self.blob_name = self.blob_path + self.blob_filename

        self.pages_text = None
        self.text = None
        self.pages_response = None

    def _validate_extension(self):
        if self.extension not in admitted_extensions:
            raise TypeError("File extension {} isn't supported".format(self.extension))

    def _upload_to_bucket(self):
        """Upload data to a bucket.
        
        Returns
        -------
        str
            GCP path for the pdf file uploaded
        """
        bucket = self.storage_client.get_bucket(self.bucket_name)
        blob = bucket.blob(self.blob_name)
        blob.upload_from_filename(self.file_path)

        print(blob.public_url)
        # returns a public url
        return blob.public_url

    def pipeline_extraction(self):
        if self.extension == "pdf":
            self._clear_folder()
            self._OCR_pdf()
            self._clear_folder()
        else:
            self._OCR_image()

    def _clear_folder(self):
        bucket = self.storage_client.get_bucket(self.bucket_name)
        blobs = bucket.list_blobs(prefix=self.blob_path)
        for blob in blobs:
            blob.delete()

    def _OCR_pdf(self, batch_size=2, mime_type="application/pdf"):
        """OCR with PDF/TIFF from local file. Return a list with the text of each page.
        
        Parameters
        ----------
        batch_size : int, optional
            Number of pdf pages in each batch, by default 2
        mime_type : str, optional
            Supported mime_types are 'application/pdf' and  'image/tiff', by default "application/pdf"
        Notes
        -----
        It overrides the parameter `ocr_response` of the class adding 
        the response of google's api
        """

        def wait_for_blob_list():
            finished = False
            while not finished:
                finished = True
                bucket = self.storage_client.get_bucket(self.bucket_name)
                blob_list = list(
                    bucket.list_blobs(prefix=self.blob_path + "proccessed")
                )
                if len(blob_list) < math.ceil(self.num_pages / batch_size):
                    finished = False
            return blob_list

        if self.num_pages == 1:
            batch_size = 1

        # Upload to google storage
        self._upload_to_bucket()
        bucket = self.storage_client.get_bucket(self.bucket_name)
        blob_list = list(bucket.list_blobs(prefix=self.blob_path))

        # Origin
        gcs_source_uri = "gs://" + self.bucket_name + "/" + self.blob_name
        print("Origin:", gcs_source_uri + "-" + self.blob_filename)

        # Destination
        gcs_destination_uri = (
            "gs://" + self.bucket_name + "/" + self.blob_path + "proccessed"
        )
        print("Destination:", gcs_destination_uri + "-" + self.blob_filename)

        # Setting Vision tool #
        # ------------------- #

        feature = vision.types.Feature(
            type=vision.enums.Feature.Type.DOCUMENT_TEXT_DETECTION
        )

        gcs_source = vision.types.GcsSource(uri=gcs_source_uri)
        input_config = vision.types.InputConfig(
            gcs_source=gcs_source, mime_type=mime_type
        )

        gcs_destination = vision.types.GcsDestination(uri=gcs_destination_uri)
        output_config = vision.types.OutputConfig(
            gcs_destination=gcs_destination, batch_size=batch_size
        )

        # Google thing  #
        # ------------- #

        async_request = vision.types.AsyncAnnotateFileRequest(
            features=[feature], input_config=input_config, output_config=output_config
        )
        self.vision_client.async_batch_annotate_files(requests=[async_request])

        blob_list = wait_for_blob_list()

        # Building response #
        # ----------------- #

        self.pages_text = []
        self.pages_response = []
        # Iterate over batches
        for index, blob in enumerate(blob_list):
            print(index, "/", len(blob_list))

            # Process one batch.
            json_string = blob.download_as_string()
            response = json_format.Parse(
                json_string, vision.types.AnnotateFileResponse()
            )

            # Iterate over pages in batch
            for page in response.responses:

                # Response por p page in batch b.
                self.pages_response.append(page)
                self.pages_text.append(page.full_text_annotation.text)

        self.text = " ".join(self.pages_text)

    def _OCR_image(self):
        """Detect document features (text blocks) in an image.
        
        Notes
        -----
        It overrides the parameters `text_response`and `text` adding
        the response of google's api to the first one and a string with all the
        text to the second one
        """
        self._validate_image(self._OCR_image)

        # Loads the image into memory
        with io.open(self.file_path, "rb") as image_file:
            content = image_file.read()
        image = types.Image(content=content)

        # Performs text detection on the image file
        response = self.vision_client.text_detection(image=image)
        self.pages_response = [response]

        self.text_response = response.text_annotations
        texts_list = [text.description for text in self.text_response]

        self.text = "\n".join(texts_list)
        self.pages_text = [self.text]
        self.num_pages = 1

    def _validate_image(self, function):
        """Validate if current file is an image (appropiate to use in image functions).
        
        Parameters
        ----------
        function : func
            functuon trying to use the file
        Raises
        ------
        TypeError  
            if the file isn't an image
        """
        if self.extension not in ["jpg", "jpeg", "png"]:
            raise TypeError(
                "File has to be an image to use the '{}' function".format(
                    function.__name__
                )
            )

    def label_image(self):
        """Use Google's vision API to detect objects in an image.
        
        Notes
        -----
        It overrides the parameters `labels_response`and `labels`adding
        the response of google's api to the first one and a list with the label
        and scores to the second one
        """

        def label_to_dict(label):
            """Convert an ImageAnnotation (google object) to dict.
            
            Arguments:
                label {Google.label} -- Label
            
            Returns:
                dict -- Dictionary with description and score
            """
            d = {}
            d["description"] = label.description
            d["score"] = label.score
            return d

        self._validate_image(self.label_image)

        # Loads the image into memory
        with io.open(self.file_path, "rb") as image_file:
            content = image_file.read()
        image = types.Image(content=content)

        # Performs label detection on the image file
        response = self.vision_client.label_detection(image=image)

        self.labels_response = response.label_annotations
        self.labels = [label_to_dict(label) for label in self.labels_response]
