## OCR module

Usamos:

- [flake8](https://flake8.pycqa.org/en/latest/) como guía de estilo
- [black](https://black.readthedocs.io/en/stable/) como code formatter
- [gitflow](https://nvie.com/posts/a-successful-git-branching-model/) como branching model
- [numpy docstring standart](https://numpy.org/devdocs/docs/howto_document.html#id10) para documentar nuestras funciones y módulos (para ligarlo con sphinx y hacer la documentación automática)


## Usage

```python
from OCR.ocr import Ocr
Doc = Ocr(file_path, action, engine)
Doc.process_file()
```

Where:

| Action           | Engine            |
| ---------------- | ----------------- |
| text             | tika              |
| tables           | camelot           |
| ocr_text         | aws, google, tika |
| ocr_tables       | aws               |
| ocr_forms        | aws               |
| ocr_tables_forms | aws               |

Which one to choose?

| Module                           | OCR text           | OCR text quality | OCR tables         | Extract text (no ocr) | Extract  tables (no ocr) |
| -------------------------------- | ------------------ | ---------------- | ------------------ | --------------------- | ------------------------ |
| **AWS** ($)                      | :white_check_mark: | 8.5              | :white_check_mark: | ❌                     | ❌                        |
| **Google** ($)                   | :white_check_mark: | 9.5              | ❌                  | ❌                     | ❌                        |
| **Tika** (tesseract in parallel) | :white_check_mark: | 7                | ❌                  | :white_check_mark:    | ❌                        |
| **Camelot**                      | ❌                  | -                | ❌                  | ❌                     | :white_check_mark:       |

```
Doc.process_file()
```

outputs

Tweeks

necesito un requirements.txt	

#### AWS textract

###### Libraries



###### Keys

To use this module you need to configure the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) and set your `aws_keys`there 



#### Google cloud vision API

###### Instalation

```
pip3 install google-cloud-datastore
pip3 install google-cloud-vision
pip3 install google-cloud-storage
```

###### Credentials

You need to put your ```google_credentials.json```file in the keys folder

#### Apache tika

[Apache tika](https://tika.apache.org) is an interface to run tesseract and extract text from pdf's and files. 

> Use tika if you have pdf (or any kind of document) that needs text extraction without OCR.
>
> If you need to do OCR you can do it with tika (you can process .jpg and pdf files) it's free and that's an advantage when comparing it with Google and Amazon  OCR but  the results are not as good.

To install the python client run

```
pip3 install tika
```

You will also need [tesseract](https://github.com/tesseract-ocr/tesseract), [java 8 command line client](https://www.oracle.com/technetwork/java/javase/overview/java8-2100321.html) and [popper](https://poppler.freedesktop.org) to run apache tika. In mac you can install all 3 using brew as follows

```
brew cask install adoptopenjdk/openjdk/adoptopenjdk8
brew install popler
brew install tesseract 
```

####Camelot

MAC

```
brew install tcl-tk ghostscript
pip install camelot-py[cv]
```

Linux

```
apt install python-tk ghostscript
pip install camelot-py[cv]
```













