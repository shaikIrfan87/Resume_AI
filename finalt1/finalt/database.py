# database.py - Pure SQLite implementation for Streamlit
import sqlite3
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from contextlib import contextmanager

# Database configuration
DATABASE_PATH = "resumematch.db"

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize SQLite database with required tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create candidates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                resume_filename TEXT NOT NULL,
                job_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES job (id) ON DELETE CASCADE
            )
        ''')
        
        # Create analysis_result table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_result (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                score INTEGER NOT NULL,
                verdict TEXT NOT NULL,
                summary TEXT NOT NULL,
                feedback TEXT NOT NULL,
                missing_skills TEXT,
                candidate_id INTEGER NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidate (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()

@dataclass
class Job:
    """Job model for Streamlit"""
    id: Optional[int] = None
    title: str = ""
    company: str = ""
    description: str = ""
    created_at: Optional[str] = None
    
    @staticmethod
    def create(title: str, company: str, description: str) -> 'Job':
        """Create a new job"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO job (title, company, description) VALUES (?, ?, ?)",
                (title, company, description)
            )
            job_id = cursor.lastrowid
            conn.commit()
            return Job.get_by_id(job_id)
    
    @staticmethod
    def get_all() -> List['Job']:
        """Get all jobs"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM job ORDER BY id DESC")
            rows = cursor.fetchall()
            return [Job(**dict(row)) for row in rows]
    
    @staticmethod
    def get_by_id(job_id: int) -> Optional['Job']:
        """Get job by ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM job WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            return Job(**dict(row)) if row else None
    
    @staticmethod
    def delete(job_id: int) -> bool:
        """Delete a job and all related data"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Delete analysis results first
            cursor.execute(
                "DELETE FROM analysis_result WHERE candidate_id IN (SELECT id FROM candidate WHERE job_id = ?)",
                (job_id,)
            )
            # Delete candidates
            cursor.execute("DELETE FROM candidate WHERE job_id = ?", (job_id,))
            # Delete job
            cursor.execute("DELETE FROM job WHERE id = ?", (job_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'description': self.description,
            'created_at': self.created_at
        }

@dataclass
class Candidate:
    """Candidate model for Streamlit"""
    id: Optional[int] = None
    name: str = ""
    email: Optional[str] = None
    resume_filename: str = ""
    job_id: int = 0
    created_at: Optional[str] = None
    
    @staticmethod
    def create(name: str, resume_filename: str, job_id: int, email: Optional[str] = None) -> 'Candidate':
        """Create a new candidate"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO candidate (name, email, resume_filename, job_id) VALUES (?, ?, ?, ?)",
                (name, email, resume_filename, job_id)
            )
            candidate_id = cursor.lastrowid
            conn.commit()
            return Candidate.get_by_id(candidate_id)
    
    @staticmethod
    def get_all() -> List['Candidate']:
        """Get all candidates"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM candidate ORDER BY id DESC")
            rows = cursor.fetchall()
            return [Candidate(**dict(row)) for row in rows]
    
    @staticmethod
    def get_by_job_id(job_id: int) -> List['Candidate']:
        """Get candidates by job ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM candidate WHERE job_id = ? ORDER BY id DESC", (job_id,))
            rows = cursor.fetchall()
            return [Candidate(**dict(row)) for row in rows]
    
    @staticmethod
    def get_by_id(candidate_id: int) -> Optional['Candidate']:
        """Get candidate by ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM candidate WHERE id = ?", (candidate_id,))
            row = cursor.fetchone()
            return Candidate(**dict(row)) if row else None
    
    def update_email(self, email: str) -> bool:
        """Update candidate email"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE candidate SET email = ? WHERE id = ?", (email, self.id))
            conn.commit()
            self.email = email
            return cursor.rowcount > 0
    
    @staticmethod
    def get_shortlisted() -> List[Dict]:
        """Get all shortlisted candidates with job details"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.name, c.email, c.resume_filename,
                       j.title as job_title, j.company, j.id as job_id,
                       ar.score, ar.verdict, ar.summary
                FROM candidate c
                JOIN job j ON c.job_id = j.id
                JOIN analysis_result ar ON c.id = ar.candidate_id
                WHERE ar.score >= 65
                ORDER BY ar.score DESC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'resume_filename': self.resume_filename,
            'job_id': self.job_id,
            'created_at': self.created_at
        }

@dataclass
class AnalysisResult:
    """Analysis result model for Streamlit"""
    id: Optional[int] = None
    score: int = 0
    verdict: str = ""
    summary: str = ""
    feedback: str = ""
    missing_skills: Optional[str] = None
    candidate_id: int = 0
    created_at: Optional[str] = None
    
    @staticmethod
    def create(score: int, verdict: str, summary: str, feedback: str, 
               missing_skills: List[str], candidate_id: int) -> 'AnalysisResult':
        """Create a new analysis result"""
        missing_skills_json = json.dumps(missing_skills) if missing_skills else None
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO analysis_result 
                   (score, verdict, summary, feedback, missing_skills, candidate_id) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (score, verdict, summary, feedback, missing_skills_json, candidate_id)
            )
            result_id = cursor.lastrowid
            conn.commit()
            return AnalysisResult.get_by_id(result_id)
    
    @staticmethod
    def get_by_candidate_id(candidate_id: int) -> Optional['AnalysisResult']:
        """Get analysis result by candidate ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analysis_result WHERE candidate_id = ?", (candidate_id,))
            row = cursor.fetchone()
            return AnalysisResult(**dict(row)) if row else None
    
    @staticmethod
    def get_by_id(result_id: int) -> Optional['AnalysisResult']:
        """Get analysis result by ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analysis_result WHERE id = ?", (result_id,))
            row = cursor.fetchone()
            return AnalysisResult(**dict(row)) if row else None
    
    def get_missing_skills_list(self) -> List[str]:
        """Get missing skills as a list"""
        if not self.missing_skills:
            return []
        try:
            return json.loads(self.missing_skills)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'score': self.score,
            'verdict': self.verdict,
            'summary': self.summary,
            'feedback': self.feedback,
            'missing_skills': self.get_missing_skills_list(),
            'candidate_id': self.candidate_id,
            'created_at': self.created_at
        }

class DatabaseManager:
    """Database manager for Streamlit app"""
    
    @staticmethod
    def get_dashboard_stats() -> Dict:
        """Get dashboard statistics"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get basic counts
            cursor.execute("SELECT COUNT(*) FROM job")
            total_jobs = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM candidate")
            total_candidates = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM analysis_result WHERE score >= 65")
            shortlisted_count = cursor.fetchone()[0]
            
            # Get job-wise statistics
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
            
            jobs_stats = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_jobs': total_jobs,
                'total_candidates': total_candidates,
                'shortlisted_count': shortlisted_count,
                'jobs_stats': jobs_stats
            }
    
    @staticmethod
    def get_candidates_with_analysis(job_id: int) -> List[Dict]:
        """Get candidates with their analysis results for a specific job"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.name, c.email, c.resume_filename,
                       ar.score, ar.verdict, ar.summary, ar.feedback, ar.missing_skills
                FROM candidate c
                LEFT JOIN analysis_result ar ON c.id = ar.candidate_id
                WHERE c.job_id = ?
                ORDER BY ar.score DESC NULLS LAST, c.id DESC
            """, (job_id,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                # Parse missing skills if present
                if result['missing_skills']:
                    try:
                        result['missing_skills'] = json.loads(result['missing_skills'])
                    except (json.JSONDecodeError, TypeError):
                        result['missing_skills'] = []
                else:
                    result['missing_skills'] = []
                results.append(result)
            
            return results
