"""
Example Usage & Testing for ATS Score Checker

This file demonstrates how to use the ATS scoring system programmatically
and provides sample test cases.

Run this file to test the ATS scorer without the Streamlit UI:
    python example_ats_usage.py
"""

from ats_scorer import calculate_ats_score, generate_improvement_suggestions
import json


# ==================== SAMPLE DATA ====================

SAMPLE_RESUME_1 = """
JOHN DOE
john.doe@email.com | (555) 123-4567 | LinkedIn.com/in/johndoe

PROFESSIONAL SUMMARY
Results-driven Python Developer with 5+ years of experience building scalable data pipelines and 
microservices. Expertise in cloud platforms, machine learning, and leading high-performing teams. 
Proven track record of delivering production-grade systems and optimizing system performance.

TECHNICAL SKILLS
Languages: Python, Java, SQL, Bash, JavaScript
Frameworks: Django, Flask, FastAPI, Spring Boot
Data & ML: Pandas, NumPy, TensorFlow, Scikit-learn, PyTorch
Cloud & DevOps: AWS (EC2, S3, RDS), Docker, Kubernetes, Jenkins, GitLab CI/CD
Databases: PostgreSQL, MongoDB, Redis, Cassandra
Tools: Git, Jira, Confluence, ELK Stack

PROFESSIONAL EXPERIENCE

Senior Python Developer | Tech Corp (2021 - Present)
• Architected and developed real-time data pipeline processing 10M+ events/day using Python and Apache Kafka
• Optimized database queries reducing query time by 45% and saving $50K/year in infrastructure costs
• Led team of 4 engineers in designing and implementing microservices-based architecture
• Implemented automated testing framework increasing code coverage from 60% to 92%
• Mentored 3 junior developers and conducted code reviews for 20+ pull requests monthly

Python Developer | Data Systems Inc (2019 - 2021)
• Developed ETL pipelines using Python and SQL, processing 500M+ records daily
• Built REST APIs serving 1M+ requests/day with 99.95% uptime
• Implemented machine learning models for customer segmentation achieving 15% improvement in accuracy
• Collaborated with cross-functional teams using Agile methodology (2-week sprints)

Junior Developer | StartUp Labs (2018 - 2019)
• Created web applications using Django and Flask frameworks
• Wrote efficient SQL queries and optimized database performance
• Participated in code reviews and contributed to technical documentation

EDUCATION
M.S. in Computer Science | State University (2018)
B.S. in Information Technology | Tech Institute (2016)

PROJECTS
Open Source Contributions: Active contributor to Flask-SQLAlchemy and NumPy projects
Personal Project: Developed open-source data analysis tool with 500+ GitHub stars
"""

SAMPLE_JD_1 = """
JOB TITLE: Senior Python Developer

COMPANY: Cloud Innovations Inc
LOCATION: San Francisco, CA (Remote Friendly)

ABOUT THE ROLE
We are seeking a Senior Python Developer to join our growing data engineering team. You will design 
and build scalable systems processing millions of events in real-time. This role involves working with 
cutting-edge technologies and leading technical decisions for the platform.

KEY RESPONSIBILITIES
• Design and build scalable Python applications and data pipelines
• Architect microservices-based solutions for real-time data processing
• Optimize database performance and SQL queries
• Lead code reviews and mentor junior developers
• Implement automated testing and CI/CD pipelines
• Collaborate with product managers and data scientists
• Troubleshoot and resolve production issues

REQUIRED QUALIFICATIONS
• 5+ years of professional Python development experience
• Strong experience with SQL and database optimization
• Experience building REST APIs and microservices
• Proficiency with cloud platforms (AWS, GCP, or Azure)
• Experience with Docker and Kubernetes
• Knowledge of machine learning concepts and frameworks
• Excellent problem-solving and communication skills
• Bachelor's degree in Computer Science or related field

PREFERRED QUALIFICATIONS
• Experience with Kafka or similar streaming platforms
• Familiarity with Agile development methodologies
• Experience mentoring junior developers
• Open source contributions
• Master's degree in Computer Science or related field

TECHNICAL SKILLS NEEDED
Python, SQL, REST APIs, Microservices, Cloud Platforms, Docker, Kubernetes, 
Machine Learning, ETL, Data Pipelines, Testing, CI/CD, Git, Linux

COMPENSATION & BENEFITS
• Salary: $150,000 - $200,000
• Comprehensive health insurance
• Remote work flexibility
• Professional development budget
"""


SAMPLE_RESUME_2 = """
JANE SMITH
jane@email.com | (555) 987-6543

WORK EXPERIENCE
Worked in IT for several years doing various tasks.

SKILLS
Computers, Programming, Data, Cloud

EDUCATION
Computer Science degree
"""

SAMPLE_JD_2 = """
JAVA DEVELOPER WANTED

Looking for Java developer. Must have:
- 5+ years Java experience
- Spring Boot knowledge  
- Microservices architecture
- REST API design
- Agile experience
- AWS or GCP
- Strong SQL skills
- Docker knowledge

Nice to have: Kubernetes, Jenkins, Maven, Gradle
"""


SAMPLE_RESUME_3 = """
ALEX JOHNSON
Senior Data Analyst with expertise in business intelligence and analytics.

SUMMARY
10 years in data analytics, business intelligence, and reporting. Excel at translating 
business requirements into analytical solutions. Strong SQL and Tableau expertise.

TECHNICAL SKILLS
SQL, Tableau, Power BI, Excel, Python (basic), Hadoop, Apache Spark, AWS

EXPERIENCE
Data Analyst at Analytics Corp - 5 years
- Created and optimized 50+ business reports
- Designed dashboard solutions in Tableau
- Analyzed customer behavior trends
- Improved query performance by 30%

Senior Data Analyst at BI Solutions - 5 years
- Led analytics team
- Managed data warehouse projects
- Implemented self-service BI solutions
"""

