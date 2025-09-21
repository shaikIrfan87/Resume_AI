# app.py - Pure Streamlit Resume Matching System
import streamlit as st
import os
import json
import pandas as pd
import pdfplumber
import io
import re
from datetime import datetime
from pathlib import Path
from docx import Document
from database import (
    init_database, Job, Candidate, AnalysisResult, DatabaseManager
)
from services.gemini_service import get_gemini_analysis, extract_job_title
from services.email_service import (
    send_shortlist_email, send_bulk_shortlist_emails, 
    test_email_configuration, send_test_email
)

# --- Streamlit Configuration ---
st.set_page_config(
    page_title="Resume Matching System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Helper Functions ---
def extract_text_from_pdf(file_content):
    """Extracts text from a PDF file content."""
    try:
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return ""

def extract_text_from_docx(file_content):
    """Extracts text from a DOCX file content."""
    try:
        doc = Document(io.BytesIO(file_content))
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        st.error(f"Error extracting text from DOCX: {e}")
        return ""

def save_uploaded_file(uploaded_file, upload_folder="uploads"):
    """Save uploaded file and return filepath."""
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# --- Initialize Database ---
if 'db_initialized' not in st.session_state:
    init_database()
    st.session_state.db_initialized = True

# --- Sidebar Navigation ---
st.sidebar.title("🎯 Resume Match AI")
page = st.sidebar.selectbox(
    "Navigate to:",
    ["Home", "Dashboard", "Jobs", "Resumes", "Cover Letters", "Email Test"]
)

# --- Main App Logic ---
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
    stats = DatabaseManager.get_dashboard_stats()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Jobs", stats['total_jobs'])
    with col2:
        st.metric("Total Applications", stats['total_candidates'])
    with col3:
        st.metric("Shortlisted", stats['shortlisted_count'])

elif page == "Dashboard":
    st.title("📊 Dashboard")
    
    stats = DatabaseManager.get_dashboard_stats()
    
    if stats['jobs_stats']:
        # Convert to DataFrame for better display
        df = pd.DataFrame(stats['jobs_stats'])
        df = df.fillna(0)  # Replace NaN values
        
        # Display job statistics table
        st.subheader("Job Performance Overview")
        st.dataframe(df[['title', 'company', 'total_applicants', 'shortlisted_count', 'rejected_count', 'avg_score']], use_container_width=True)
        
        # Charts
        if len(df) > 0 and df['total_applicants'].sum() > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Applications by Job")
                chart_data = df[df['total_applicants'] > 0][['title', 'total_applicants']].set_index('title')
                if not chart_data.empty:
                    st.bar_chart(chart_data)
            
            with col2:
                st.subheader("Shortlisting Rate")
                df['shortlisting_rate'] = df.apply(lambda x: (x['shortlisted_count'] / x['total_applicants'] * 100) if x['total_applicants'] > 0 else 0, axis=1)
                rate_data = df[df['total_applicants'] > 0][['title', 'shortlisting_rate']].set_index('title')
                if not rate_data.empty:
                    st.bar_chart(rate_data)
    else:
        st.info("📊 No jobs found. Add some jobs first to see dashboard analytics.")

elif page == "Jobs":
    st.title("💼 Job Management")
    
    # Add new job section
    st.subheader("➕ Add New Job")
    
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
        
        submitted = st.form_submit_button("➕ Add Job", type="primary")
        
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
                st.error("⚠️ Company name and job description are required!")
            else:
                # Extract job title if not provided
                if not title:
                    with st.spinner("🧐 Extracting job title..."):
                        try:
                            title = extract_job_title(description)
                            if not title or 'no job title' in (title or '').lower():
                                title = f"Job Position {datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        except:
                            title = f"Job Position {datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Save to database
                try:
                    new_job = Job.create(title=title, company=company_name, description=description)
                    st.success(f"✅ Job '{title}' added successfully!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"❌ Error adding job: {str(e)}")
    
    st.divider()
    
    # Display existing jobs
    st.subheader("📁 Existing Jobs")
    
    jobs = Job.get_all()
    
    if jobs:
        for job in jobs:
            with st.expander(f"🏢 {job.title} at {job.company}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Job ID:** {job.id}")
                    st.write(f"**Description:**")
                    description_preview = job.description[:500] + "..." if len(job.description) > 500 else job.description
                    st.write(description_preview)
                
                with col2:
                    if st.button(f"🗑️ Delete", key=f"delete_{job.id}", type="secondary"):
                        if Job.delete(job.id):
                            st.success("✅ Job deleted successfully!")
                            st.experimental_rerun()
                        else:
                            st.error("❌ Error deleting job")
    else:
        st.info("🏢 No jobs added yet. Add your first job above!")

elif page == "Resumes":
    st.title("📄 Resume Analysis")
    
    # Get available jobs
    jobs = Job.get_all()
    
    if not jobs:
        st.warning("⚠️ No jobs available. Please add a job first in the Jobs section.")
        st.stop()
    
    # Job selection
    job_options = {f"{job.title} at {job.company}": job.id for job in jobs}
    selected_job_display = st.selectbox("🎯 Select Job for Analysis:", list(job_options.keys()))
    selected_job_id = job_options[selected_job_display]
    
    st.divider()
    
    # Resume upload section
    st.subheader("📎 Upload Resumes")
    uploaded_files = st.file_uploader(
        "Choose resume files", 
        type=['pdf'], 
        accept_multiple_files=True,
        help="Upload PDF resumes for analysis against the selected job"
    )
    
    if uploaded_files:
        if st.button("🔍 Analyze Resumes", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_files = len(uploaded_files)
            processed_count = 0
            
            # Get job details
            selected_job = Job.get_by_id(selected_job_id)
            
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"🔄 Processing {uploaded_file.name}...")
                progress_bar.progress((i + 1) / total_files)
                
                try:
                    # Extract text from PDF
                    file_content = uploaded_file.read()
                    resume_text = extract_text_from_pdf(file_content)
                    
                    if not resume_text:
                        st.warning(f"⚠️ Could not extract text from {uploaded_file.name}")
                        continue
                    
                    # Save file
                    file_path = save_uploaded_file(uploaded_file)
                    
                    # Create candidate name from filename
                    candidate_name = os.path.splitext(uploaded_file.name)[0].replace('_', ' ').replace('-', ' ').title()
                    
                    # Create candidate
                    candidate = Candidate.create(
                        name=candidate_name, 
                        resume_filename=uploaded_file.name, 
                        job_id=selected_job_id
                    )
                    
                    # Get AI analysis
                    status_text.text(f"🧠 Analyzing {candidate_name}...")
                    analysis_data = get_gemini_analysis(selected_job.description, resume_text)
                    
                    if "error" not in analysis_data:
                        # Save analysis result
                        AnalysisResult.create(
                            score=analysis_data.get('relevance_score'),
                            verdict=analysis_data.get('fit_verdict'),
                            summary=analysis_data.get('summary'),
                            feedback=analysis_data.get('personalized_feedback'),
                            missing_skills=analysis_data.get('missing_skills', []),
                            candidate_id=candidate.id
                        )
                        processed_count += 1
                    else:
                        st.error(f"❌ Analysis failed for {candidate_name}: {analysis_data.get('error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                    continue
            
            status_text.text("✅ Analysis complete!")
            st.success(f"🎉 Successfully processed {processed_count} out of {total_files} resumes.")
            st.experimental_rerun()
    
    st.divider()
    
    # Display results for selected job
    st.subheader(f"📈 Analysis Results for: {selected_job_display}")
    
    results = DatabaseManager.get_candidates_with_analysis(selected_job_id)
    
    if results:
        # Show summary statistics
        analyzed_results = [r for r in results if r['score'] is not None]
        if analyzed_results:
            scores = [r['score'] for r in analyzed_results]
            shortlisted = [r for r in analyzed_results if r['score'] >= 65]
            
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
            if result['score'] is not None:
                # Color coding based on score
                if result['score'] >= 85:
                    score_color = "🟢"
                elif result['score'] >= 65:
                    score_color = "🟡"
                else:
                    score_color = "🔴"
                
                with st.expander(f"{score_color} {result['name']} - Score: {result['score']}% ({result['verdict']})", expanded=result['score'] >= 65):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Summary:** {result['summary']}")
                        st.write(f"**Feedback:** {result['feedback']}")
                        
                        if result['missing_skills']:
                            st.write(f"**Missing Skills:** {', '.join(result['missing_skills'])}")
                    
                    with col2:
                        st.write(f"**File:** {result['resume_filename']}")
                        st.write(f"**Score:** {result['score']}%")
                        st.write(f"**Verdict:** {result['verdict']}")
                        
                        # Email management
                        current_email = result['email'] or ""
                        new_email = st.text_input(
                            "Email:", 
                            value=current_email, 
                            key=f"email_{result['id']}",
                            placeholder="candidate@email.com"
                        )
                        
                        if new_email != current_email and new_email.strip():
                            if st.button(f"Update Email", key=f"update_{result['id']}"):
                                candidate = Candidate.get_by_id(result['id'])
                                if candidate and candidate.update_email(new_email):
                                    st.success("✅ Email updated!")
                                    st.experimental_rerun()
                                else:
                                    st.error("❌ Error updating email")
            else:
                with st.expander(f"⚪ {result['name']} - Not analyzed yet"):
                    st.info(f"Resume '{result['resume_filename']}' is uploaded but not analyzed yet.")
        
        # Shortlisted candidates email section
        shortlisted_candidates = [r for r in results if r['score'] and r['score'] >= 65 and r['email']]
        if shortlisted_candidates:
            st.divider()
            st.subheader("📧 Send Shortlist Emails")
            
            selected_candidates = st.multiselect(
                "Select candidates to email:",
                options=[{"id": r['id'], "display": f"{r['name']} ({r['score']}%)"} for r in shortlisted_candidates],
                format_func=lambda x: x["display"]
            )
            
            if selected_candidates and st.button("📧 Send Shortlist Emails", type="primary"):
                selected_job = Job.get_by_id(selected_job_id)
                
                # Prepare email data
                candidates_data = []
                for candidate_selection in selected_candidates:
                    result = next(r for r in shortlisted_candidates if r['id'] == candidate_selection['id'])
                    candidates_data.append({
                        'name': result['name'],
                        'email': result['email'],
                        'job_title': selected_job.title,
                        'company_name': selected_job.company
                    })
                
                # Send emails
                with st.spinner("📧 Sending emails..."):
                    results = send_bulk_shortlist_emails(candidates_data)
                
                successful_sends = [r for r in results if r['status']['success']]
                failed_sends = [r for r in results if not r['status']['success']]
                
                if successful_sends:
                    st.success(f"✅ Successfully sent emails to {len(successful_sends)} candidates:")
                    for result in successful_sends:
                        st.write(f"- {result['candidate']} ({result['email']})")
                
                if failed_sends:
                    st.error(f"❌ Failed to send emails to {len(failed_sends)} candidates:")
                    for result in failed_sends:
                        st.write(f"- {result['candidate']}: {result['status']['message']}")
    else:
        st.info("📄 No candidates uploaded for this job yet.")

elif page == "Cover Letters":
    st.title("✉️ Cover Letter Generator")
    
    st.markdown("""
    🎆 Generate personalized cover letters using AI analysis of job descriptions and candidate resumes.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💼 Job Description")
        job_description = st.text_area(
            "Paste job description here:",
            height=300,
            placeholder="Enter the complete job description..."
        )
    
    with col2:
        st.subheader("📄 Resume/Candidate Profile")
        resume_text = st.text_area(
            "Paste resume content here:",
            height=300,
            placeholder="Enter the candidate's resume content..."
        )
    
    # Alternative: Upload files
    st.divider()
    st.subheader("📁 Or Upload Files")
    
    col1, col2 = st.columns(2)
    with col1:
        jd_file = st.file_uploader("📎 Upload Job Description", type=['pdf', 'docx', 'txt'])
        if jd_file:
            file_content = jd_file.read()
            if jd_file.type == "application/pdf":
                job_description = extract_text_from_pdf(file_content)
            elif jd_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                job_description = extract_text_from_docx(file_content)
            else:
                job_description = file_content.decode('utf-8')
            st.text_area("Extracted Job Description:", value=job_description, height=100, disabled=True)
    
    with col2:
        resume_file = st.file_uploader("📄 Upload Resume", type=['pdf', 'docx', 'txt'])
        if resume_file:
            file_content = resume_file.read()
            if resume_file.type == "application/pdf":
                resume_text = extract_text_from_pdf(file_content)
            elif resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                resume_text = extract_text_from_docx(file_content)
            else:
                resume_text = file_content.decode('utf-8')
            st.text_area("Extracted Resume Text:", value=resume_text, height=100, disabled=True)
    
    if st.button("🚀 Generate Analysis & Cover Letter Tips", type="primary"):
        if not job_description or not resume_text:
            st.error("⚠️ Both job description and resume text are required!")
        else:
            with st.spinner("🧠 Analyzing and generating content..."):
                analysis_data = get_gemini_analysis(job_description, resume_text)
            
            if "error" not in analysis_data:
                st.success("✅ Analysis completed successfully!")
                
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
                st.error(f"❌ Analysis failed: {analysis_data.get('error', 'Unknown error')}")

elif page == "Email Test":
    st.title("📧 Email Configuration Test")
    
    st.markdown("""
    🔧 Test your email configuration to ensure shortlist notifications work properly.
    """)
    
    # Test email configuration
    st.subheader("⚙️ Configuration Status")
    config_test = test_email_configuration()
    
    if config_test['success']:
        st.success(f"✅ {config_test['message']}")
        
        with st.expander("🔍 View Email Configuration"):
            st.json(config_test['config'])
        
        # Send test email
        st.subheader("📧 Send Test Email")
        test_email_address = st.text_input(
            "Test Email Address:",
            placeholder="your-test-email@example.com",
            help="Enter an email address to receive a test shortlist notification"
        )
        
        if st.button("🚀 Send Test Email", type="primary"):
            if test_email_address:
                with st.spinner("📧 Sending test email..."):
                    result = send_test_email(test_email_address)
                
                if result['success']:
                    st.success(f"✅ {result['message']}")
                    st.balloons()
                else:
                    st.error(f"❌ {result['message']}")
            else:
                st.error("⚠️ Please enter a test email address")
    else:
        st.error(f"❌ {config_test['message']}")
        if 'instructions' in config_test:
            st.info(f"💡 {config_test['instructions']}")
        
        st.subheader("📝 Email Setup Instructions")
        st.markdown("""
        To enable email functionality, update your `.env` file with:
        
        ```
        MAIL_SERVER=smtp.gmail.com
        MAIL_PORT=587
        MAIL_USE_TLS=true
        MAIL_USERNAME=your-email@gmail.com
        MAIL_PASSWORD=your-app-password
        MAIL_DEFAULT_SENDER=your-email@gmail.com
        ```
        
        **For Gmail:**
        1. Enable 2-factor authentication
        2. Generate an App Password (not your regular password)
        3. Use the App Password in the MAIL_PASSWORD field
        """)

# Footer
st.sidebar.divider()
st.sidebar.markdown("""
---
**Resume Match AI**  
💻 Pure Streamlit Version  
🤖 Powered by Google Gemini AI
""")

# --- Main Execution ---
if __name__ == "__main__":
    # This section runs when the script is executed directly
    # Streamlit handles the execution automatically
    pass
