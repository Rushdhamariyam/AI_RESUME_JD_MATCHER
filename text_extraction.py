import PyPDF2
import re

def extract_text_from_pdf(file_source):
    """
    Extracts raw text from a PDF file.

    Parameters:
    - file_source: A file path string OR a file-like object (e.g., BytesIO from Streamlit).

    Returns:
    - Extracted plain text string.
    """
    text = ""
    try:
        # Check if the input is a file path (string) or a file-like object (from Streamlit)
        if isinstance(file_source, str):
            with open(file_source, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        else:
            # Read from file-like object
            reader = PyPDF2.PdfReader(file_source)
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error during PDF text extraction: {e}")
    return text

def clean_text(text):
    """
    Performs preprocessing/cleaning on the raw text:
    - Converts text to lowercase.
    - Removes URLs and Email patterns.
    - Normalizes whitespace (tabs, newlines, multiple spaces).
    - Removes special symbols while carefully retaining characters commonly used in
      technical skills (e.g., C++, C#, .NET, TCP/IP).
    """
    if not text:
        return ""

    # 1. Convert to lowercase
    text = text.lower()

    # 2. Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)

    # 3. Remove Email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', ' ', text)

    # 4. Replace tabs and newlines with space
    text = re.sub(r'\s+', ' ', text)

    # 5. Remove unwanted special characters, but retain chars needed for skills like C++, C#, .NET, TCP/IP
    # We keep alphanumeric characters, whitespace, plus (+), sharp/hash (#), dots (.), and hyphens (-)
    text = re.sub(r'[^a-zA-Z0-9\s+#\.-]', ' ', text)

    # 6. Normalize multiple spaces to a single space
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def preprocess_text_spacy(text, nlp):
    """
    Tokenizes text, filters out English stopwords and punctuation,
    and returns a list of lemmatized words/tokens.

    Parameters:
    - text: Cleaned string.
    - nlp: A loaded spaCy model (e.g., spacy.load("en_core_web_sm")).

    Returns:
    - List of lemmatized, lowercase tokens.
    """
    if not text:
        return []

    doc = nlp(text)

    # Filter out stopwords and punctuation, then lemmatize and clean spacing
    cleaned_tokens = [
        token.lemma_.strip() for token in doc
        if not token.is_stop and not token.is_punct and token.text.strip()
    ]

    return cleaned_tokens
