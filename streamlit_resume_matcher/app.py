# app.py - Streamlit Resume Matching System with Flask-like Design
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
import plotly.express as px
import plotly.graph_objects as go
from database import (
    init_database, Job, Candidate, AnalysisResult, DatabaseManager
)
from services.gemini_service import get_gemini_analysis, extract_job_title
from services.email_service import (
    send_shortlist_email, send_bulk_shortlist_emails, 
    test_email_configuration, send_test_email
)

# Page configuration
st.set_page_config(
    page_title="Resume Matching System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to match Flask frontend design
def load_custom_css():
    st.markdown("""
    <style>
    /* Main container styling */
    .main-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: white;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #7f5af0, #ff5470);
        padding: 30px;
        text-align: center;
        border-radius: 10px;
        color: white;
        margin-bottom: 30px;
    }
    
    /* Card styling */
    .card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        border-left: 4px solid #7f5af0;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #7f5af0, #ff5470);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(127, 90, 240, 0.4);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Success message styling */
    .success-card {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    /* Error message styling */
    .error-card {
        background: linear-gradient(135deg, #f44336, #d32f2f);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    /* Stats card styling */
    .stats-card {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    
    /* Navigation styling */
    .nav-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    /* Form styling */
    .form-container {
        background: #f8f9fa;
        padding: 25px;
        border-radius: 10px;
        margin: 20px 0;
        border: 1px solid #e9ecef;
    }
    
    /* Progress bar styling */
    .progress-container {
        background: white;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Score indicators */
    .score-high { 
        color: #4CAF50; 
        font-weight: bold; 
        background: #e8f5e8; 
        padding: 5px 10px; 
        border-radius: 5px; 
    }
    .score-medium { 
        color: #FF9800; 
        font-weight: bold; 
        background: #fff3e0; 
        padding: 5px 10px; 
        border-radius: 5px; 
    }
    .score-low { 
        color: #f44336; 
        font-weight: bold; 
        background: #ffebee; 
        padding: 5px 10px; 
        border-radius: 5px; 
    }
    
    /* Table styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Upload area styling */
    .upload-area {
        border: 2px dashed #7f5af0;
        border-radius: 10px;
        padding: 30px;
        text-align: center;
        background: #fafafa;
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Helper Functions
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

def create_header(title, subtitle=""):
    """Create a styled header matching Flask design"""
    st.markdown(f"""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">{title}</h1>
        {f'<p style="margin: 10px 0 0 0; font-size: 1.2rem; opacity: 0.9;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

def create_stats_card(title, value, icon="📊"):
    """Create a stats card with styling"""
    return f"""
    <div class="stats-card">
        <h3 style="margin: 0; font-size: 1.1rem;">{icon} {title}</h3>
        <h2 style="margin: 10px 0 0 0; font-size: 2.2rem; font-weight: bold;">{value}</h2>
    </div>
    """

def create_card_container(content):
    """Create a card container"""
    st.markdown(f'<div class="card">{content}</div>', unsafe_allow_html=True)

# Load custom CSS
load_custom_css()

# Initialize database
if 'db_initialized' not in st.session_state:
    init_database()
    st.session_state.db_initialized = True

# Sidebar Navigation with styling
st.markdown('<div class="nav-header"><h2>🎯 Resume Match AI</h2></div>', unsafe_allow_html=True)

page = st.sidebar.selectbox(
    "Navigate to:",
    ["🏠 Home", "📊 Dashboard", "💼 Jobs", "📄 Resumes", "✉️ Cover Letters", "📧 Email Test"],
    format_func=lambda x: x
)

# Main App Logic
if page == "🏠 Home":
    create_header("Resume Matching System", "AI-Powered Recruitment Solution")
    
    st.markdown("""
    <div class="card">
        <h3>🚀 Welcome to the AI-Powered Resume Matching System!</h3>
        <p>This intelligent system revolutionizes your recruitment process with cutting-edge AI technology:</p>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0;">
            <div style="background: #f8f9ff; padding: 20px; border-radius: 8px; border-left: 4px solid #7f5af0;">
                <h4>📝 Smart Job Management</h4>
                <p>Upload and organize job postings with automatic title extraction</p>
            </div>
            <div style="background: #f0fff4; padding: 20px; border-radius: 8px; border-left: 4px solid #4CAF50;">
                <h4>📄 Intelligent Analysis</h4>
                <p>AI-powered resume analysis with detailed scoring and feedback</p>
            </div>
            <div style="background: #fffaf0; padding: 20px; border-radius: 8px; border-left: 4px solid #FF9800;">
                <h4>🎯 Precise Matching</h4>
                <p>Advanced relevance scoring with skill gap analysis</p>
            </div>
            <div style="background: #fff0f5; padding: 20px; border-radius: 8px; border-left: 4px solid #ff5470;">
                <h4>📧 Auto Notifications</h4>
                <p>Automated email notifications for shortlisted candidates</p>
            </div>
        </div>
        
        <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h4>🎯 Getting Started:</h4>
            <ol style="margin: 10px 0; padding-left: 20px;">
                <li>Add job descriptions in the <strong>Jobs</strong> section</li>
                <li>Upload candidate resumes in the <strong>Resumes</strong> section</li>
                <li>View comprehensive analytics in the <strong>Dashboard</strong></li>
                <li>Generate cover letter tips in the <strong>Cover Letters</strong> section</li>
            </ol>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick stats with enhanced styling
    st.markdown('<h3 style="text-align: center; margin: 30px 0;">📈 System Overview</h3>', unsafe_allow_html=True)
    
    stats = DatabaseManager.get_dashboard_stats()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(create_stats_card("Total Jobs", stats['total_jobs'], "💼"), unsafe_allow_html=True)
    with col2:
        st.markdown(create_stats_card("Applications", stats['total_candidates'], "📄"), unsafe_allow_html=True)
    with col3:
        st.markdown(create_stats_card("Shortlisted", stats['shortlisted_count'], "⭐"), unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 10px;">
        <p style="margin: 0; color: #666; font-style: italic;">Powered by Google Gemini AI for intelligent resume analysis</p>
    </div>
    """, unsafe_allow_html=True)

elif page == "📊 Dashboard":
    create_header("Analytics Dashboard", "Comprehensive Recruitment Insights")
    
    stats = DatabaseManager.get_dashboard_stats()
    
    if stats['jobs_stats']:
        # Enhanced statistics cards
        col1, col2, col3, col4 = st.columns(4)
        
        total_apps = sum(job['total_applicants'] for job in stats['jobs_stats'])
        total_shortlisted = sum(job['shortlisted_count'] for job in stats['jobs_stats'])
        total_rejected = sum(job['rejected_count'] for job in stats['jobs_stats'])
        avg_success_rate = (total_shortlisted / total_apps * 100) if total_apps > 0 else 0
        
        with col1:
            st.markdown(create_stats_card("Total Jobs", stats['total_jobs'], "💼"), unsafe_allow_html=True)
        with col2:
            st.markdown(create_stats_card("Applications", total_apps, "📄"), unsafe_allow_html=True)
        with col3:
            st.markdown(create_stats_card("Shortlisted", total_shortlisted, "⭐"), unsafe_allow_html=True)
        with col4:
            st.markdown(create_stats_card("Success Rate", f"{avg_success_rate:.1f}%", "📈"), unsafe_allow_html=True)
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(stats['jobs_stats'])
        df = df.fillna(0)
        
        # Job performance table with enhanced styling
        st.markdown('<div class="card"><h3>📋 Job Performance Overview</h3></div>', unsafe_allow_html=True)
        
        # Create styled dataframe
        display_df = df[['title', 'company', 'total_applicants', 'shortlisted_count', 'rejected_count', 'avg_score']].copy()
        display_df.columns = ['Job Title', 'Company', 'Total Apps', 'Shortlisted', 'Rejected', 'Avg Score']
        display_df['Avg Score'] = display_df['Avg Score'].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) and x > 0 else "N/A")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=300
        )
        
        # Enhanced charts
        if len(df) > 0 and df['total_applicants'].sum() > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="card"><h4>📊 Applications by Job</h4></div>', unsafe_allow_html=True)
                apps_data = df[df['total_applicants'] > 0]
                if not apps_data.empty:
                    fig = px.bar(
                        apps_data, 
                        x='title', 
                        y='total_applicants',
                        title='',
                        color='total_applicants',
                        color_continuous_scale='viridis'
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=12)
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown('<div class="card"><h4>🎯 Shortlisting Performance</h4></div>', unsafe_allow_html=True)
                df['shortlisting_rate'] = df.apply(
                    lambda x: (x['shortlisted_count'] / x['total_applicants'] * 100) if x['total_applicants'] > 0 else 0, 
                    axis=1
                )
                rate_data = df[df['total_applicants'] > 0]
                if not rate_data.empty:
                    fig = px.bar(
                        rate_data, 
                        x='title', 
                        y='shortlisting_rate',
                        title='',
                        color='shortlisting_rate',
                        color_continuous_scale='RdYlGn'
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=12)
                    )
                    fig.update_yaxis(title='Success Rate (%)')
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: #f8f9fa; border-radius: 10px; border: 2px dashed #ddd;">
            <h3>📊 No Data Available</h3>
            <p>Add some jobs and upload resumes to see comprehensive analytics here.</p>
            <a href="#" style="color: #7f5af0; text-decoration: none;">Get started with your first job →</a>
        </div>
        """, unsafe_allow_html=True)

elif page == "💼 Jobs":
    create_header("Job Management", "Create and Manage Job Postings")
    
    # Add new job section with enhanced styling
    st.markdown("""
    <div class="form-container">
        <h3>➕ Add New Job Posting</h3>
        <p>Upload job descriptions or paste them directly. Our AI will automatically extract the job title.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("add_job_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input(
                "🏢 Company Name *", 
                placeholder="e.g., Tech Solutions Inc.",
                help="Enter the company name for this position"
            )
            job_title = st.text_input(
                "💼 Job Title", 
                placeholder="Will be auto-extracted if empty",
                help="Leave empty to auto-extract from job description"
            )
        
        with col2:
            job_description = st.text_area(
                "📝 Job Description *", 
                height=150,
                placeholder="Paste the complete job description here...",
                help="Enter the full job description with requirements and responsibilities"
            )
        
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "📎 Or Upload Job Description File", 
            type=['pdf', 'docx'],
            help="Upload PDF or DOCX file containing job description"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button("➕ Add Job Posting", type="primary", use_container_width=True)
        
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
                st.markdown('<div class="error-card">⚠️ Company name and job description are required!</div>', unsafe_allow_html=True)
            else:
                # Extract job title if not provided
                if not title:
                    with st.spinner("🧐 Extracting job title using AI..."):
                        try:
                            title = extract_job_title(description)
                            if not title or 'no job title' in (title or '').lower():
                                title = f"Job Position {datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        except:
                            title = f"Job Position {datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Save to database
                try:
                    new_job = Job.create(title=title, company=company_name, description=description)
                    st.markdown(f'<div class="success-card">✅ Job "{title}" added successfully!</div>', unsafe_allow_html=True)
                    st.success("Job added! Refreshing page...")
                    st.experimental_rerun()
                except Exception as e:
                    st.markdown(f'<div class="error-card">❌ Error adding job: {str(e)}</div>', unsafe_allow_html=True)
    
    # Display existing jobs with enhanced cards
    st.markdown('<h3 style="margin-top: 40px;">📁 Existing Job Postings</h3>', unsafe_allow_html=True)
    
    jobs = Job.get_all()
    
    if jobs:
        for i, job in enumerate(jobs):
            # Create job card with styling
            st.markdown(f"""
            <div class="card" style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: between; align-items: center;">
                    <div style="flex-grow: 1;">
                        <h4 style="margin: 0; color: #333;">🏢 {job.title}</h4>
                        <p style="margin: 5px 0; color: #666; font-weight: 500;">{job.company}</p>
                        <p style="margin: 10px 0; color: #555;">Job ID: {job.id}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"View Details - {job.title}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write("**Job Description:**")
                    description_preview = job.description[:800] + "..." if len(job.description) > 800 else job.description
                    st.write(description_preview)
                
                with col2:
                    if st.button(f"🗑️ Delete Job", key=f"delete_{job.id}", type="secondary"):
                        if Job.delete(job.id):
                            st.success("✅ Job deleted successfully!")
                            st.experimental_rerun()
                        else:
                            st.error("❌ Error deleting job")
    else:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: #f8f9fa; border-radius: 10px; border: 2px dashed #ddd;">
            <h3>💼 No Jobs Posted Yet</h3>
            <p>Create your first job posting using the form above to get started with candidate matching.</p>
        </div>
        """, unsafe_allow_html=True)

