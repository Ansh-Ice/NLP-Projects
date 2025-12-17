import streamlit as st
import pickle
import re
import nltk
import string
import io

# from sklearn.feature_extraction.text import TfidfVectorizer
# tfidf = TfidfVectorizer(stop_words='english')


nltk.download('punkt')
nltk.download('stopwords')

# Check for optional extraction libraries; show tips if missing
MISSING_EXTRACTOR_LIBS = []
try:
    import PyPDF2  # noqa: F401
except Exception:
    MISSING_EXTRACTOR_LIBS.append('PyPDF2')
try:
    import docx  # noqa: F401
except Exception:
    MISSING_EXTRACTOR_LIBS.append('python-docx')

# loading models
clf = pickle.load(open('clf.pkl', 'rb'))
tfidf = pickle.load(open('tfidf.pkl', 'rb'))

# Mapping of category IDs to human-readable names (legacy/fallback)
CATEGORY_NAMES = [
    'Data Science', 'HR', 'Advocate', 'Arts', 'Web Designing',
    'Mechanical Engineer', 'Sales', 'Health and fitness', 'Civil Engineer',
    'Java Developer', 'Business Analyst', 'SAP Developer', 'Automation Testing',
    'Electrical Engineering', 'Operations Manager', 'Python Developer',
    'DevOps Engineer', 'Network Security Engineer', 'PMO', 'Database', 'Hadoop',
    'ETL Developer', 'DotNet Developer', 'Blockchain', 'Testing'
]

CATEGORY_IDS = [6, 12, 0, 1, 24, 16, 22, 14, 5, 15, 4, 21, 2, 11, 18, 20, 8, 17, 19, 7, 13, 10, 9, 3, 23]

# Build a mapping from id -> name (legacy fallback)
ID_TO_CATEGORY = {cid: name for name, cid in zip(CATEGORY_NAMES, CATEGORY_IDS)}

# Try to load LabelEncoder created at training time to correctly map
# model numeric predictions back to original category names.
try:
    le = pickle.load(open('label_encoder.pkl', 'rb'))
except Exception:
    le = None


def map_id_to_category(cid):
    """Return a human-readable category name for a numeric id or label index.

    Prefer using the saved LabelEncoder if available (most reliable). If the
    encoder is not present, fall back to the legacy ID_TO_CATEGORY mapping.
    """
    try:
        cid_int = int(cid)
        if le is not None:
            try:
                return le.inverse_transform([cid_int])[0]
            except Exception:
                pass
        return ID_TO_CATEGORY.get(cid_int, 'Unknown')
    except Exception:
        return 'Unknown'


# Helper to extract text from uploaded files (PDF / DOCX / fallback)
def extract_text_from_bytes(file_bytes, filename='file'):
    ext = filename.split('.')[-1].lower() if filename and '.' in filename else ''

    # PDF
    if ext == 'pdf':
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            text = ''
            for page in reader.pages:
                # extract_text may return None for some pages
                text += page.extract_text() or ''
            if text.strip():
                return text
        except Exception:
            pass

    # DOCX
    if ext == 'docx':
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            return '\n'.join([p.text for p in doc.paragraphs])
        except Exception:
            pass

    # Fallback: try decoding bytes directly
    try:
        return file_bytes.decode('utf-8', errors='ignore')
    except Exception:
        return file_bytes.decode('latin-1', errors='ignore')


def cleanResume(txt):
    
    cleanTxt = re.sub(r'http\S+', ' ', txt)
    cleanTxt = re.sub(r'@\S+', '', cleanTxt)
    cleanTxt = re.sub(r'#\S+', '', cleanTxt)
    cleanTxt = re.sub(r'RT||cc', '', cleanTxt)
    # cleanTxt = re.sub(r'[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), '', cleanTxt)
    cleanTxt = re.sub(rf"[{re.escape(string.punctuation)}]", "", cleanTxt)
    cleanTxt = re.sub(r'[^\x00-\x7f]', '', cleanTxt)
    cleanTxt = re.sub(r'\s+', ' ', cleanTxt)
    
    return cleanTxt

#webapp
def main():
    st.title("Resume Scanner")
    if MISSING_EXTRACTOR_LIBS:
        st.info(f"To improve PDF/DOCX text extraction install: pip install {' '.join(MISSING_EXTRACTOR_LIBS)}")
    uploaded_file = st.file_uploader("Upload your Resume", type=["pdf", "docx", "doc"])
    
    if uploaded_file is not None:
        # read bytes once and extract text depending on file type
        resume_bytes = uploaded_file.read()
        resume_text = extract_text_from_bytes(resume_bytes, uploaded_file.name)

        # If we couldn't extract meaningful text from PDF/DOCX, warn the user
        if uploaded_file.name.lower().endswith((".pdf", ".docx")) and (not resume_text or len(resume_text.strip()) < 20):
            st.warning("Could not reliably extract text from this file. Install `PyPDF2` and `python-docx`, or provide a plain text/Word resume.")

        cleaned_resume = cleanResume(resume_text)
        cleaned_resume = tfidf.transform([cleaned_resume])
        prediction = clf.predict(cleaned_resume)[0]
        category_name = map_id_to_category(prediction)
        
        # show name and id for easier debugging
        st.write(f"Predicted Job Role: {category_name} (id: {prediction})")
    
# python main
if __name__ == '__main__':
    main()
    
    
# ['Data Science' 'HR' 'Advocate' 'Arts' 'Web Designing'
#  'Mechanical Engineer' 'Sales' 'Health and fitness' 'Civil Engineer'
#  'Java Developer' 'Business Analyst' 'SAP Developer' 'Automation Testing'
#  'Electrical Engineering' 'Operations Manager' 'Python Developer'
#  'DevOps Engineer' 'Network Security Engineer' 'PMO' 'Database' 'Hadoop'
#  'ETL Developer' 'DotNet Developer' 'Blockchain' 'Testing']

# [ 6 12  0  1 24 16 22 14  5 15  4 21  2 11 18 20  8 17 19  7 13 10  9  3
#  23]