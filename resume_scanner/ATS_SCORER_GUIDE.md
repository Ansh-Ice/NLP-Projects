# ATS Score Checker - Implementation Guide

## Overview

The ATS Score Checker module is an advanced scoring system that evaluates how well a resume matches a given Job Description (JD). It provides a comprehensive score (0-100) along with detailed breakdowns and actionable improvement suggestions.

## Architecture

### File Structure
```
resume_scanner/
├── app.py                  # Main Streamlit application (updated)
├── ats_scorer.py           # ATS scoring module (NEW)
├── Resume Screening.ipynb  # Jupyter notebook with training code
├── UpdatedResumeDataSet.csv # Training dataset
├── clf.pkl                 # Trained classifier model
├── tfidf.pkl              # TF-IDF vectorizer
└── label_encoder.pkl      # Label encoder for categories
```

## Scoring System Details

The ATS score is calculated as a weighted combination of 5 components:

### 1. **Keyword Matching (40% weight)**

**Purpose:** Measure how many important keywords from the JD appear in the resume.

**Algorithm:**
- Extract up to 40 important keywords from JD using frequency analysis
- Count how many JD keywords appear in the resume
- Score = (matched keywords / total JD keywords) × 40

**Output:**
- Matched keywords count
- Missing keywords (actionable list for improvements)
- Match percentage

**Example:**
- JD keywords: [python, machine learning, sql, data analysis, ...]
- Resume contains: [python, sql, data analysis, ...]
- Match rate: 75% → Score: 30/40

---

### 2. **Resume Section Detection (20% weight)**

**Purpose:** Verify presence of essential resume sections that ATS systems look for.

**Sections Detected:**
- Summary / Objective
- Skills
- Experience
- Education
- Projects

**Algorithm:**
- Each section contributes 4 points (20 ÷ 5 = 4)
- Pattern matching detects section headers
- Score = number of detected sections × 4

**Output:**
- Detection status for each section
- Count of detected sections
- Recommendations for missing sections

**Example:**
- Detected 4/5 sections → Score: 16/20
- Missing: Projects section

---

### 3. **Formatting Heuristics (10% weight)**

**Purpose:** Evaluate resume formatting quality and readability.

**Scoring Rules:**

| Criterion | Penalty/Bonus | Rules |
|-----------|---------------|-------|
| Word Count | -3 pts | < 100 words OR > 2000 words |
| Special Chars | -2 pts | > 15% of total characters |
| Bullet Points | +2 pts | ≥ 5 bullet points found |
| **Base Score** | **10 pts** | Starting score |

**Algorithm:**
- Start with 10 points
- Apply penalties for poor word count
- Apply penalties for excessive special characters
- Award bonus for good use of bullet points
- Clamp final score between 0-10

**Output:**
- Word count analysis
- Special character ratio
- Bullet point count
- Penalties and bonuses applied

**Example:**
- Base: 10
- 500 words: OK (0 pts)
- 8 bullet points: +2 pts
- 5% special chars: OK (0 pts)
- **Final: 12 → clamped to 10**

---

### 4. **Action Verbs & Impact Language (10% weight)**

**Purpose:** Measure use of strong, action-oriented language.

**Strong Action Verbs Tracked (48 total):**

Built, developed, created, designed, engineered, architected, optimized, improved, enhanced, accelerated, automated, streamlined, led, managed, coordinated, orchestrated, directed, supervised, achieved, accomplished, delivered, executed, implemented, launched, spearheaded, pioneered, transformed, revolutionized, innovated, analyzed, identified, discovered, resolved, solved, troubleshot, increased, decreased, reduced, maximized, minimized, scaled, integrated, consolidated, merged, combined, unified, aligned, awarded, recognized, certified, promoted, selected, chosen

**Algorithm:**
- Count occurrences of strong action verbs
- Scoring scale:
  - 0-5 verbs: (count / 5) × 6 points
  - 5+ verbs: 6 + (count - 5) / 10 points (bonus for excellence)
  - Max: 10 points

**Output:**
- Action verb count
- Specific verbs found
- Benchmark recommendation

**Example:**
- Found 8 action verbs: 6 + (8-5)/10 = 6.3/10

---

### 5. **Semantic Similarity (10% weight)**

**Purpose:** Measure overall conceptual match between resume and JD.

**Algorithm:**
- Create TF-IDF vectors for both texts
- Use n-grams (1-2 words) for better context
- Calculate cosine similarity between vectors
- Scale similarity (0-1) to score (0-10)

**Fallback:** If TF-IDF fails, use simple word overlap:
- Similarity = (common words) / (total JD words)

**Output:**
- Similarity score (0-1 or percentage)
- Method used (TF-IDF or fallback)
- Semantic overlap interpretation

**Example:**
- Cosine similarity: 0.75 → Score: 7.5/10
- Interpretation: "75% semantic overlap"

