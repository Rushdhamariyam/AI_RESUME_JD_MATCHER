AI Resume JD Matcher

A Streamlit app that analyzes how well a resume matches a target job description — and helps you close the gap.

Upload a resume and paste a job description to get a compatibility score, a breakdown of matched and missing skills, and an AI-generated resume tailored to that specific role.

Features


Compatibility scoring — semantic comparison between resume and job description content, returned as a percentage match.
Skill gap analysis — clearly separated lists of:

Confirmed match: skills/keywords present in both the resume and the posting.
Missing from resume: requirements from the posting not found in the resume, with suggestions on how to address them.



Tailored resume generation — creates an ATS-optimized version of the resume rewritten to better align with the job description, without fabricating experience or credentials.
Editable output — the tailored resume is shown in an editable text area so you can review and adjust before exporting.
Offline fallback — if the AI service is unavailable (e.g. API quota limits), the app falls back to a rule-based tailoring pipeline so the feature still works.


How It Works


Upload your resume as a PDF.
Paste the target job description into the text box.
Click Check Match & Analyze to get your compatibility score and skill breakdown.
Click Generate Tailored Resume to produce a version of your resume optimized for that job posting.
Review, edit, and download the result.


Tech Stack


Streamlit — web app framework and UI
Python — core application logic
NLP / sentence embeddings — for semantic similarity scoring between resume and job description
OpenAI API — for AI-generated resume tailoring (with an offline fallback when unavailable)


Getting Started

Prerequisites


Python 3.9+
An OpenAI API key (optional — required only for AI-powered resume tailoring; the app falls back to a rule-based pipeline without it)


Installation

bashgit clone https://github.com/Rushdhamariyam/AI_RESUME_JD_MATCHER.git
cd AI_RESUME_JD_MATCHER
pip install -r requirements.txt

Configuration

Create a .env file in the project root and add your OpenAI API key:

OPENAI_API_KEY=your_api_key_here

Run the app

bashstreamlit run app.py

The app will be available at http://localhost:8501.

Roadmap


 Export tailored resume as .docx / .pdf
 Support multiple resume formats (DOCX, TXT)
 Batch matching against multiple job descriptions
 Improved entity filtering (e.g. excluding company names from required skills)


License

This project is open source and available under the MIT License.

Author

Rushdha Mariyam
