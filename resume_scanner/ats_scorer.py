"""
ATS Score Checker Module

This module implements a comprehensive ATS (Applicant Tracking System) scoring system
that evaluates how well a resume matches a given Job Description (JD).

Scoring Components:
1. Keyword Matching (40%): Extracts keywords from JD and matches them in resume
2. Resume Section Detection (20%): Detects presence of important resume sections
3. Formatting Heuristics (10%): Evaluates formatting quality and word count
4. Action Verbs & Impact Language (10%): Counts strong action verbs
5. Semantic Similarity (10%): Computes similarity between resume and JD

Author: ATS Scoring System
"""

import re
import string
from collections import Counter
from typing import Dict, List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ==================== CONSTANTS ====================

# Strong action verbs that indicate impactful experience
STRONG_ACTION_VERBS = {
    'built', 'developed', 'created', 'designed', 'engineered', 'architected',
    'optimized', 'improved', 'enhanced', 'accelerated', 'automated', 'streamlined',
    'led', 'managed', 'coordinated', 'orchestrated', 'directed', 'supervised',
    'achieved', 'accomplished', 'delivered', 'executed', 'implemented', 'launched',
    'spearheaded', 'pioneered', 'transformed', 'revolutionized', 'innovated',
    'analyzed', 'identified', 'discovered', 'resolved', 'solved', 'troubleshot',
    'increased', 'decreased', 'reduced', 'maximized', 'minimized', 'scaled',
    'integrated', 'consolidated', 'merged', 'combined', 'unified', 'aligned',
    'awarded', 'recognized', 'certified', 'promoted', 'selected', 'chosen'
}

# Resume sections to detect
RESUME_SECTIONS = {
    'summary': r'\b(summary|objective|profile|about)\b',
    'skills': r'\b(skills|technical skills|competencies|expertise)\b',
    'experience': r'\b(experience|work experience|professional experience|employment)\b',
    'education': r'\b(education|academic|degree|certification|bachelors|masters|phd|b\.s|b\.a|m\.s|m\.a)\b',
    'projects': r'\b(projects|portfolio|personal projects|key projects)\b'
}


# ==================== UTILITY FUNCTIONS ====================

