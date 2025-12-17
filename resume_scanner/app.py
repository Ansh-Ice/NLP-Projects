import streamlit as st
import pickle
import re
import nltk
import string
import io
from ats_scorer import calculate_ats_score, generate_improvement_suggestions

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
    st.set_page_config(page_title="Resume Scanner & ATS Checker", layout="wide")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio("Select Mode", ["Resume Classifier", "ATS Score Checker"])
    
    st.title("Resume Scanner")
    
    if MISSING_EXTRACTOR_LIBS:
        st.info(f"To improve PDF/DOCX text extraction install: pip install {' '.join(MISSING_EXTRACTOR_LIBS)}")
    
    if app_mode == "Resume Classifier":
        resume_classifier_mode()
    else:
        ats_checker_mode()


def resume_classifier_mode():
    """Original resume classification functionality."""
    st.header("Resume Classifier")
    st.write("Upload a resume to classify it into a job category.")
    
    uploaded_file = st.file_uploader("Upload your Resume", type=["pdf", "docx", "doc"])
    
    if uploaded_file is not None:
        # read bytes once and extract text depending on file type
        resume_bytes = uploaded_file.read()
        resume_text = extract_text_from_bytes(resume_bytes, uploaded_file.name)

        # If we couldn't extract meaningful text from PDF/DOCX, warn the user
        if uploaded_file.name.lower().endswith((".pdf", ".docx")) and (not resume_text or len(resume_text.strip()) < 20):
            st.warning("Could not reliably extract text from this file. Install `PyPDF2` and `python-docx`, or provide a plain text/Word resume.")

        cleaned_resume = cleanResume(resume_text)
        cleaned_resume_tfidf = tfidf.transform([cleaned_resume])
        prediction = clf.predict(cleaned_resume_tfidf)[0]
        category_name = map_id_to_category(prediction)
        
        # Display results
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Predicted Job Role", category_name)
        with col2:
            st.metric("Category ID", prediction)
        
        with st.expander("View Extracted Resume Text"):
            st.text_area("Resume Text", value=resume_text, height=200, disabled=True)


