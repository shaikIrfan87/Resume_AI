import streamlit as st
import os
import sys
import sqlite3
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir / "finalt"))

# Import existing services
try:
    from services.gemini_service import get_gemini_analysis, extract_job_title
    from services.email_service import send_shortlist_email, send_bulk_shortlist_emails
except ImportError as e:
    st.error(f"Error importing services: {e}")
    st.stop()

# Database functions
def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect('resumematch.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            description TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidate (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            resume_filename TEXT NOT NULL,
            job_id INTEGER NOT NULL,
            FOREIGN KEY (job_id) REFERENCES job (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_result (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score INTEGER NOT NULL,
            verdict TEXT NOT NULL,
            summary TEXT NOT NULL,
            feedback TEXT NOT NULL,
            missing_skills TEXT,
            candidate_id INTEGER NOT NULL UNIQUE,
            FOREIGN KEY (candidate_id) REFERENCES candidate (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect('resumematch.db')

# Utility functions
def extract_text_from_pdf(file_content):
    """Extract text from PDF file content"""
    try:
        import pdfplumber
        import io
        
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return ""

def extract_text_from_docx(file_content):
    """Extract text from DOCX file content"""
    try:
        from docx import Document
        import io
        
        doc = Document(io.BytesIO(file_content))
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        st.error(f"Error extracting text from DOCX: {e}")
        return ""

def save_uploaded_file(uploaded_file, upload_folder="uploads"):
    """Save uploaded file and return filepath"""
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Page configuration
st.set_page_config(
    page_title="Resume Matching System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
if 'db_initialized' not in st.session_state:
    init_database()
    st.session_state.db_initialized = True

# Sidebar navigation
st.sidebar.title("🎯 Resume Match AI")
page = st.sidebar.selectbox(
    "Navigate to:",
    ["Home", "Dashboard", "Jobs", "Resumes", "Cover Letters"]
)

# Main content based on selected page
if page == "Home":
    st.title("🎯 Resume Matching System")
    st.markdown("""
    ### Welcome to the AI-Powered Resume Matching System!
    
    This system helps you:
    - 📝 **Manage Job Descriptions**: Upload and organize job postings
    - 📄 **Analyze Resumes**: Upload candidate resumes for AI-powered analysis  
    - 🎯 **Match Candidates**: Get relevance scores and fit assessments
    - 📧 **Send Notifications**: Email shortlisted candidates automatically
    - 📊 **Track Progress**: Monitor recruitment analytics on the dashboard
    
    **Getting Started:**
    1. Add job descriptions in the **Jobs** section
    2. Upload candidate resumes in the **Resumes** section
    3. View results and analytics in the **Dashboard**
    4. Generate cover letters in the **Cover Letters** section
    
    ---
    *Powered by Google Gemini AI for intelligent resume analysis*
    """)
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM job")
    total_jobs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM candidate")
    total_candidates = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM analysis_result WHERE score >= 65")
    shortlisted_count = cursor.fetchone()[0]
    
    conn.close()
    
    with col1:
        st.metric("Total Jobs", total_jobs)
    with col2:
        st.metric("Total Applications", total_candidates)
    with col3:
        st.metric("Shortlisted", shortlisted_count)

elif page == "Dashboard":
    st.title("📊 Dashboard")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get comprehensive job statistics
    cursor.execute("""
        SELECT 
            j.id, j.title, j.company,
            COUNT(c.id) as total_applicants,
            COUNT(CASE WHEN ar.score >= 65 THEN 1 END) as shortlisted_count,
            COUNT(CASE WHEN ar.score < 65 THEN 1 END) as rejected_count,
            ROUND(AVG(ar.score), 1) as avg_score
        FROM job j
        LEFT JOIN candidate c ON j.id = c.job_id
        LEFT JOIN analysis_result ar ON c.id = ar.candidate_id
        GROUP BY j.id, j.title, j.company
        ORDER BY j.id DESC
    """)
    
    jobs_data = cursor.fetchall()
    conn.close()
    
    if jobs_data:
        # Convert to DataFrame for better display
        df = pd.DataFrame(jobs_data, columns=[
            'ID', 'Job Title', 'Company', 'Total Applicants', 
            'Shortlisted', 'Rejected', 'Avg Score'
        ])
        
        st.dataframe(df, use_container_width=True)
        
        # Charts
        if len(df) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Applications by Job")
                chart_data = df[['Job Title', 'Total Applicants']].set_index('Job Title')
                st.bar_chart(chart_data)
            
            with col2:
                st.subheader("Shortlisting Rate")
                df['Shortlisting Rate'] = (df['Shortlisted'] / df['Total Applicants'] * 100).fillna(0)
                rate_data = df[['Job Title', 'Shortlisting Rate']].set_index('Job Title')
                st.bar_chart(rate_data)
    else:
        st.info("No jobs found. Add some jobs first to see dashboard analytics.")

elif page == "Jobs":
    st.title("💼 Job Management")
    
    # Add new job section
    st.subheader("Add New Job")
    
    with st.form("add_job_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("Company Name*", placeholder="e.g., Tech Corp Inc.")
            job_title = st.text_input("Job Title", placeholder="Will be extracted from description if empty")
        
        with col2:
            job_description = st.text_area(
                "Job Description*", 
                height=150,
                placeholder="Paste the complete job description here..."
            )
        
        uploaded_file = st.file_uploader(
            "Or Upload Job Description File", 
            type=['pdf', 'docx'],
            help="Upload PDF or DOCX file containing job description"
        )
        
        submitted = st.form_submit_button("Add Job")
        
        if submitted:
            description = job_description
            title = job_title
            
            # Handle file upload
            if uploaded_file:
                file_content = uploaded_file.read()
                if uploaded_file.type == "application/pdf":
                    description = extract_text_from_pdf(file_content) or description
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    description = extract_text_from_docx(file_content) or description
            
            if not company_name or not description:
                st.error("Company name and job description are required!")
            else:
                # Extract job title if not provided
                if not title:
                    with st.spinner("Extracting job title..."):
                        try:
                            title = extract_job_title(description)
                        except:
                            title = f"Job Position {datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Save to database
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO job (title, company, description) VALUES (?, ?, ?)",
                    (title, company_name, description)
                )
                conn.commit()
                conn.close()
                
                st.success(f"Job '{title}' added successfully!")
                st.experimental_rerun()
    
    st.divider()
    
    # Display existing jobs
    st.subheader("Existing Jobs")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, company, description FROM job ORDER BY id DESC")
    jobs = cursor.fetchall()
    conn.close()
    
    if jobs:
        for job in jobs:
            job_id, title, company, description = job
            
            with st.expander(f"🏢 {title} at {company}"):
                st.write(f"**Job ID:** {job_id}")
                st.write(f"**Description:**")
                st.write(description[:500] + "..." if len(description) > 500 else description)
                
                if st.button(f"Delete Job {job_id}", key=f"delete_{job_id}", type="secondary"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    # Delete related records first
                    cursor.execute("DELETE FROM analysis_result WHERE candidate_id IN (SELECT id FROM candidate WHERE job_id = ?)", (job_id,))
                    cursor.execute("DELETE FROM candidate WHERE job_id = ?", (job_id,))
                    cursor.execute("DELETE FROM job WHERE id = ?", (job_id,))
                    conn.commit()
                    conn.close()
                    st.success("Job deleted successfully!")
                    st.experimental_rerun()
    else:
        st.info("No jobs added yet. Add your first job above!")

elif page == "Resumes":
    st.title("📄 Resume Analysis")
    
    # Get available jobs
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, company FROM job ORDER BY id DESC")
    jobs = cursor.fetchall()
    conn.close()
    
    if not jobs:
        st.warning("No jobs available. Please add a job first in the Jobs section.")
        st.stop()
    
    # Job selection
    job_options = {f"{title} at {company}": job_id for job_id, title, company in jobs}
    selected_job_display = st.selectbox("Select Job for Analysis:", list(job_options.keys()))
    selected_job_id = job_options[selected_job_display]
    
    st.divider()
    
    # Resume upload section
    st.subheader("Upload Resumes")
    uploaded_files = st.file_uploader(
        "Choose resume files", 
        type=['pdf'], 
        accept_multiple_files=True,
        help="Upload PDF resumes for analysis against the selected job"
    )
    
    if uploaded_files:
        if st.button("Analyze Resumes", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_files = len(uploaded_files)
            processed_count = 0
            
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {uploaded_file.name}...")
                progress_bar.progress((i + 1) / total_files)
                
                try:
                    # Extract text from PDF
                    file_content = uploaded_file.read()
                    resume_text = extract_text_from_pdf(file_content)
                    
                    if not resume_text:
                        st.warning(f"Could not extract text from {uploaded_file.name}")
                        continue
                    
                    # Save file
                    file_path = save_uploaded_file(uploaded_file)
                    
                    # Create candidate name from filename
                    candidate_name = os.path.splitext(uploaded_file.name)[0].replace('_', ' ').replace('-', ' ').title()
                    
                    # Save candidate to database
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO candidate (name, resume_filename, job_id) VALUES (?, ?, ?)",
                        (candidate_name, uploaded_file.name, selected_job_id)
                    )
                    candidate_id = cursor.lastrowid
                    conn.commit()
                    conn.close()
                    
                    # Get job description
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT description FROM job WHERE id = ?", (selected_job_id,))
                    job_description = cursor.fetchone()[0]
                    conn.close()
                    
                    # Get AI analysis
                    with st.spinner(f"Analyzing {candidate_name}..."):
                        analysis_data = get_gemini_analysis(job_description, resume_text)
                    
                    if "error" not in analysis_data:
                        # Save analysis result
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            """INSERT INTO analysis_result 
                            (score, verdict, summary, feedback, missing_skills, candidate_id) 
                            VALUES (?, ?, ?, ?, ?, ?)""",
                            (
                                analysis_data.get('relevance_score'),
                                analysis_data.get('fit_verdict'),
                                analysis_data.get('summary'),
                                analysis_data.get('personalized_feedback'),
                                json.dumps(analysis_data.get('missing_skills', [])),
                                candidate_id
                            )
                        )
                        conn.commit()
                        conn.close()
                        processed_count += 1
                    else:
                        st.error(f"Analysis failed for {candidate_name}: {analysis_data.get('error')}")
                        
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                    continue
            
            status_text.text("Analysis complete!")
            st.success(f"Successfully processed {processed_count} out of {total_files} resumes.")
    
    st.divider()
    
    # Display results for selected job
    st.subheader(f"Analysis Results for: {selected_job_display}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.name, c.email, c.resume_filename, 
               ar.score, ar.verdict, ar.summary, ar.feedback, ar.missing_skills
        FROM candidate c
        LEFT JOIN analysis_result ar ON c.id = ar.candidate_id
        WHERE c.job_id = ?
        ORDER BY ar.score DESC, c.id DESC
    """, (selected_job_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    if results:
        # Show summary statistics
        analyzed_results = [r for r in results if r[4] is not None]  # Results with scores
        if analyzed_results:
            scores = [r[4] for r in analyzed_results]
            shortlisted = [r for r in analyzed_results if r[4] >= 65]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Candidates", len(results))
            with col2:
                st.metric("Analyzed", len(analyzed_results))
            with col3:
                st.metric("Shortlisted (≥65%)", len(shortlisted))
            with col4:
                st.metric("Average Score", f"{sum(scores)/len(scores):.1f}%" if scores else "N/A")
        
        st.divider()
        
        # Display individual results
        for result in results:
            candidate_id, name, email, filename, score, verdict, summary, feedback, missing_skills = result
            
            if score is not None:
                # Color coding based on score
                if score >= 85:
                    score_color = "🟢"
                elif score >= 65:
                    score_color = "🟡"
                else:
                    score_color = "🔴"
                
                with st.expander(f"{score_color} {name} - Score: {score}% ({verdict})", expanded=score >= 65):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Summary:** {summary}")
                        st.write(f"**Feedback:** {feedback}")
                        
                        if missing_skills:
                            skills = json.loads(missing_skills) if isinstance(missing_skills, str) else missing_skills
                            if skills:
                                st.write(f"**Missing Skills:** {', '.join(skills)}")
                    
                    with col2:
                        st.write(f"**File:** {filename}")
                        st.write(f"**Score:** {score}%")
                        st.write(f"**Verdict:** {verdict}")
                        
                        # Email management
                        current_email = email or ""
                        new_email = st.text_input(
                            "Email:", 
                            value=current_email, 
                            key=f"email_{candidate_id}",
                            placeholder="candidate@email.com"
                        )
                        
                        if new_email != current_email:
                            if st.button(f"Update Email", key=f"update_{candidate_id}"):
                                conn = get_db_connection()
                                cursor = conn.cursor()
                                cursor.execute(
                                    "UPDATE candidate SET email = ? WHERE id = ?", 
                                    (new_email, candidate_id)
                                )
                                conn.commit()
                                conn.close()
                                st.success("Email updated!")
                                st.experimental_rerun()
            else:
                with st.expander(f"⚪ {name} - Not analyzed yet"):
                    st.info(f"Resume '{filename}' is uploaded but not analyzed yet.")
        
        # Shortlisted candidates email section
        shortlisted_candidates = [r for r in results if r[4] and r[4] >= 65 and r[2]]  # With email
        if shortlisted_candidates:
            st.divider()
            st.subheader("📧 Send Shortlist Emails")
            
            selected_candidates = st.multiselect(
                "Select candidates to email:",
                options=[(r[0], f"{r[1]} ({r[4]}%)") for r in shortlisted_candidates],
                format_func=lambda x: x[1]
            )
            
            if selected_candidates and st.button("Send Shortlist Emails", type="primary"):
                # Get job details
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT title, company FROM job WHERE id = ?", (selected_job_id,))
                job_title, company = cursor.fetchone()
                conn.close()
                
                # Prepare email data
                candidates_data = []
                for candidate_id, _ in selected_candidates:
                    result = next(r for r in shortlisted_candidates if r[0] == candidate_id)
                    candidates_data.append({
                        'name': result[1],
                        'email': result[2],
                        'job_title': job_title,
                        'company_name': company
                    })
                
                # Note: Email functionality needs proper Flask-Mail setup
                # For Streamlit, we'll show the email content instead
                st.success(f"Would send emails to {len(candidates_data)} candidates:")
                for candidate in candidates_data:
                    st.write(f"- {candidate['name']} ({candidate['email']})")
                
                # In a production environment, you'd integrate with an email service
                st.info("💡 Email functionality requires proper email service configuration. Check the .env file for email setup.")
    
    else:
        st.info("No candidates uploaded for this job yet.")

elif page == "Cover Letters":
    st.title("✉️ Cover Letter Generator")
    
    st.markdown("""
    Generate personalized cover letters using AI analysis of job descriptions and candidate resumes.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Job Description")
        job_description = st.text_area(
            "Paste job description here:",
            height=300,
            placeholder="Enter the complete job description..."
        )
    
    with col2:
        st.subheader("Resume/Candidate Profile")
        resume_text = st.text_area(
            "Paste resume content here:",
            height=300,
            placeholder="Enter the candidate's resume content..."
        )
    
    # Alternative: Upload files
    st.divider()
    st.subheader("Or Upload Files")
    
    col1, col2 = st.columns(2)
    with col1:
        jd_file = st.file_uploader("Upload Job Description", type=['pdf', 'docx', 'txt'])
        if jd_file:
            file_content = jd_file.read()
            if jd_file.type == "application/pdf":
                job_description = extract_text_from_pdf(file_content)
            elif jd_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                job_description = extract_text_from_docx(file_content)
            else:
                job_description = file_content.decode('utf-8')
    
    with col2:
        resume_file = st.file_uploader("Upload Resume", type=['pdf', 'docx', 'txt'])
        if resume_file:
            file_content = resume_file.read()
            if resume_file.type == "application/pdf":
                resume_text = extract_text_from_pdf(file_content)
            elif resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                resume_text = extract_text_from_docx(file_content)
            else:
                resume_text = file_content.decode('utf-8')
    
    if st.button("Generate Analysis & Cover Letter", type="primary"):
        if not job_description or not resume_text:
            st.error("Both job description and resume text are required!")
        else:
            with st.spinner("Analyzing and generating content..."):
                # Get analysis (this will include cover letter suggestions)
                analysis_data = get_gemini_analysis(job_description, resume_text)
            
            if "error" not in analysis_data:
                st.success("Analysis completed successfully!")
                
                # Display results in tabs
                tab1, tab2, tab3 = st.tabs(["📊 Analysis Summary", "💡 Feedback", "✉️ Cover Letter Tips"])
                
                with tab1:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Relevance Score", f"{analysis_data['relevance_score']}%")
                    with col2:
                        st.metric("Fit Level", analysis_data['fit_verdict'])
                    with col3:
                        verdict_color = {
                            'High': '🟢',
                            'Medium': '🟡', 
                            'Low': '🔴'
                        }.get(analysis_data['fit_verdict'], '⚪')
                        st.metric("Status", f"{verdict_color} {analysis_data['fit_verdict']}")
                    
                    st.write("**Summary:**")
                    st.write(analysis_data['summary'])
                
                with tab2:
                    st.write("**Personalized Feedback:**")
                    st.write(analysis_data['personalized_feedback'])
                    
                    if analysis_data.get('missing_skills'):
                        st.write("**Skills to Highlight or Develop:**")
                        for skill in analysis_data['missing_skills']:
                            st.write(f"• {skill}")
                
                with tab3:
                    st.write("**Cover Letter Recommendations:**")
                    
                    # Generate cover letter tips based on analysis
                    if analysis_data['relevance_score'] >= 80:
                        st.success("🎯 **Strong Match - Highlight Your Strengths**")
                        st.write("""
                        Your profile aligns well with this role. In your cover letter:
                        - Lead with your most relevant achievements
                        - Quantify your impact with specific metrics
                        - Show enthusiasm for the company's mission
                        - Demonstrate knowledge of their recent developments
                        """)
                    elif analysis_data['relevance_score'] >= 65:
                        st.info("⚡ **Good Match - Bridge the Gaps**")
                        st.write("""
                        You have a solid foundation for this role. In your cover letter:
                        - Address any skill gaps with related experience
                        - Show your learning agility and growth mindset
                        - Highlight transferable skills from other domains
                        - Express genuine interest in developing missing skills
                        """)
                    else:
                        st.warning("🔧 **Developing Match - Focus on Potential**")
                        st.write("""
                        Focus on your potential and passion. In your cover letter:
                        - Emphasize your eagerness to learn and grow
                        - Highlight any relevant projects or coursework
                        - Show how your unique background brings value
                        - Demonstrate commitment to skill development
                        """)
                    
                    st.write("**Key Points to Include:**")
                    st.write("• Reference specific requirements from the job description")
                    st.write("• Use keywords from the job posting naturally")
                    st.write("• Tell a story about your relevant experience")
                    st.write("• Show genuine interest in the company and role")
                    st.write("• Keep it concise (3-4 paragraphs maximum)")
                    
                    # Suggested structure
                    with st.expander("📝 Cover Letter Structure Template"):
                        st.code("""
**Paragraph 1: Hook & Interest**
- State the position you're applying for
- Mention how you learned about the role
- Include a compelling hook about your background

**Paragraph 2: Relevant Experience**
- Highlight your most relevant achievements
- Use specific examples with quantifiable results
- Connect your experience to job requirements

**Paragraph 3: Company Connection**
- Show knowledge of the company
- Explain why you want to work there
- Mention how you can contribute to their goals

**Paragraph 4: Call to Action**
- Express enthusiasm for next steps
- Thank them for their consideration
- Provide your contact information
                        """, language='text')
            
            else:
                st.error(f"Analysis failed: {analysis_data.get('error', 'Unknown error')}")

# Footer
st.sidebar.divider()
st.sidebar.markdown("""
---
**Resume Match AI**  
Powered by Google Gemini  
Version 2.0 (Streamlit)
""")
