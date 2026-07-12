import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------------------------------------------------------------
# 1. PREDEFINED DATA SCIENCE & ML SKILLS DATABASE
# -----------------------------------------------------------------------------
PREDEFINED_SKILLS = [
    # Programming Languages
    "Python", "R", "SQL", "Julia", "Scala", "Java", "C++", "C#", "JavaScript", "MATLAB", "Go", "Bash", "Rust", "SAS",

    # Libraries & Frameworks
    "Pandas", "NumPy", "SciPy", "Scikit-Learn", "Sklearn", "TensorFlow", "PyTorch", "Keras", "NLTK", "spaCy",
    "Hugging Face", "HuggingFace", "XGBoost", "LightGBM", "CatBoost", "OpenCV", "Gensim", "Statsmodels",
    "LangChain", "LlamaIndex", "PySpark", "Dask", "FastAPI", "Flask", "Django",

    # ML/AI Concepts & Sub-fields
    "Machine Learning", "Deep Learning", "Natural Language Processing", "NLP", "Computer Vision",
    "Reinforcement Learning", "Generative AI", "LLMs", "Large Language Models", "Transformers",
    "Neural Networks", "Transfer Learning", "Supervised Learning", "Unsupervised Learning",
    "Feature Engineering", "Model Deployment", "MLOps", "A/B Testing", "Dimensionality Reduction",
    "Clustering", "Regression", "Classification", "Time Series", "Anomaly Detection",

    # Data Visualization & Business Intelligence (BI)
    "Power BI", "PowerBI", "Tableau", "Looker", "Qlik", "QlikView", "Matplotlib", "Seaborn", "Plotly", "Dash", "Streamlit", "Shiny",

    # Big Data & Cloud Platforms
    "Spark", "Hadoop", "MapReduce", "AWS", "Amazon Web Services", "Azure", "GCP", "Google Cloud Platform",
    "Snowflake", "Databricks", "Redshift", "BigQuery", "Hive", "Kafka", "Cassandra", "Apache Spark",

    # DevOps, CI/CD & Development Tools
    "Docker", "Kubernetes", "Git", "GitHub", "GitLab", "CI/CD", "MLflow", "DVC", "Airflow", "Prefect", "Linux",

    # Databases (Relational & NoSQL)
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "DynamoDB", "Neo4j", "SQLite", "Oracle",

    # Mathematics & Theory
    "Statistics", "Probability", "Linear Algebra", "Calculus", "Optimization", "Hypothesis Testing", "Bayesian Statistics"
]

# Synonym groups to map different ways of writing the same technology
SYNONYM_GROUPS = [
    {"nlp", "natural language processing"},
    {"power bi", "powerbi"},
    {"scikit-learn", "sklearn"},
    {"hugging face", "huggingface"},
    {"aws", "amazon web services"},
    {"gcp", "google cloud platform"},
    {"spark", "apache spark"}
]

# Cache loaded sentence-transformer models to avoid reloading
_model_cache = {}

def get_sentence_transformer_model(model_name='all-MiniLM-L6-v2'):
    """
    Loads and caches the sentence transformer model to prevent reloading overhead.
    """
    if model_name not in _model_cache:
        _model_cache[model_name] = SentenceTransformer(model_name)
    return _model_cache[model_name]

# -----------------------------------------------------------------------------
# 2. SKILLS EXTRACTION LOGIC
# -----------------------------------------------------------------------------
def extract_predefined_skills(text):
    """
    Scans the clean text for skills from the predefined list using regex.
    Uses negative lookarounds to avoid matching substrings of larger words
    (e.g., matching 'Go' inside 'google', or 'R' inside 'learning').
    """
    if not text:
        return set()

    text_lower = text.lower()
    found_skills = set()

    for skill in PREDEFINED_SKILLS:
        # Use lookarounds to enforce that the keyword is a distinct token/term.
        # This properly handles skills with symbols like C++, C#, .NET, and hyphens like Scikit-Learn
        pattern = r'(?<![a-zA-Z0-9_])' + re.escape(skill.lower()) + r'(?![a-zA-Z0-9_])'
        if re.search(pattern, text_lower):
            found_skills.add(skill)

    return found_skills

def detect_company_names(text):
    """
    Extracts potential company names from the text using common patterns.
    """
    if not text:
        return set()
    
    companies = set()
    
    # Pattern 1: "... at [Company]" (capitalized word)
    matches_at = re.findall(r'(?i)\bat\s+([A-Z][a-zA-Z0-9]+)', text)
    for m in matches_at:
        companies.add(m.strip().lower())
        
    # Pattern 2: "... join [Company]"
    matches_join = re.findall(r'(?i)\bjoin\s+([A-Z][a-zA-Z0-9]+)', text)
    for m in matches_join:
        companies.add(m.strip().lower())
        
    # Pattern 3: "[Company] is looking for / is hiring"
    matches_hiring = re.findall(r'\b([A-Z][a-zA-Z0-9]+)\s+(?:is\s+)?(?:hiring|looking\s+for)', text)
    for m in matches_hiring:
        companies.add(m.strip().lower())

    # Pattern 4: "About [Company]"
    matches_about = re.findall(r'(?i)\babout\s+([A-Z][a-zA-Z0-9]+)', text)
    for m in matches_about:
        companies.add(m.strip().lower())

    # Filter out common false positives that might start with a capital letter
    common_false_positives = {
        "at", "the", "a", "an", "this", "our", "their", "we", "you", "your", 
        "intern", "trainee", "joining", "present", "least", "once", "first",
        "highly", "flexible", "passionate", "working", "leading", "growing",
        "modern", "innovative", "top", "best", "global", "local"
    }
    
    return companies.difference(common_false_positives)