SAMPLE_JD_3 = """
PYTHON MACHINE LEARNING ENGINEER

We need a Python/ML engineer for our AI team.

Required:
- Advanced Python (NumPy, Pandas, Scikit-learn)
- TensorFlow or PyTorch experience
- Machine learning model deployment
- Strong statistics background
- Cloud ML experience (AWS SageMaker, GCP Vertex AI)
- Docker and containerization
- 5+ years ML engineering

We build and deploy AI models at scale.
"""


# ==================== TEST FUNCTIONS ====================

def print_ats_result(name: str, ats_result: dict):
    """Pretty print ATS result."""
    print("\n" + "=" * 80)
    print(f"TEST: {name}")
    print("=" * 80)
    
    # Final Score
    score = ats_result['final_score']
    if score >= 80:
        status = "🟢 EXCELLENT"
    elif score >= 60:
        status = "🟡 GOOD"
    else:
        status = "🔴 NEEDS IMPROVEMENT"
    
    print(f"\nFinal ATS Score: {score}/100 [{status}]")
    
    # Component Breakdown
    print("\n" + "-" * 80)
    print("SCORE BREAKDOWN")
    print("-" * 80)
    
    components = ats_result['components']
    total_possible = 0
    
    for comp_name, comp_data in components.items():
        score = comp_data['score']
        weight = comp_data['weight']
        print(f"{comp_name.replace('_', ' ').title():.<40} {score:>6} / {weight}")
        total_possible += float(weight.rstrip('%'))
    
    # Keyword Details
    print("\n" + "-" * 80)
    print("KEYWORD MATCHING ANALYSIS")
    print("-" * 80)
    keyword_details = components['keyword_matching']['details']
    print(f"Match Rate: {keyword_details['match_percentage']}%")
    print(f"Matched Keywords: {keyword_details['matched_count']}/{keyword_details['total_jd_keywords']}")
    
    if keyword_details['matched_keywords']:
        matched = keyword_details['matched_keywords'][:10]
        print(f"✅ Found: {', '.join(matched)}")
    
    if keyword_details['missing_keywords']:
        missing = keyword_details['missing_keywords'][:10]
        print(f"❌ Missing: {', '.join(missing)}")
    
    # Section Detection
    print("\n" + "-" * 80)
    print("RESUME SECTIONS")
    print("-" * 80)
    sections = components['resume_sections']['details']['sections_detected']
    for section, found in sections.items():
        status = "✅" if found else "❌"
        print(f"{status} {section.title()}")
    
    # Action Verbs
    print("\n" + "-" * 80)
    print("ACTION VERBS")
    print("-" * 80)
    action_details = components['action_verbs']['details']
    print(f"Count: {action_details['action_verb_count']}")
    if action_details['verbs_found']:
        verbs = list(set(action_details['verbs_found']))[:10]
        print(f"Found: {', '.join(verbs)}")
    
    # Suggestions
    print("\n" + "-" * 80)
    print("IMPROVEMENT SUGGESTIONS")
    print("-" * 80)
    suggestions = generate_improvement_suggestions(ats_result)
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion}\n")


def test_case_1():
    """Test: Strong match between resume and JD"""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " TEST CASE 1: STRONG MATCH - Senior Python Developer ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    
    ats_result = calculate_ats_score(SAMPLE_RESUME_1, SAMPLE_JD_1)
    print_ats_result("Senior Python Developer (High Match)", ats_result)


def test_case_2():
    """Test: Weak match between resume and JD"""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " TEST CASE 2: WEAK MATCH - Vague Resume vs Java Role ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    
    ats_result = calculate_ats_score(SAMPLE_RESUME_2, SAMPLE_JD_2)
    print_ats_result("Generic Resume vs Java Developer Role", ats_result)


def test_case_3():
    """Test: Partial match (different specialization)"""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " TEST CASE 3: PARTIAL MATCH - Data Analyst vs ML Engineer ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    
    ats_result = calculate_ats_score(SAMPLE_RESUME_3, SAMPLE_JD_3)
    print_ats_result("Data Analyst vs Python ML Engineer Role", ats_result)


def test_case_4():
    """Test: Edge case - Empty or minimal inputs"""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " TEST CASE 4: EDGE CASE - Minimal Content ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    
    minimal_resume = "John Doe Python Developer"
    minimal_jd = "Python developer needed"
    
    ats_result = calculate_ats_score(minimal_resume, minimal_jd)
    print_ats_result("Minimal Resume vs Minimal JD", ats_result)


# ==================== MAIN ====================

if __name__ == '__main__':
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " ATS SCORE CHECKER - EXAMPLE USAGE & TESTING ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Run all test cases
    test_case_1()
    test_case_2()
    test_case_3()
    test_case_4()
    
    # Summary
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("1. Keyword Matching is the most important (40%) - use relevant skills/keywords")
    print("2. Resume Sections matter (20%) - ensure all sections are present")
    print("3. Action verbs (10%) - use strong, impactful language")
    print("4. Formatting (10%) - maintain good word count and formatting")
    print("5. Semantic Match (10%) - overall conceptual alignment with JD")
    print("\nFor more information, see ATS_SCORER_GUIDE.md\n")
