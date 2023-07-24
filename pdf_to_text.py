import PyPDF2
import requests
import io

def download_pdf(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        else:
            return None
    except Exception as e:
        print("Error while downloading PDF:", str(e))
        return None

def convert_pdf_to_text(pdf_content):
    try:
        if pdf_content is None:
            return None

        pdf_file = io.BytesIO(pdf_content)
        pdfreader = PyPDF2.PdfReader(pdf_file)
        num_pages = len(pdfreader.pages)
        text = ""

        for page_num in range(num_pages):
            pageobj = pdfreader.pages[page_num]
            text += pageobj.extract_text()

        return text

    except Exception as e:
        print("Error while converting PDF to text:", str(e))
        return None
    
# Usage example:
pdf_url = 'https://www.takumi-duesseldorf.de/wp-content/uploads/2022/04/Takumi-Düsseldorf-Menu.pdf'
pdf_content = download_pdf(pdf_url)

if pdf_content is not None:
    extracted_text = convert_pdf_to_text(pdf_content)
    if extracted_text is not None:
        with open('output.txt', 'a', encoding='utf-8') as txt_file:
            txt_file.write(extracted_text)
        print("PDF content successfully extracted and saved to output.txt.")
    else:
        print("Error occurred during PDF text extraction.")
else:
    print("Failed to download the PDF file.")