def ats_checker_mode():
    """ATS Score Checker functionality."""
    st.header("ATS Score Checker")
    st.write(
        "Evaluate how well your resume matches a job description. "
        "Upload your resume and paste the job description to get an ATS score with improvement suggestions."
    )
    
    # Create two columns for inputs
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Resume Upload")
        uploaded_file = st.file_uploader("Upload your Resume", type=["pdf", "docx", "doc"], key="ats_resume")
        resume_text = None
        
        if uploaded_file is not None:
            resume_bytes = uploaded_file.read()
            resume_text = extract_text_from_bytes(resume_bytes, uploaded_file.name)
            
            if uploaded_file.name.lower().endswith((".pdf", ".docx")) and (not resume_text or len(resume_text.strip()) < 20):
                st.warning("Could not extract text reliably. Try again or use plain text.")
            else:
                st.success(f"✅ Resume loaded ({len(resume_text.split())} words)")
                with st.expander("View Resume Text"):
                    st.text_area("Resume", value=resume_text, height=150, disabled=True, key="resume_preview")
    
    with col2:
        st.subheader("📋 Job Description")
        jd_text = st.text_area(
            "Paste the job description here",
            height=250,
            placeholder="Paste job description text here...",
            key="jd_input"
        )
        if jd_text:
            st.info(f"Job Description: {len(jd_text.split())} words")
    
    # Calculate ATS Score
    if st.button("🚀 Calculate ATS Score", use_container_width=True):
        if not resume_text or not resume_text.strip():
            st.error("❌ Please upload a resume first.")
        elif not jd_text or not jd_text.strip():
            st.error("❌ Please paste a job description first.")
        else:
            with st.spinner("Analyzing resume against job description..."):
                # Calculate ATS score
                ats_result = calculate_ats_score(resume_text, jd_text)
                
                # Display final score with color coding
                st.markdown("---")
                st.subheader("📊 ATS Score Results")
                
                final_score = ats_result['final_score']
                
                # Color coding
                if final_score >= 80:
                    score_color = "🟢"
                    score_feedback = "Excellent Match!"
                elif final_score >= 60:
                    score_color = "🟡"
                    score_feedback = "Good Match"
                else:
                    score_color = "🔴"
                    score_feedback = "Needs Improvement"
                
                # Display main score
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Final ATS Score", f"{final_score}/100", delta=score_feedback)
                with col2:
                    st.metric("Score Status", score_color, label_visibility="collapsed")
                
                # Display component scores
                st.markdown("### Score Breakdown by Component")
                components = ats_result['components']
                
                score_cols = st.columns(5)
                with score_cols[0]:
                    st.metric(
                        "Keyword Matching",
                        f"{components['keyword_matching']['score']}/40",
                        help=f"Matched: {components['keyword_matching']['details']['matched_count']}/{components['keyword_matching']['details']['total_jd_keywords']}"
                    )
                with score_cols[1]:
                    st.metric(
                        "Resume Sections",
                        f"{components['resume_sections']['score']}/20",
                        help=f"Detected: {components['resume_sections']['details']['detected_count']}/5"
                    )
                with score_cols[2]:
                    st.metric(
                        "Formatting",
                        f"{components['formatting_heuristics']['score']}/10",
                        help=f"Words: {components['formatting_heuristics']['details']['word_count']}"
                    )
                with score_cols[3]:
                    st.metric(
                        "Action Verbs",
                        f"{components['action_verbs']['score']}/10",
                        help=f"Count: {components['action_verbs']['details']['action_verb_count']}"
                    )
                with score_cols[4]:
                    st.metric(
                        "Semantic Match",
                        f"{components['semantic_similarity']['score']}/10",
                        help=f"{components['semantic_similarity']['details']['interpretation']}"
                    )
                
                # Detailed Analysis
                st.markdown("### Detailed Analysis")
                
                # Keyword Matching Details
                with st.expander("🔍 Keyword Matching Analysis"):
                    keyword_details = components['keyword_matching']['details']
                    st.write(f"**Match Percentage:** {keyword_details['match_percentage']}%")
                    st.write(f"**Matched Keywords:** {keyword_details['matched_count']}/{keyword_details['total_jd_keywords']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if keyword_details['matched_keywords']:
                            st.write("**✅ Keywords Found:**")
                            st.write(", ".join(keyword_details['matched_keywords'][:15]))
                    
                    with col2:
                        if keyword_details['missing_keywords']:
                            st.warning("**❌ Missing Keywords:**")
                            st.write(", ".join(keyword_details['missing_keywords'][:15]))
                
                # Resume Sections Details
                with st.expander("📑 Resume Sections Analysis"):
                    section_details = components['resume_sections']['details']
                    for section, found in section_details['sections_detected'].items():
                        status = "✅" if found else "❌"
                        st.write(f"{status} {section.title()}")
                
                # Formatting Details
                with st.expander("🔧 Formatting Analysis"):
                    format_details = components['formatting_heuristics']['details']
                    st.write(f"**Word Count:** {format_details['word_count']}")
                    st.write(f"**Special Character Ratio:** {format_details['special_char_ratio']:.2%}")
                    st.write(f"**Bullet Points:** {format_details['bullet_point_count']}")
                    
                    if format_details['penalties']:
                        st.warning("**Penalties Applied:**")
                        for penalty in format_details['penalties']:
                            st.write(f"- {penalty}")
                    
                    if format_details['bonuses']:
                        st.success("**Bonuses Applied:**")
                        for bonus in format_details['bonuses']:
                            st.write(f"- {bonus}")
                
                # Action Verbs Details
                with st.expander("💪 Action Verbs & Impact Language"):
                    action_details = components['action_verbs']['details']
                    st.write(f"**Action Verb Count:** {action_details['action_verb_count']}")
                    st.write(f"**Benchmark:** {action_details['benchmark']}")
                    if action_details['verbs_found']:
                        st.write(f"**Verbs Found:** {', '.join(set(action_details['verbs_found']))}")
                
                # Semantic Similarity Details
                with st.expander("🎯 Semantic Similarity Analysis"):
                    semantic_details = components['semantic_similarity']['details']
                    st.write(f"**Similarity Score:** {semantic_details['similarity_score']:.1%}")
                    st.write(f"**Method:** {semantic_details['method']}")
                    st.write(f"**Interpretation:** {semantic_details['interpretation']}")
                
                # Improvement Suggestions
                st.markdown("---")
                st.subheader("💡 Improvement Suggestions")
                suggestions = generate_improvement_suggestions(ats_result)
                for suggestion in suggestions:
                    st.info(suggestion)
                
                # Download Report
                st.markdown("---")
                report_text = generate_ats_report(ats_result, resume_text, jd_text)
                st.download_button(
                    label="📥 Download ATS Report (Text)",
                    data=report_text,
                    file_name="ats_score_report.txt",
                    mime="text/plain"
                )


def generate_ats_report(ats_result: dict, resume_text: str, jd_text: str) -> str:
    """Generate a text report of the ATS score analysis."""
    report = []
    report.append("=" * 80)
    report.append("ATS SCORE REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Final Score
    report.append(f"FINAL ATS SCORE: {ats_result['final_score']}/100")
    report.append("")
    
    # Component Breakdown
    report.append("-" * 80)
    report.append("SCORE BREAKDOWN BY COMPONENT")
    report.append("-" * 80)
    
    components = ats_result['components']
    for component_name, component_data in components.items():
        report.append(f"\n{component_name.upper().replace('_', ' ')}")
        report.append(f"  Score: {component_data['score']}/{component_data['weight']}")
        report.append(f"  Details:")
        
        for key, value in component_data['details'].items():
            if isinstance(value, list) and len(value) > 0:
                report.append(f"    - {key}: {', '.join(str(v) for v in value[:10])}")
            elif isinstance(value, dict):
                report.append(f"    - {key}:")
                for k, v in value.items():
                    report.append(f"        {k}: {v}")
            else:
                report.append(f"    - {key}: {value}")
    
    # Improvement Suggestions
    report.append("\n" + "-" * 80)
    report.append("IMPROVEMENT SUGGESTIONS")
    report.append("-" * 80)
    
    suggestions = generate_improvement_suggestions(ats_result)
    for i, suggestion in enumerate(suggestions, 1):
        report.append(f"{i}. {suggestion}")
    
    report.append("\n" + "=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    return "\n".join(report)

    
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