elif page == "📄 Resumes":
    create_header("Resume Analysis", "AI-Powered Candidate Evaluation")
    
    # Get available jobs
    jobs = Job.get_all()
    
    if not jobs:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: #fff3cd; border-radius: 10px; border: 2px solid #ffeaa7;">
            <h3>⚠️ No Jobs Available</h3>
            <p>Please add a job first in the Jobs section before analyzing resumes.</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    
    # Job selection with enhanced styling
    st.markdown('<div class="form-container"><h4>🎯 Select Job for Analysis</h4></div>', unsafe_allow_html=True)
    job_options = {f"{job.title} at {job.company}": job.id for job in jobs}
    selected_job_display = st.selectbox("Choose the job position:", list(job_options.keys()))
    selected_job_id = job_options[selected_job_display]
    
    # Resume upload section
    st.markdown("""
    <div class="form-container">
        <h3>📎 Upload Resume Files</h3>
        <p>Upload multiple PDF resumes for batch analysis against the selected job position.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="upload-area">', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Choose resume files", 
        type=['pdf'], 
        accept_multiple_files=True,
        help="Upload PDF resumes for analysis against the selected job"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_files:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔍 Analyze All Resumes", type="primary", use_container_width=True):
                # Progress tracking with enhanced styling
                st.markdown('<div class="progress-container">', unsafe_allow_html=True)
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total_files = len(uploaded_files)
                processed_count = 0
                
                # Get job details
                selected_job = Job.get_by_id(selected_job_id)
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.markdown(f'<p style="text-align: center; margin: 10px 0;">🔄 Processing <strong>{uploaded_file.name}</strong>...</p>', unsafe_allow_html=True)
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
                        status_text.markdown(f'<p style="text-align: center; margin: 10px 0;">🧠 Analyzing <strong>{candidate_name}</strong>...</p>', unsafe_allow_html=True)
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
                
                status_text.markdown('<p style="text-align: center; margin: 10px 0; color: green; font-weight: bold;">✅ Analysis Complete!</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="success-card">🎉 Successfully analyzed {processed_count} out of {total_files} resumes!</div>', unsafe_allow_html=True)
                st.experimental_rerun()
    
    # Display results with enhanced styling
    st.markdown(f'<h3 style="margin-top: 40px;">📈 Analysis Results for: {selected_job_display}</h3>', unsafe_allow_html=True)
    
    results = DatabaseManager.get_candidates_with_analysis(selected_job_id)
    
    if results:
        # Enhanced summary statistics
        analyzed_results = [r for r in results if r['score'] is not None]
        if analyzed_results:
            scores = [r['score'] for r in analyzed_results]
            shortlisted = [r for r in analyzed_results if r['score'] >= 65]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(create_stats_card("Total", len(results), "👥"), unsafe_allow_html=True)
            with col2:
                st.markdown(create_stats_card("Analyzed", len(analyzed_results), "🔍"), unsafe_allow_html=True)
            with col3:
                st.markdown(create_stats_card("Shortlisted", len(shortlisted), "⭐"), unsafe_allow_html=True)
            with col4:
                avg_score = sum(scores)/len(scores) if scores else 0
                st.markdown(create_stats_card("Avg Score", f"{avg_score:.1f}%", "📊"), unsafe_allow_html=True)
        
        # Display individual results with enhanced cards
        for result in results:
            if result['score'] is not None:
                # Enhanced score color coding
                if result['score'] >= 85:
                    score_color = "🟢"
                    score_class = "score-high"
                elif result['score'] >= 65:
                    score_color = "🟡"
                    score_class = "score-medium"
                else:
                    score_color = "🔴"
                    score_class = "score-low"
                
                # Create candidate card
                st.markdown(f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <h4 style="margin: 0; color: #333;">{score_color} {result['name']}</h4>
                        <span class="{score_class}">{result['score']}% - {result['verdict']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"View Details - {result['name']}", expanded=result['score'] >= 65):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("**📋 Summary:**")
                        st.write(result['summary'])
                        st.markdown("**💡 Feedback:**")
                        st.write(result['feedback'])
                        
                        if result['missing_skills']:
                            st.markdown("**🎯 Skills to Develop:**")
                            skills_html = "".join([f'<span style="background: #f1f3f4; padding: 3px 8px; margin: 2px; border-radius: 15px; font-size: 0.9em;">{skill}</span> ' for skill in result['missing_skills']])
                            st.markdown(skills_html, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("**📄 File Information:**")
                        st.write(f"File: {result['resume_filename']}")
                        st.write(f"Score: {result['score']}%")
                        st.write(f"Verdict: {result['verdict']}")
                        
                        # Email management with styling
                        st.markdown("**📧 Contact Information:**")
                        current_email = result['email'] or ""
                        new_email = st.text_input(
                            "Email Address:", 
                            value=current_email, 
                            key=f"email_{result['id']}",
                            placeholder="candidate@email.com"
                        )
                        
                        if new_email != current_email and new_email.strip():
                            if st.button(f"📧 Update Email", key=f"update_{result['id']}", type="secondary"):
                                candidate = Candidate.get_by_id(result['id'])
                                if candidate and candidate.update_email(new_email):
                                    st.success("✅ Email updated!")
                                    st.experimental_rerun()
                                else:
                                    st.error("❌ Error updating email")
            else:
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #dee2e6; margin: 10px 0;">
                    <h5 style="margin: 0; color: #6c757d;">⚪ {result['name']} - Pending Analysis</h5>
                    <p style="margin: 5px 0 0 0; color: #6c757d;">Resume uploaded but analysis not completed yet.</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Enhanced email section
        shortlisted_candidates = [r for r in results if r['score'] and r['score'] >= 65 and r['email']]
        if shortlisted_candidates:
            st.markdown("""
            <div class="form-container" style="margin-top: 40px;">
                <h3>📧 Send Shortlist Notifications</h3>
                <p>Send professional email notifications to shortlisted candidates.</p>
            </div>
            """, unsafe_allow_html=True)
            
            selected_candidates = st.multiselect(
                "Select candidates to notify:",
                options=[{"id": r['id'], "display": f"{r['name']} ({r['score']}% - {r['email']})", "name": r['name'], "email": r['email']} for r in shortlisted_candidates],
                format_func=lambda x: x["display"]
            )
            
            if selected_candidates:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("📧 Send Notification Emails", type="primary", use_container_width=True):
                        selected_job = Job.get_by_id(selected_job_id)
                        
                        # Prepare email data
                        candidates_data = []
                        for candidate_selection in selected_candidates:
                            candidates_data.append({
                                'name': candidate_selection['name'],
                                'email': candidate_selection['email'],
                                'job_title': selected_job.title,
                                'company_name': selected_job.company
                            })
                        
                        # Send emails with progress indicator
                        with st.spinner("📧 Sending notification emails..."):
                            results_email = send_bulk_shortlist_emails(candidates_data)
                        
                        successful_sends = [r for r in results_email if r['status']['success']]
                        failed_sends = [r for r in results_email if not r['status']['success']]
                        
                        if successful_sends:
                            st.markdown(f'<div class="success-card">✅ Successfully sent emails to {len(successful_sends)} candidates!</div>', unsafe_allow_html=True)
                            for result in successful_sends[:3]:  # Show first 3
                                st.write(f"📧 {result['candidate']} ({result['email']})")
                            if len(successful_sends) > 3:
                                st.write(f"... and {len(successful_sends) - 3} more")
                        
                        if failed_sends:
                            st.markdown(f'<div class="error-card">❌ Failed to send emails to {len(failed_sends)} candidates</div>', unsafe_allow_html=True)
                            for result in failed_sends:
                                st.write(f"❌ {result['candidate']}: {result['status']['message']}")
    else:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: #f8f9fa; border-radius: 10px; border: 2px dashed #ddd;">
            <h3>📄 No Candidates Yet</h3>
            <p>Upload some resumes for this job position to see analysis results here.</p>
        </div>
        """, unsafe_allow_html=True)