---

## Final Score Calculation

```
Final Score = Keyword(40) + Sections(20) + Formatting(10) + ActionVerbs(10) + Semantic(10)
            = 0-100 (clamped)
```

**Score Interpretation:**
- **80-100:** Excellent match - highly optimized for this role
- **60-79:** Good match - has room for improvement
- **40-59:** Fair match - significant gaps to address
- **0-39:** Poor match - needs substantial revision

---

## Improvement Suggestions Engine

The system generates context-aware suggestions based on component scores:

### Keyword Matching (< 20/40)
"Add missing keywords: [list of 10 missing keywords]. These terms are in the JD but not in your resume."

### Resume Sections (< 20/20)
"Add missing sections: [list]. These are crucial for ATS parsing."

### Formatting Issues (< 10/10)
- Low word count: "Expand your resume content. Current: X words. Target: 150-400 words per section."
- High word count: "Reduce resume length to improve readability."
- Special characters: "Remove excessive special characters for better ATS parsing."

### Action Verbs (< 6/10)
"Use stronger action verbs. Current count: X. Example verbs: developed, optimized, architected, led, accelerated."

### Semantic Similarity (< 5/10)
"Low semantic match with JD. Try to incorporate more role-specific terminology and technical context from the job description."

### General Feedback
"⭐ Overall ATS Score: X/100. Focus on the areas above to improve match with this job description."

---

## Integration with Streamlit App

### UI Features

1. **Navigation Sidebar**
   - Select between "Resume Classifier" and "ATS Score Checker" modes

2. **Resume Classifier Mode** (Original functionality)
   - Upload resume
   - Display predicted job category

3. **ATS Score Checker Mode** (New)
   - **Left Column:** Upload resume
   - **Right Column:** Paste job description
   - **Calculate Button:** Trigger ATS analysis
   - **Results Display:**
     - Final ATS score with color coding (🟢🟡🔴)
     - Score breakdown by component (5 metrics)
     - Expandable sections for detailed analysis:
       - Keyword Matching Analysis
       - Resume Sections Analysis
       - Formatting Analysis
       - Action Verbs & Impact Language
       - Semantic Similarity Analysis
     - Improvement suggestions
     - Download report button

### Color Coding
- 🟢 **Green (80-100):** Excellent match
- 🟡 **Yellow (60-79):** Good match
- 🔴 **Red (0-59):** Needs improvement

---

## Code Structure

### Key Functions in `ats_scorer.py`

#### Utility Functions
```python
preprocess_text(text: str) -> str
```
Clean and normalize text for analysis.

```python
extract_keywords(text: str, min_length: int, max_keywords: int) -> List[str]
```
Extract important keywords using frequency analysis.

```python
tokenize_sentences(text: str) -> List[str]
```
Split text into sentences.

#### Scoring Functions
```python
score_keyword_matching(resume_text, jd_text) -> Tuple[float, Dict]
```
Calculate keyword matching score (0-40).

```python
score_resume_sections(resume_text) -> Tuple[float, Dict]
```
Detect and score resume sections (0-20).

```python
score_formatting_heuristics(resume_text) -> Tuple[float, Dict]
```
Evaluate formatting quality (0-10).

```python
score_action_verbs(resume_text) -> Tuple[float, Dict]
```
Count strong action verbs (0-10).

```python
score_semantic_similarity(resume_text, jd_text) -> Tuple[float, Dict]
```
Calculate semantic match using TF-IDF (0-10).

#### Main Scoring Engine
```python
calculate_ats_score(resume_text: str, jd_text: str) -> Dict
```
Main entry point - calculates complete ATS score with all components.

#### Improvement Suggestions
```python
generate_improvement_suggestions(ats_result: Dict, threshold: float) -> List[str]
```
Generate actionable improvement suggestions.

---

## Usage Examples

### Example 1: Python Developer Resume

**Resume Snippet:**
```
EXPERIENCE
• Developed real-time data pipeline using Python and Apache Kafka
• Optimized database queries, reducing query time by 40%
• Led team of 3 engineers in building microservices architecture

SKILLS
Python, SQL, Docker, AWS, Machine Learning, TensorFlow, Pandas
```

**Job Description:**
```
We're looking for a Python Developer with experience in data engineering.
Required: Python, SQL, data pipeline development, cloud platforms (AWS/GCP)
Nice to have: Docker, Kubernetes, machine learning experience
```

**Expected Score Breakdown:**
- Keyword Matching: 35/40 (87% match)
- Resume Sections: 20/20 (all detected)
- Formatting: 10/10 (good structure)
- Action Verbs: 9/10 (developed, optimized, led)
- Semantic: 8/10 (high overlap)
- **Final: 82/100 ✅ Excellent**

---

### Example 2: Weak Match Resume

