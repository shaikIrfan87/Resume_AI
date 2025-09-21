# Resume Matching System - Streamlit Version 🎯

A powerful AI-driven resume analysis and matching system built with Streamlit and Google Gemini AI.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Google AI](https://img.shields.io/badge/Google_AI-4285F4?style=for-the-badge&logo=google&logoColor=white)

## ✨ Features

- **🤖 AI-Powered Analysis**: Uses Google Gemini AI for intelligent resume-job matching
- **📊 Interactive Dashboard**: Real-time analytics and recruitment metrics
- **📄 Multi-format Support**: Handles PDF and DOCX files for both resumes and job descriptions
- **🎯 Smart Scoring**: Relevance scoring with detailed feedback and missing skills analysis
- **📧 Email Integration**: Automated shortlist notifications (configurable)
- **✉️ Cover Letter Assistant**: AI-powered cover letter recommendations
- **🔍 Batch Processing**: Analyze multiple resumes simultaneously
- **💾 Data Persistence**: SQLite database for storing jobs, candidates, and analysis results

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

1. **Run the setup script:**
   ```bash
   python setup_streamlit.py
   ```

2. **Configure your API key** when prompted in the `.env` file

3. **Launch the app** - the setup script will offer to start it automatically!

### Option 2: Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements_streamlit.txt
   ```

2. **Set up environment:**
   ```bash
   # Copy the .env file and add your Google API key
   cp .env.template .env
   # Edit .env with your actual API key
   ```

3. **Run the application:**
   ```bash
   streamlit run streamlit_app.py
   ```

## 🔧 Configuration

### Required Environment Variables

Create a `.env` file in the project root with:

```env
# Google Gemini API Configuration
GOOGLE_API_KEY=your_google_api_key_here

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here
```

### Getting Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Create a new project or select existing one
4. Generate an API key
5. Copy the key to your `.env` file

## 🎮 How to Use

### 1. **Home Page**
- Overview of system capabilities
- Quick statistics dashboard
- Getting started guide

### 2. **Jobs Section**
- Add new job descriptions (text or file upload)
- View and manage existing jobs
- Automatic job title extraction using AI

### 3. **Resumes Section**
- Select a job for analysis
- Upload multiple PDF resumes
- View analysis results with scores and feedback
- Manage candidate emails
- Send shortlist notifications

### 4. **Dashboard**
- Comprehensive analytics
- Job performance metrics
- Visual charts and statistics
- Shortlisting success rates

### 5. **Cover Letters**
- AI-powered analysis of job-resume fit
- Personalized cover letter recommendations
- Structured templates and tips
- Missing skills identification

## 🏗️ System Architecture

```
streamlit_app.py          # Main Streamlit application
├── services/
│   ├── gemini_service.py # Google Gemini AI integration
│   └── email_service.py  # Email notifications
├── uploads/              # Uploaded resume files
├── resumematch.db       # SQLite database
└── .env                 # Environment configuration
```

## 📊 Database Schema

- **Jobs**: Job descriptions with company and title information
- **Candidates**: Resume uploads linked to specific jobs
- **Analysis Results**: AI analysis scores, verdicts, and feedback

## 🎯 AI Analysis Features

The system provides detailed analysis including:

- **Relevance Score**: 0-100% match percentage
- **Fit Verdict**: High/Medium/Low classification
- **Summary**: Concise candidate strengths/weaknesses
- **Personalized Feedback**: Improvement suggestions
- **Missing Skills**: Gap analysis for better targeting

## 🚀 Deployment Options

### Local Development
```bash
streamlit run streamlit_app.py
```

### Streamlit Community Cloud
1. Push code to GitHub repository
2. Connect to [Streamlit Community Cloud](https://streamlit.io/cloud)
3. Deploy directly from repository
4. Add secrets in Streamlit Cloud dashboard

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements_streamlit.txt .
RUN pip install -r requirements_streamlit.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py"]
```

## 🔄 Migration from Flask Version

This Streamlit version maintains compatibility with the original Flask application data:

- Database schema is identical
- Service modules are reused
- Configuration remains the same
- File uploads are preserved

## 🛠️ Troubleshooting

### Common Issues

1. **API Key Error**
   - Ensure `GOOGLE_API_KEY` is set in `.env`
   - Check API key validity in Google AI Studio

2. **File Upload Issues**
   - Verify PDF files are not corrupted
   - Check file permissions in uploads directory

3. **Database Errors**
   - Delete `resumematch.db` to reset database
   - Run the app again to recreate tables

4. **Import Errors**
   - Install all requirements: `pip install -r requirements_streamlit.txt`
   - Check Python version (3.8+ recommended)

### Performance Tips

- Use PDF files under 10MB for faster processing
- Batch process resumes in groups of 10-20 for optimal performance
- Monitor API quota usage with high-volume analysis

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

- **Issues**: Report bugs via GitHub Issues
- **Documentation**: Check this README and inline code comments
- **Community**: Join discussions in GitHub Discussions

## 🎉 Acknowledgments

- **Google Gemini AI** for powerful language understanding
- **Streamlit** for the amazing web app framework
- **Open Source Libraries** used in this project

---

**Made with ❤️ and AI-powered insights**

Ready to revolutionize your recruitment process? Get started now! 🚀