elif page == "✉️ Cover Letters":
    create_header("Cover Letter Generator", "AI-Powered Career Guidance")
    
    st.markdown("""
    <div class="card">
        <h3>🎆 Personalized Cover Letter Assistant</h3>
        <p>Get AI-powered insights and recommendations for creating compelling cover letters tailored to specific job descriptions and candidate profiles.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Input sections with enhanced styling
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="form-container"><h4>💼 Job Description</h4></div>', unsafe_allow_html=True)
        job_description = st.text_area(
            "Paste job description here:",
            height=300,
            placeholder="Enter the complete job description with requirements, responsibilities, and company information..."
        )
    
    with col2:
        st.markdown('<div class="form-container"><h4>📄 Candidate Resume</h4></div>', unsafe_allow_html=True)
        resume_text = st.text_area(
            "Paste resume content here:",
            height=300,
            placeholder="Enter the candidate's resume content, experience, skills, and achievements..."
        )
    
    # Enhanced file upload section
    st.markdown("""
    <div class="form-container">
        <h4>📁 Alternative: Upload Documents</h4>
        <p>Upload files if you prefer not to copy-paste the content.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="upload-area" style="margin: 10px; padding: 20px;">', unsafe_allow_html=True)
        jd_file = st.file_uploader("📎 Upload Job Description", type=['pdf', 'docx', 'txt'])
        if jd_file:
            file_content = jd_file.read()
            if jd_file.type == "application/pdf":
                job_description = extract_text_from_pdf(file_content)
            elif jd_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                job_description = extract_text_from_docx(file_content)
            else:
                job_description = file_content.decode('utf-8')
            st.success(f"✅ Extracted text from {jd_file.name}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="upload-area" style="margin: 10px; padding: 20px;">', unsafe_allow_html=True)
        resume_file = st.file_uploader("📄 Upload Resume", type=['pdf', 'docx', 'txt'])
        if resume_file:
            file_content = resume_file.read()
            if resume_file.type == "application/pdf":
                resume_text = extract_text_from_pdf(file_content)
            elif resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                resume_text = extract_text_from_docx(file_content)
            else:
                resume_text = file_content.decode('utf-8')
            st.success(f"✅ Extracted text from {resume_file.name}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Generate analysis button with enhanced styling
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Generate Analysis & Recommendations", type="primary", use_container_width=True):
            if not job_description or not resume_text:
                st.markdown('<div class="error-card">⚠️ Both job description and resume content are required!</div>', unsafe_allow_html=True)
            else:
                with st.spinner("🧠 Analyzing compatibility and generating personalized recommendations..."):
                    analysis_data = get_gemini_analysis(job_description, resume_text)
                
                if "error" not in analysis_data:
                    st.markdown('<div class="success-card">✅ Analysis completed successfully!</div>', unsafe_allow_html=True)
                    
                    # Enhanced results display with tabs
                    tab1, tab2, tab3, tab4 = st.tabs(["📊 Compatibility Analysis", "💡 Personalized Feedback", "✉️ Cover Letter Strategy", "📝 Writing Template"])
                    
                    with tab1:
                        # Enhanced metrics display
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            score_color = "#4CAF50" if analysis_data['relevance_score'] >= 80 else "#FF9800" if analysis_data['relevance_score'] >= 65 else "#f44336"
                            st.markdown(f"""
                            <div style="background: {score_color}; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                                <h3 style="margin: 0;">Relevance Score</h3>
                                <h1 style="margin: 10px 0 0 0; font-size: 3rem;">{analysis_data['relevance_score']}%</h1>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            verdict_colors = {'High': '#4CAF50', 'Medium': '#FF9800', 'Low': '#f44336'}
                            verdict_color = verdict_colors.get(analysis_data['fit_verdict'], '#6c757d')
                            st.markdown(f"""
                            <div style="background: {verdict_color}; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                                <h3 style="margin: 0;">Fit Level</h3>
                                <h2 style="margin: 10px 0 0 0; font-size: 2rem;">{analysis_data['fit_verdict']}</h2>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col3:
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                                <h3 style="margin: 0;">Match Status</h3>
                                <h2 style="margin: 10px 0 0 0; font-size: 1.5rem;">{'🟢 Strong' if analysis_data['relevance_score'] >= 80 else '🟡 Good' if analysis_data['relevance_score'] >= 65 else '🔴 Developing'}</h2>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown('<div class="card"><h4>📋 Summary Analysis</h4>', unsafe_allow_html=True)
                        st.write(analysis_data['summary'])
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with tab2:
                        st.markdown('<div class="card"><h4>💡 Personalized Development Feedback</h4>', unsafe_allow_html=True)
                        st.write(analysis_data['personalized_feedback'])
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        if analysis_data.get('missing_skills'):
                            st.markdown('<div class="card"><h4>🎯 Key Skills to Highlight or Develop</h4>', unsafe_allow_html=True)
                            for i, skill in enumerate(analysis_data['missing_skills'], 1):
                                st.markdown(f"**{i}.** {skill}")
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    with tab3:
                        st.markdown('<div class="card"><h4>✉️ Cover Letter Strategy & Recommendations</h4>', unsafe_allow_html=True)
                        
                        # Personalized strategy based on score
                        if analysis_data['relevance_score'] >= 80:
                            st.markdown("""
                            <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; border-left: 4px solid #4CAF50; margin: 15px 0;">
                                <h4 style="color: #4CAF50; margin: 0 0 10px 0;">🎯 Strong Match Strategy</h4>
                                <p><strong>Your profile aligns excellently with this role!</strong></p>
                                <ul>
                                    <li>Lead with your most impressive and relevant achievements</li>
                                    <li>Use specific metrics and quantifiable results</li>
                                    <li>Show genuine enthusiasm for the company's mission and values</li>
                                    <li>Demonstrate knowledge of recent company developments or industry trends</li>
                                    <li>Position yourself as someone who can make an immediate impact</li>
                                </ul>
                            </div>
                            """)
                        elif analysis_data['relevance_score'] >= 65:
                            st.markdown("""
                            <div style="background: #fff3e0; padding: 20px; border-radius: 8px; border-left: 4px solid #FF9800; margin: 15px 0;">
                                <h4 style="color: #FF9800; margin: 0 0 10px 0;">⚡ Good Match Strategy</h4>
                                <p><strong>You have a solid foundation - focus on bridging any gaps!</strong></p>
                                <ul>
                                    <li>Address skill gaps by highlighting related or transferable experience</li>
                                    <li>Emphasize your learning agility and adaptability</li>
                                    <li>Show specific examples of how you've quickly mastered new skills</li>
                                    <li>Express genuine interest in developing the missing competencies</li>
                                    <li>Highlight unique perspectives or experiences you bring</li>
                                </ul>
                            </div>
                            """)
                        else:
                            st.markdown("""
                            <div style="background: #ffebee; padding: 20px; border-radius: 8px; border-left: 4px solid #f44336; margin: 15px 0;">
                                <h4 style="color: #f44336; margin: 0 0 10px 0;">🔧 Growth-Focused Strategy</h4>
                                <p><strong>Focus on your potential, passion, and unique value!</strong></p>
                                <ul>
                                    <li>Emphasize your eagerness to learn and grow in this field</li>
                                    <li>Highlight relevant projects, coursework, or self-directed learning</li>
                                    <li>Show how your diverse background brings fresh perspectives</li>
                                    <li>Demonstrate genuine passion for the industry or role</li>
                                    <li>Provide examples of how you've successfully tackled challenges outside your comfort zone</li>
                                </ul>
                            </div>
                            """)
                        
                        st.markdown("""
                        <h4>📝 Essential Cover Letter Elements:</h4>
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 10px 0;">
                            <ul>
                                <li><strong>Compelling Opening:</strong> Reference the specific position and grab attention immediately</li>
                                <li><strong>Keyword Integration:</strong> Naturally incorporate important terms from the job description</li>
                                <li><strong>Storytelling:</strong> Use specific examples and narratives to illustrate your points</li>
                                <li><strong>Company Research:</strong> Show you've done your homework about the organization</li>
                                <li><strong>Call to Action:</strong> End with enthusiasm for next steps and clear contact information</li>
                                <li><strong>Professional Tone:</strong> Match the company's communication style and culture</li>
                            </ul>
                        </div>
                        """)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with tab4:
                        st.markdown('<div class="card"><h4>📝 Professional Cover Letter Template</h4>', unsafe_allow_html=True)
                        
                        st.code("""
[Your Name]
[Your Address]
[City, State, ZIP Code]
[Your Email]
[Your Phone Number]
[Date]

[Hiring Manager's Name]
[Company Name]
[Company Address]
[City, State, ZIP Code]

Dear [Hiring Manager's Name / Hiring Team],

**PARAGRAPH 1: COMPELLING OPENING & INTEREST**
I am writing to express my strong interest in the [Job Title] position at [Company Name]. [Mention how you learned about the role]. With my background in [relevant field/experience], I am excited about the opportunity to contribute to [specific company goal/project/mission].

**PARAGRAPH 2: RELEVANT EXPERIENCE & ACHIEVEMENTS**
In my [current/previous role] at [Company], I [specific achievement with quantifiable results]. This experience has prepared me well for the [specific requirement from job description]. For example, [detailed example that directly relates to job requirements]. My expertise in [relevant skills] would allow me to [specific contribution you can make].

**PARAGRAPH 3: COMPANY CONNECTION & CULTURAL FIT**
I am particularly drawn to [Company Name] because of [specific reason related to company values/mission/recent news]. Your commitment to [company value/initiative] aligns perfectly with my professional values and career goals. I am excited about the possibility of [specific contribution/project/goal].

**PARAGRAPH 4: CALL TO ACTION & CLOSING**
I would welcome the opportunity to discuss how my [key strengths/skills] can contribute to [Company Name]'s continued success. Thank you for considering my application. I look forward to hearing from you soon.

Sincerely,
[Your Name]
                        """, language='text')
                        
                        st.markdown("""
                        <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <h5>💡 Pro Tips for Success:</h5>
                            <ul>
                                <li><strong>Length:</strong> Keep it to one page (3-4 paragraphs)</li>
                                <li><strong>Customization:</strong> Tailor each letter to the specific role and company</li>
                                <li><strong>Action Words:</strong> Use strong verbs like "achieved," "led," "improved," "created"</li>
                                <li><strong>Quantify Results:</strong> Include numbers, percentages, and specific outcomes</li>
                                <li><strong>Proofreading:</strong> Check for grammar, spelling, and formatting errors</li>
                                <li><strong>File Format:</strong> Save as PDF to preserve formatting</li>
                            </ul>
                        </div>
                        """)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                else:
                    st.markdown(f'<div class="error-card">❌ Analysis failed: {analysis_data.get("error", "Unknown error occurred")}</div>', unsafe_allow_html=True)

elif page == "📧 Email Test":
    create_header("Email Configuration Test", "Verify Notification System")
    
    st.markdown("""
    <div class="card">
        <h3>🔧 Email System Verification</h3>
        <p>Test your email configuration to ensure shortlist notifications are working properly. This helps verify SMTP settings and email delivery.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Test email configuration with enhanced display
    st.markdown('<div class="form-container"><h4>⚙️ Current Configuration Status</h4></div>', unsafe_allow_html=True)
    config_test = test_email_configuration()
    
    if config_test['success']:
        st.markdown(f'<div class="success-card">✅ {config_test["message"]}</div>', unsafe_allow_html=True)
        
        # Display configuration details
        with st.expander("🔍 View Email Configuration Details"):
            config_data = config_test.get('config', {})
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Server:** {config_data.get('server', 'N/A')}")
                st.write(f"**Port:** {config_data.get('port', 'N/A')}")
            with col2:
                st.write(f"**TLS Enabled:** {'Yes' if config_data.get('use_tls') else 'No'}")
                st.write(f"**Sender:** {config_data.get('sender', 'N/A')}")
        
        # Send test email section
        st.markdown("""
        <div class="form-container">
            <h4>📧 Send Test Notification</h4>
            <p>Send a sample shortlist notification to verify email delivery is working correctly.</p>
        </div>
        """, unsafe_allow_html=True)
        
        test_email_address = st.text_input(
            "📧 Test Email Address:",
            placeholder="your-test-email@example.com",
            help="Enter an email address where you want to receive the test notification"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Send Test Email", type="primary", use_container_width=True):
                if test_email_address and '@' in test_email_address:
                    with st.spinner("📧 Sending test notification email..."):
                        result = send_test_email(test_email_address)
                    
                    if result['success']:
                        st.markdown(f'<div class="success-card">✅ {result["message"]}</div>', unsafe_allow_html=True)
                        st.balloons()
                        
                        st.markdown("""
                        <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h5 style="color: #4CAF50;">🎉 Test Email Sent Successfully!</h5>
                            <p>Check your email inbox (and spam folder) for the test notification. The email should contain:</p>
                            <ul>
                                <li>Professional formatting and styling</li>
                                <li>Sample job title and company information</li>
                                <li>Congratulations message for being shortlisted</li>
                                <li>Next steps information</li>
                            </ul>
                        </div>
                        """)
                    else:
                        st.markdown(f'<div class="error-card">❌ {result["message"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-card">⚠️ Please enter a valid email address</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="error-card">❌ {config_test["message"]}</div>', unsafe_allow_html=True)
        if 'instructions' in config_test:
            st.markdown(f'<div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 10px 0;">💡 {config_test["instructions"]}</div>', unsafe_allow_html=True)
        
        # Email setup guide
        st.markdown("""
        <div class="form-container">
            <h4>📝 Email Configuration Setup Guide</h4>
            <p>To enable email notifications, you need to configure SMTP settings in your environment file.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card">
            <h5>🔧 Required Environment Variables (.env file)</h5>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <pre><code>MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com</code></pre>
            </div>
            
            <h5>📧 Gmail Setup Instructions:</h5>
            <ol>
                <li><strong>Enable 2-Factor Authentication:</strong> Go to your Google Account settings and enable 2FA</li>
                <li><strong>Generate App Password:</strong> Create a specific app password for this application</li>
                <li><strong>Use App Password:</strong> Use the generated app password (not your regular Gmail password)</li>
                <li><strong>Update .env File:</strong> Add your email and app password to the environment file</li>
            </ol>
            
            <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h6>💡 Security Best Practices:</h6>
                <ul>
                    <li>Never use your regular password - always use app passwords</li>
                    <li>Keep your .env file secure and never commit it to version control</li>
                    <li>Consider using environment variables or secrets management for production</li>
                    <li>Regularly rotate your app passwords for security</li>
                </ul>
            </div>
        </div>
        """)

# Enhanced Footer
st.markdown("""
<div style="margin-top: 50px; padding: 30px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 15px; text-align: center;">
    <h3 style="margin: 0 0 15px 0;">🎯 Resume Match AI</h3>
    <p style="margin: 0 0 10px 0; opacity: 0.9;">Powered by Google Gemini AI • Built with Streamlit</p>
    <p style="margin: 0; font-size: 0.9em; opacity: 0.8;">Revolutionizing recruitment with artificial intelligence</p>
</div>
""", unsafe_allow_html=True)