def extract_ner_skills(text, predefined_found, nlp):
    """
    Fallback NER skill extraction using spaCy.
    Looks for PRODUCT or WORK_OF_ART entities (excluding ORG to prevent company/org leakage)
    that do not appear in the predefined database to capture unique or proprietary systems/tools.
    """
    if not text or not nlp:
        return set()

    doc = nlp(text)
    ner_skills = set()

    # Common text blocks or sections to ignore to filter out noise
    exclusions = {
        "resume", "cv", "curriculum vitae", "university", "college", "school",
        "experience", "education", "summary", "project", "projects", "company",
        "contact", "phone", "email", "address", "city", "state", "zip", "hobbies",
        "interests", "languages", "profile", "career", "objective", "references",
        "duration", "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december",
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        # Job titles, levels, and location names to prevent non-skill leakages
        "intern", "internship", "trainee", "training", "job", "role", "position",
        "candidate", "applicant", "employee", "employer", "recruiter", "manager",
        "engineer", "developer", "analyst", "specialist", "expert", "consultant",
        "lead", "senior", "junior", "fresher", "entry-level", "full-time", "part-time",
        "contract", "remote", "hybrid", "on-site", "office", "salary", "stipend",
        "location", "india", "usa", "uk", "canada", "germany", "singapore", "bengaluru",
        "bangalore", "pune", "mumbai", "delhi", "noida", "hyderabad", "chennai"
    }

    # Dynamically detect and exclude company names
    detected_companies = detect_company_names(text)
    exclusions.update(detected_companies)

    predefined_found_lower = {s.lower() for s in predefined_found}

    for ent in doc.ents:
        # Exclude ORGs entirely to avoid leakage of company/organization names
        if ent.label_ in ["PRODUCT", "WORK_OF_ART"]:
            ent_text = ent.text.strip()
            # Clean and normalize spaces
            ent_clean = re.sub(r'\s+', ' ', ent_text)
            ent_lower = ent_clean.lower()

            # Filtering criteria:
            # - Length > 1 to avoid noise
            # - Not already captured in the predefined skills
            # - Not in the standard/dynamic exclusions list
            # - Not just a digit
            # - Max 3 words to capture standard technology names
            if (len(ent_clean) > 1 and
                ent_lower not in predefined_found_lower and
                ent_lower not in exclusions and
                not ent_clean.isdigit() and
                len(ent_clean.split()) <= 3):

                # Check that none of the individual words in the entity are exclusions
                words = [w for w in ent_lower.split() if w not in exclusions]
                if words:
                    # Capture name with its original title casing
                    ner_skills.add(ent_clean)

    return ner_skills

# -----------------------------------------------------------------------------
# 3. COMPARISON & SIMILARITY COMPUTATION
# -----------------------------------------------------------------------------
def check_synonym_match(resume_skills_lower, jd_skill_lower):
    """
    Checks if the resume contains a skill or any of its defined synonyms.
    """
    # 1. Direct check
    if jd_skill_lower in resume_skills_lower:
        return True

    # 2. Check group synonyms
    for group in SYNONYM_GROUPS:
        if jd_skill_lower in group:
            # If the JD skill is in this synonym group, check if any of the resume skills are also in it
            if any(res_skill in group for res_skill in resume_skills_lower):
                return True
    return False

def get_missing_skills(resume_skills, jd_skills):
    """
    Computes skills present in the JD but missing from the Resume.
    Utilizes the synonym mapping list to prevent flagging synonyms as missing.
    """
    resume_skills_lower = {s.lower() for s in resume_skills}
    missing = []

    for skill in jd_skills:
        if not check_synonym_match(resume_skills_lower, skill.lower()):
            missing.append(skill)

    return missing

def calculate_similarity(resume_text, jd_text, model=None):
    """
    Generates embeddings and computes cosine similarity between the clean texts.

    Parameters:
    - resume_text: Preprocessed text of the resume.
    - jd_text: Preprocessed text of the job description.
    - model: Optional preloaded SentenceTransformer model.

    Returns:
    - Match score percentage (0.0 to 100.0).
    """
    if not resume_text or not jd_text:
        return 0.0

    if model is None:
        model = get_sentence_transformer_model()

    # Encode both text documents
    embeddings = model.encode([resume_text, jd_text])

    # Compute Cosine Similarity between the two vectors
    similarity_val = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

    # Convert range [-1, 1] to a readable percentage [0, 100]
    match_score = float(similarity_val) * 100.0
    return max(0.0, min(100.0, match_score))
