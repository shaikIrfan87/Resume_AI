# 🎯 Streamlit Resume Matcher

An AI-powered recruitment tool built with Streamlit that matches resumes to job descriptions using Google's Gemini AI. This application helps HR teams streamline their recruitment process by automatically analyzing resumes, generating insights, and sending professional notifications to candidates.

## ✨ Features

### 🏠 **Dashboard Analytics**
- Real-time recruitment statistics
- Job application analytics with interactive charts
- Candidate shortlisting success rates
- Visual data representation with Plotly

### 💼 **Job Management**
- Add jobs manually or via file upload
- AI-assisted job title extraction from descriptions
- Job listing with search and filter capabilities
- Delete and manage existing job postings

### 📄 **Resume Analysis**
- Bulk PDF resume upload and processing
- AI-powered resume-to-job matching using Gemini AI
- Detailed scoring system (0-100) with fit verdicts
- Personalized feedback and missing skills identification
- Export analysis results

### 📧 **Email Notifications**
- Professional email templates for candidate notifications
- Bulk email sending capabilities
- SMTP configuration with popular email providers
- Email testing and validation tools

### 📝 **Cover Letter Generation**
- AI-powered personalized cover letter creation
- Multiple template options and styles
- Integration with job descriptions and candidate profiles
- Real-time generation with custom parameters

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key
- Email account with app password (for notifications)

### Installation

1. **Clone or download the project**
   ```bash
   cd streamlit_resume_matcher
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Copy `.env` file and update with your actual credentials:
   ```bash
   # Required
   GOOGLE_API_KEY=your_actual_google_api_key
   
   # For email notifications (optional)
   EMAIL_USERNAME=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```

4. **Run setup script**
   ```bash
   python setup_streamlit.py
   ```

5. **Start the application**
   ```bash
   streamlit run app.py
   ```

6. **Open your browser** to `http://localhost:8501`

## 📋 Configuration

### Google Gemini API Setup
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file as `GOOGLE_API_KEY`

### Email Configuration
For Gmail users:
1. Enable 2-factor authentication
2. Generate an app password
3. Use the app password in `EMAIL_PASSWORD`

For other email providers, update the SMTP settings accordingly.

## 🏗️ Project Structure

```
streamlit_resume_matcher/
├── app.py                 # Main Streamlit application
├── database.py           # SQLite database models and operations
├── services/
│   ├── email_service.py  # Email notification service
│   └── gemini_service.py # AI analysis service
├── .streamlit/
│   ├── config.toml       # Streamlit configuration
│   └── secrets.toml      # Secrets template
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables template
├── setup_streamlit.py   # Setup and initialization script
└── README.md           # This file
```

## 🎨 User Interface

The application features a modern, professional interface with:

- **Responsive sidebar navigation**
- **Interactive data visualizations**
- **Professional color scheme**
- **Card-based layouts**
- **Progress indicators**
- **Real-time feedback**

### Main Pages

1. **🏠 Home** - Welcome dashboard with system overview
2. **📊 Dashboard** - Analytics and recruitment insights
3. **💼 Jobs** - Job management and posting
4. **📄 Resumes** - Resume upload and analysis
5. **📝 Cover Letters** - AI cover letter generation
6. **✉️ Email Test** - Email configuration testing

## 🤖 AI Features

### Resume Analysis
- **Relevance Scoring**: 0-100 match score
- **Fit Verdict**: High/Medium/Low classification
- **Detailed Summary**: Candidate strengths and weaknesses
- **Personalized Feedback**: Improvement suggestions
- **Missing Skills**: Gap analysis

### Job Title Extraction
- Automatic job title detection from descriptions
- AI-powered text processing
- Smart categorization

### Cover Letter Generation
- Personalized content based on job requirements
- Multiple template styles
- Professional formatting

## 📧 Email Templates

Professional HTML email templates include:
- Company branding placeholder
- Personalized candidate information
- Job-specific details
- Professional styling
- Call-to-action buttons

## 🔒 Security & Privacy

- Environment variables for sensitive data
- Local SQLite database (no cloud storage)
- Secure SMTP authentication
- API key protection
- No permanent file storage of resumes

## 🛠️ Development

### Adding New Features
1. Create new page functions in `app.py`
2. Add database models in `database.py`
3. Implement services in the `services/` directory
4. Update navigation in the sidebar

### Customization
- Modify themes in `.streamlit/config.toml`
- Update email templates in `email_service.py`
- Adjust AI prompts in `gemini_service.py`

## 📈 Performance

- **Fast Loading**: Optimized Streamlit components
- **Efficient Database**: SQLite with proper indexing
- **Responsive UI**: Real-time updates and feedback
- **Batch Processing**: Bulk resume analysis
- **Error Handling**: Graceful degradation with fallbacks

## 🚨 Troubleshooting

### Common Issues

**API Quota Exceeded**
- The app includes mock data fallbacks
- Check your Google Cloud API limits
- Consider upgrading your API plan

**Email Not Sending**
- Verify SMTP settings
- Check app password configuration
- Use the built-in email test feature

**Database Errors**
- Run `python setup_streamlit.py` to recreate database
- Check file permissions in the project directory

**Streamlit Not Starting**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version compatibility
- Verify port 8501 is available

### Support

For additional support:
1. Check the setup script output for configuration issues
2. Verify all environment variables are set correctly
3. Test API connectivity using the built-in test features
4. Review console output for detailed error messages

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

---

**Built with ❤️ using Streamlit and Google Gemini AI**