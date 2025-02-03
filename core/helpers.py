import PyPDF2


def extract_text_from_pdf(file_path):
    """
    Extract text from uploaded PDFs
    """
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