**Resume:**
```
SUMMARY
I am a professional with experience in various roles.

SKILLS
Working knowledge of many technologies

EXPERIENCE
Worked on several projects
```

**Job Description:**
```
Java Developer needed. Must have:
- Java 8+, Spring Boot, Microservices
- Database design, REST APIs
- Agile methodology experience
```

**Expected Score Breakdown:**
- Keyword Matching: 5/40 (no Java, Spring Boot, Microservices)
- Resume Sections: 15/20 (missing Projects section)
- Formatting: 6/10 (too vague, low word count)
- Action Verbs: 2/10 (weak language)
- Semantic: 2/10 (minimal overlap)
- **Final: 30/100 🔴 Needs Major Revision**

---

## Performance Considerations

### Time Complexity
- Keyword extraction: O(n) where n = text length
- TF-IDF similarity: O(n*m) where n,m = vector dimensions
- Overall: Linear to quadratic depending on text size

### Memory Usage
- Text preprocessing: Minimal
- TF-IDF vectorization: O(vocabulary size)
- Result storage: ~1-5 KB per analysis

### Optimization Tips
- Typical analysis time: < 2 seconds for average resumes
- Caching not implemented but can be added for JD reuse
- Scalable for batch analysis if needed

---

## Customization Guide

### Adjusting Scoring Weights
Edit the final score calculation in `calculate_ats_score()`:
```python
final_score = (
    keyword_score * 0.40 +      # Adjust weights here
    section_score * 0.20 +
    formatting_score * 0.10 +
    action_verb_score * 0.10 +
    semantic_score * 0.10
)
```

### Adding More Action Verbs
Edit `STRONG_ACTION_VERBS` set in `ats_scorer.py`:
```python
STRONG_ACTION_VERBS = {
    'built', 'developed', 'created', ...,
    'your_new_verb', 'another_verb'
}
```

### Modifying Resume Sections
Edit `RESUME_SECTIONS` dictionary:
```python
RESUME_SECTIONS = {
    'section_name': r'your_regex_pattern',
    ...
}
```

### Adjusting Thresholds
In any scoring function, modify the thresholds:
```python
# Example: Change word count threshold
if word_count < 150:  # Changed from 100
    score -= penalty
```

---

## Requirements

### Python Packages
```
streamlit>=1.0.0
scikit-learn>=0.24.0
nltk>=3.6
PyPDF2>=1.26.0        # For PDF extraction (optional)
python-docx>=0.8.10   # For DOCX extraction (optional)
numpy>=1.20.0
```

### Installation
```bash
pip install -r requirements.txt
```

---

## Running the Application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Testing

### Test Case 1: High Score
1. Upload a well-formatted Python developer resume
2. Paste a Python developer job description
3. Expected: Score > 75

### Test Case 2: Low Score
1. Upload a vague healthcare resume
2. Paste a software engineer job description
3. Expected: Score < 50

### Test Case 3: Missing Keywords
1. Upload resume without key technical skills
2. Paste JD with specific tech stack
3. Expected: Keyword matching score low, suggestions shown

---

## Limitations & Future Improvements

### Current Limitations
1. Requires well-formatted text input
2. Action verb detection case-insensitive only
3. No support for skills ontologies or taxonomies
4. Semantic similarity depends on vocabulary overlap

### Future Enhancements
1. **Spell-check & grammar analysis**
   - Add 5-10% weight to grammar/spell accuracy
   
2. **Industry-specific keyword database**
   - Expand from generic keywords to domain-specific terms
   
3. **Experience level matching**
   - Detect years of experience and match to JD requirements
   
4. **Salary/role alignment**
   - Extract salary ranges and role levels
   
5. **Real ATS system simulation**
   - Test with actual ATS tools (LinkedIn Recruiter, Taleo, etc.)
   
6. **Machine learning ranking**
   - Train a model to predict ATS compatibility
   
7. **Multi-language support**
   - Process resumes in multiple languages
   
8. **Visual resume analysis**
   - Analyze resume design and layout formatting

---

## Troubleshooting

### Issue: ImportError for ats_scorer
**Solution:** Ensure `ats_scorer.py` is in the same directory as `app.py`

### Issue: PDF text extraction fails
**Solution:** Install required libraries:
```bash
pip install PyPDF2 python-docx
```

### Issue: Streamlit cache errors
**Solution:** Clear Streamlit cache:
```bash
streamlit cache clear
```

### Issue: Low semantic similarity scores
**Solution:** 
- Check if JD and resume are in same language
- Ensure resume mentions domain-specific technologies
- Verify TF-IDF vectorizer vocabulary is adequate

---

## Support & Contact

For issues, feature requests, or improvements, please refer to the main project documentation.

---

**Last Updated:** December 2024
**Version:** 1.0
**Status:** Production Ready