def preprocess_text(text: str) -> str:
    """
    Clean and preprocess text for analysis.
    
    Args:
        text: Raw text to preprocess
        
    Returns:
        Cleaned and normalized text
    """
    # Convert to lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    # Remove special characters but keep hyphens and periods
    text = re.sub(rf"[{re.escape(string.punctuation.replace('-', '').replace('.', ''))}]", '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 50) -> List[str]:
    """
    Extract important keywords from text using TF-IDF and frequency analysis.
    
    Args:
        text: Text to extract keywords from
        min_length: Minimum keyword length (in characters)
        max_keywords: Maximum number of keywords to extract
        
    Returns:
        List of extracted keywords sorted by importance
    """
    words = preprocess_text(text).split()
    # Filter by minimum length
    words = [w for w in words if len(w) >= min_length]
    
    # Count word frequencies
    word_freq = Counter(words)
    
    # Get top keywords by frequency
    top_keywords = [word for word, freq in word_freq.most_common(max_keywords)]
    return top_keywords


def tokenize_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    
    Args:
        text: Text to split
        
    Returns:
        List of sentences
    """
    # Split on periods, question marks, exclamation marks, and newlines
    sentences = re.split(r'[.!?\n]+', text)
    return [s.strip() for s in sentences if s.strip()]


# ==================== SCORING FUNCTIONS ====================

def score_keyword_matching(resume_text: str, jd_text: str) -> Tuple[float, Dict]:
    """
    Score: Keyword Matching (40% weight)
    
    Extracts keywords from JD and checks how many appear in resume.
    Returns score and detailed breakdown.
    
    Args:
        resume_text: Resume text
        jd_text: Job Description text
        
    Returns:
        Tuple of (score: float 0-40, metadata: dict with details)
    """
    # Extract keywords from JD
    jd_keywords = set(extract_keywords(jd_text, max_keywords=40))
    
    # Preprocess resume text
    resume_processed = preprocess_text(resume_text)
    resume_words = set(resume_processed.split())
    
    # Find matched keywords
    matched_keywords = jd_keywords.intersection(resume_words)
    missing_keywords = jd_keywords - resume_words
    
    # Calculate score
    total_keywords = len(jd_keywords) if jd_keywords else 1
    match_ratio = len(matched_keywords) / total_keywords
    score = match_ratio * 40
    
    return score, {
        'matched_keywords': sorted(list(matched_keywords)),
        'missing_keywords': sorted(list(missing_keywords)),
        'total_jd_keywords': total_keywords,
        'matched_count': len(matched_keywords),
        'match_percentage': round(match_ratio * 100, 2)
    }


def score_resume_sections(resume_text: str) -> Tuple[float, Dict]:
    """
    Score: Resume Section Detection (20% weight)
    
    Detects presence of important resume sections.
    Each section contributes 4 points (5 sections × 4 = 20 total).
    
    Args:
        resume_text: Resume text
        
    Returns:
        Tuple of (score: float 0-20, metadata: dict with details)
    """
    resume_lower = resume_text.lower()
    sections_found = {}
    points_per_section = 4  # 20 points / 5 sections
    
    for section_name, pattern in RESUME_SECTIONS.items():
        found = bool(re.search(pattern, resume_lower))
        sections_found[section_name] = found
    
    # Calculate score
    detected_count = sum(1 for found in sections_found.values() if found)
    score = detected_count * points_per_section
    
    return score, {
        'sections_detected': sections_found,
        'detected_count': detected_count,
        'total_sections': len(RESUME_SECTIONS),
        'score_per_section': points_per_section
    }


def score_formatting_heuristics(resume_text: str) -> Tuple[float, Dict]:
    """
    Score: Formatting Heuristics (10% weight)
    
    Evaluates formatting quality:
    - Penalizes excessive special characters
    - Penalizes very low (<100) or very high (>2000) word count
    - Bonus for bullet points
    
    Args:
        resume_text: Resume text
        
    Returns:
        Tuple of (score: float 0-10, metadata: dict with details)
    """
    score = 10.0  # Start with full score
    details = {
        'word_count': 0,
        'special_char_ratio': 0.0,
        'bullet_point_count': 0,
        'penalties': [],
        'bonuses': []
    }
    
    # Check word count
    word_count = len(resume_text.split())
    details['word_count'] = word_count
    
    if word_count < 100:
        penalty = 3
        score -= penalty
        details['penalties'].append(f'Too few words ({word_count}): -{penalty}pts')
    elif word_count > 2000:
        penalty = 3
        score -= penalty
        details['penalties'].append(f'Too many words ({word_count}): -{penalty}pts')
    
    # Check special character ratio (excluding common ones like hyphens, periods)
    special_chars = sum(1 for c in resume_text if c in string.punctuation and c not in '.-,')
    special_char_ratio = special_chars / len(resume_text) if resume_text else 0
    details['special_char_ratio'] = round(special_char_ratio, 4)
    
    if special_char_ratio > 0.15:  # More than 15% special characters
        penalty = 2
        score -= penalty
        details['penalties'].append(f'Excessive special characters ({special_char_ratio:.2%}): -{penalty}pts')
    
    # Count bullet points (hyphens, asterisks at line start)
    bullet_count = len(re.findall(r'^\s*[-*•]\s', resume_text, re.MULTILINE))
    details['bullet_point_count'] = bullet_count
    
    if bullet_count >= 5:
        bonus = 2
        score += bonus
        details['bonuses'].append(f'Good use of bullet points ({bullet_count}): +{bonus}pts')
    
    # Clamp score between 0 and 10
    score = max(0, min(10, score))
    
    return score, details


def score_action_verbs(resume_text: str) -> Tuple[float, Dict]:
    """
    Score: Action Verbs & Impact Language (10% weight)
    
    Counts strong action verbs in resume. Higher usage → higher score.
    
    Args:
        resume_text: Resume text
        
    Returns:
        Tuple of (score: float 0-10, metadata: dict with details)
    """
    resume_lower = resume_text.lower()
    # Find words that are action verbs
    words = preprocess_text(resume_lower).split()
    
    action_verb_count = sum(1 for word in words if word in STRONG_ACTION_VERBS)
    
    # Scale: aim for 5+ action verbs for full score
    # 0-5 verbs: 0-6 points
    # 5-15 verbs: 6-10 points (bonus for excellent usage)
    if action_verb_count < 5:
        score = (action_verb_count / 5) * 6
    else:
        score = min(10, 6 + (action_verb_count - 5) / 10)
    
    return score, {
        'action_verb_count': action_verb_count,
        'verbs_found': [w for w in words if w in STRONG_ACTION_VERBS],
        'benchmark': '5-10+ strong action verbs for competitive resume'
    }


def score_semantic_similarity(resume_text: str, jd_text: str) -> Tuple[float, Dict]:
    """
    Score: Semantic Similarity (10% weight)
    
    Computes similarity between resume and JD using TF-IDF cosine similarity.
    
    Args:
        resume_text: Resume text
        jd_text: Job Description text
        
    Returns:
        Tuple of (score: float 0-10, metadata: dict with details)
    """
    try:
        # Preprocess texts
        resume_processed = preprocess_text(resume_text)
        jd_processed = preprocess_text(jd_text)
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=100,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        # Fit and transform both texts
        vectors = vectorizer.fit_transform([resume_processed, jd_processed])
        
        # Calculate cosine similarity
        similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
        
        # Scale similarity (0-1) to score (0-10)
        score = similarity * 10
        
    except Exception as e:
        # Fallback: simple word overlap similarity
        resume_words = set(preprocess_text(resume_text).split())
        jd_words = set(preprocess_text(jd_text).split())
        
        if not jd_words:
            similarity = 0
        else:
            overlap = len(resume_words.intersection(jd_words))
            similarity = overlap / len(jd_words)
        
        score = min(10, similarity * 10)
    
    return score, {
        'similarity_score': round(similarity, 4),
        'method': 'TF-IDF Cosine Similarity',
        'interpretation': f'{round(similarity * 100, 1)}% semantic overlap'
    }


# ==================== MAIN SCORING ENGINE ====================

def calculate_ats_score(resume_text: str, jd_text: str) -> Dict:
    """
    Calculate comprehensive ATS score (0-100) with breakdown by component.
    
    Components:
    - Keyword Matching (40%)
    - Resume Section Detection (20%)
    - Formatting Heuristics (10%)
    - Action Verbs & Impact Language (10%)
    - Semantic Similarity (10%)
    
    Args:
        resume_text: Resume text
        jd_text: Job Description text
        
    Returns:
        Dictionary with final score and detailed breakdown
    """
    # Calculate individual component scores
    keyword_score, keyword_details = score_keyword_matching(resume_text, jd_text)
    section_score, section_details = score_resume_sections(resume_text)
    formatting_score, formatting_details = score_formatting_heuristics(resume_text)
    action_verb_score, action_verb_details = score_action_verbs(resume_text)
    semantic_score, semantic_details = score_semantic_similarity(resume_text, jd_text)
    
    # Calculate final score
    final_score = (
        keyword_score +
        section_score +
        formatting_score +
        action_verb_score +
        semantic_score
    )
    
    # Clamp between 0 and 100
    final_score = max(0, min(100, final_score))
    
    return {
        'final_score': round(final_score, 2),
        'components': {
            'keyword_matching': {
                'score': round(keyword_score, 2),
                'weight': '40%',
                'details': keyword_details
            },
            'resume_sections': {
                'score': round(section_score, 2),
                'weight': '20%',
                'details': section_details
            },
            'formatting_heuristics': {
                'score': round(formatting_score, 2),
                'weight': '10%',
                'details': formatting_details
            },
            'action_verbs': {
                'score': round(action_verb_score, 2),
                'weight': '10%',
                'details': action_verb_details
            },
            'semantic_similarity': {
                'score': round(semantic_score, 2),
                'weight': '10%',
                'details': semantic_details
            }
        }
    }


# ==================== IMPROVEMENT SUGGESTIONS ====================

def generate_improvement_suggestions(ats_result: Dict, threshold: float = 75.0) -> List[str]:
    """
    Generate actionable improvement suggestions based on ATS score breakdown.
    
    Args:
        ats_result: Result dictionary from calculate_ats_score()
        threshold: Score threshold (below which suggestions are provided)
        
    Returns:
        List of improvement suggestions
    """
    suggestions = []
    components = ats_result['components']
    
    # Keyword Matching suggestions
    keyword_comp = components['keyword_matching']
    missing_keywords = keyword_comp['details'].get('missing_keywords', [])
    if keyword_comp['score'] < 20 and missing_keywords:
        suggestions.append(
            f"📌 Add missing keywords: {', '.join(missing_keywords[:10])}. "
            f"These terms are in the JD but not in your resume."
        )
    
    # Section Detection suggestions
    section_comp = components['resume_sections']
    sections_detected = section_comp['details'].get('sections_detected', {})
    missing_sections = [s for s, found in sections_detected.items() if not found]
    if section_comp['score'] < 20 and missing_sections:
        suggestions.append(
            f"📋 Add missing sections: {', '.join(missing_sections)}. "
            f"These are crucial for ATS parsing."
        )
    
    # Formatting suggestions
    format_comp = components['formatting_heuristics']
    penalties = format_comp['details'].get('penalties', [])
    if penalties:
        for penalty in penalties:
            suggestions.append(f"🔧 {penalty}")
    
    word_count = format_comp['details'].get('word_count', 0)
    if word_count < 100:
        suggestions.append(
            f"📝 Expand your resume content. Current: {word_count} words. "
            f"Target: 150-400 words per section."
        )
    
    # Action Verbs suggestions
    action_comp = components['action_verbs']
    if action_comp['score'] < 6:
        suggestions.append(
            f"💪 Use stronger action verbs. Current count: {action_comp['details']['action_verb_count']}. "
            f"Example verbs: developed, optimized, architected, led, accelerated."
        )
    
    # Semantic Similarity suggestions
    semantic_comp = components['semantic_similarity']
    if semantic_comp['score'] < 5:
        suggestions.append(
            f"🎯 Low semantic match with JD. Try to incorporate more role-specific terminology "
            f"and technical context from the job description."
        )
    
    # General suggestions
    if ats_result['final_score'] < threshold:
        suggestions.append(
            f"⭐ Overall ATS Score: {ats_result['final_score']}/100. "
            f"Focus on the areas above to improve match with this job description."
        )
    
    return suggestions if suggestions else [
        f"✅ Great ATS Score: {ats_result['final_score']}/100! "
        f"Your resume is well-optimized for this job description."
    ]
