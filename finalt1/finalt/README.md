# Resume Matching System - Pure Streamlit Version 🎯

A powerful AI-driven resume analysis and matching system built entirely with Streamlit and Google Gemini AI. This version completely replaces Flask with Streamlit for a better user experience.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Google AI](https://img.shields.io/badge/Google_AI-4285F4?style=for-the-badge&logo=google&logoColor=white)

## ✨ Features

- **🤖 AI-Powered Analysis**: Uses Google Gemini AI for intelligent resume-job matching
- **📊 Interactive Dashboard**: Real-time analytics and recruitment metrics
- **📄 Multi-format Support**: Handles PDF and DOCX files for both resumes and job descriptions
- **🎯 Smart Scoring**: Relevance scoring with detailed feedback and missing skills analysis
- **📧 Email Integration**: Automated shortlist notifications using pure Python SMTP
- **✉️ Cover Letter Assistant**: AI-powered cover letter recommendations
- **🔍 Batch Processing**: Analyze multiple resumes simultaneously
- **💾 Pure SQLite**: Lightweight database without complex dependencies
- **🚀 Easy Deployment**: Simple setup with Streamlit Community Cloud support

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

1. **Clone/Download the project and navigate to the directory:**
   ```bash
   cd finalt1/finalt
   ```

2. **Run the setup script:**
   ```bash
   python setup_streamlit.py
   ```

3. **Follow the prompts** to configure your API key and launch the app!

### Option 2: Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   # Copy and edit the .env file with your Google API key
   # Update GOOGLE_API_KEY with your actual key
   ```

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```

## 🔧 Configuration

### Required Environment Variables

Create/update the `.env` file in the project root:

```env
# Google Gemini AI Configuration
GOOGLE_API_KEY=your_google_api_key_here

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here
MAIL_DEFAULT_SENDER=your_email@gmail.com
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

### 6. **Email Test**
- Test email configuration
- Send test notifications
- Verify SMTP settings

## 🏗️ Architecture

```
app.py                    # Main Streamlit application
├── database.py          # Pure SQLite database models
├── services/
│   ├── gemini_service.py # Google Gemini AI integration
│   └── email_service.py  # Pure Python SMTP email service
├── uploads/              # Uploaded resume files
├── .streamlit/           # Streamlit configuration
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
streamlit run app.py
```

### Streamlit Community Cloud
1. Push code to GitHub repository
2. Connect to [Streamlit Community Cloud](https://streamlit.io/cloud)
3. Deploy directly from repository
4. Add secrets in Streamlit Cloud dashboard:
   ```
   GOOGLE_API_KEY = "your_api_key_here"
   ```

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

## 🔄 Migration from Flask Version

This pure Streamlit version offers several advantages:

- **Better UX**: Interactive widgets and real-time feedback
- **Easier Deployment**: No complex Flask setup required
- **Modern Interface**: Built-in responsive design
- **Simplified Architecture**: Pure Python without web server complexities
- **Better Performance**: Streamlit's efficient caching and state management

## 📦 Dependencies

- **streamlit**: Web application framework
- **python-docx**: Word document processing
- **python-dotenv**: Environment variable management
- **google-generativeai**: Google Gemini AI integration
- **pdfplumber**: PDF text extraction
- **PyMuPDF**: Alternative PDF processing
- **pandas**: Data manipulation and analysis

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
   - Install all requirements: `pip install -r requirements.txt`
   - Check Python version (3.8+ recommended)

5. **Email Issues**
   - For Gmail, use App Passwords (not regular password)
   - Enable 2-factor authentication first
   - Check SMTP settings in `.env` file

### Performance Tips

- Use PDF files under 10MB for faster processing
- Batch process resumes in groups of 10-20 for optimal performance
- Monitor API quota usage with high-volume analysis
- Clear browser cache if UI becomes unresponsive

## 🔒 Security Notes

- Never commit actual API keys or credentials to version control
- Use environment variables or Streamlit secrets for sensitive data
- For production deployment, consider using secure secret management
- Regularly rotate API keys and passwords

## 📝 Development

### Running in Development Mode

```bash
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
streamlit run app.py

# Run setup with cleanup
python setup_streamlit.py
```

### File Structure

- All Flask-related files have been removed
- Pure Streamlit implementation in `app.py`
- Modular service architecture maintained
- SQLite replaces SQLAlchemy for simplicity

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

- **Issues**: Report bugs via GitHub Issues
- **Documentation**: Check this README and inline code comments
- **Email Configuration**: See EMAIL_SETUP.md for detailed email setup

## 🎉 Acknowledgments

- **Google Gemini AI** for powerful language understanding
- **Streamlit** for the amazing web app framework
- **Open Source Libraries** used in this project

---

**Made with ❤️ and Pure Streamlit Power**

Ready to revolutionize your recruitment process with pure Streamlit? Get started now! 🚀