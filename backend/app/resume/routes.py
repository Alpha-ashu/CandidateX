"""
Resume processing routes for upload, parsing, and ATS analysis.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import os
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.models.user import User
from app.models import get_database
from app.auth.dependencies import get_current_user
from app.config import settings
from app.utils.cloud_storage import cloud_storage

# Resume processing service would be imported here
# from app.services.resume_processor import process_resume_file

logger = logging.getLogger(__name__)

router = APIRouter()

class ResumeUploadResponse(BaseModel):
    """Resume upload response model."""
    resume_id: str
    filename: str
    file_size: int
    content_type: str
    upload_status: str
    message: str

class ResumeAnalysisResponse(BaseModel):
    """Resume analysis response model."""
    resume_id: str
    ats_score: float
    ats_feedback: Dict[str, Any]
    skills_extracted: List[str]
    experience_years: Optional[float]
    education_level: Optional[str]
    keywords_found: List[str]
    suggestions: List[str]
    processing_status: str

class ResumeComparisonRequest(BaseModel):
    """Resume comparison request model."""
    resume_id: str
    job_description: str
    job_title: str

class ResumeComparisonResponse(BaseModel):
    """Resume comparison response model."""
    resume_id: str
    job_title: str
    match_score: float
    skills_match: Dict[str, Any]
    experience_match: Dict[str, Any]
    education_match: Dict[str, Any]
    keyword_match: Dict[str, Any]
    recommendations: List[str]

@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Upload and process a resume file.
    """
    # Validate file type
    allowed_extensions = [".pdf", ".docx", ".doc", ".txt"]
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
        )

    # Validate file size (10MB limit)
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes"
        )

    # Generate unique resume ID
    resume_id = str(uuid.uuid4())

    # Upload file to cloud storage
    from io import BytesIO
    file_stream = BytesIO(file_content)

    try:
        upload_result = await cloud_storage.upload_file(
            file_stream,
            file.filename,
            file.content_type,
            folder="resumes"
        )
    except Exception as e:
        logger.error(f"Failed to upload resume to cloud storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload resume file"
        )

    # Store resume metadata in database
    resume_doc = {
        "id": resume_id,
        "user_id": current_user.id,
        "filename": file.filename,
        "storage_info": upload_result,
        "file_size": file_size,
        "content_type": file.content_type,
        "file_extension": file_extension,
        "upload_status": "uploaded",
        "processing_status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    await db.resumes.insert_one(resume_doc)

    # Start background processing
    background_tasks.add_task(process_resume_background, resume_id)

    logger.info(f"Resume uploaded: {resume_id} for user {current_user.email}")

    return ResumeUploadResponse(
        resume_id=resume_id,
        filename=file.filename,
        file_size=file_size,
        content_type=file.content_type,
        upload_status="uploaded",
        message="Resume uploaded successfully. Processing will begin shortly."
    )

@router.get("/list")
async def list_user_resumes(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List user's uploaded resumes.
    """
    cursor = db.resumes.find({"user_id": current_user.id}).sort("created_at", -1).skip(skip).limit(limit)
    resumes = await cursor.to_list(length=None)

    # Format response
    resume_list = []
    for resume in resumes:
        resume_list.append({
            "id": resume["id"],
            "filename": resume["filename"],
            "file_size": resume["file_size"],
            "upload_status": resume["upload_status"],
            "processing_status": resume.get("processing_status", "unknown"),
            "ats_score": resume.get("ats_score"),
            "created_at": resume["created_at"],
            "updated_at": resume["updated_at"]
        })

    return {
        "resumes": resume_list,
        "total": len(resume_list),  # In production, use count_documents
        "skip": skip,
        "limit": limit
    }

@router.get("/{resume_id}")
async def get_resume_details(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get detailed resume information and analysis.
    """
    resume_doc = await db.resumes.find_one({"id": resume_id, "user_id": current_user.id})
    if not resume_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    # Format response
    resume_details = {
        "id": resume_doc["id"],
        "filename": resume_doc["filename"],
        "file_size": resume_doc["file_size"],
        "content_type": resume_doc["content_type"],
        "upload_status": resume_doc["upload_status"],
        "processing_status": resume_doc.get("processing_status", "unknown"),
        "created_at": resume_doc["created_at"],
        "updated_at": resume_doc["updated_at"]
    }

    # Include analysis results if available
    if "analysis" in resume_doc:
        resume_details["analysis"] = resume_doc["analysis"]

    return resume_details

@router.get("/{resume_id}/analysis", response_model=ResumeAnalysisResponse)
async def get_resume_analysis(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get resume ATS analysis results.
    """
    resume_doc = await db.resumes.find_one({"id": resume_id, "user_id": current_user.id})
    if not resume_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    processing_status = resume_doc.get("processing_status", "unknown")

    if processing_status == "pending":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Resume is still being processed. Please check back later."
        )
    elif processing_status == "failed":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Resume processing failed. Please try uploading again."
        )
    elif processing_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Resume processing is in progress."
        )

    # Return analysis results
    analysis = resume_doc.get("analysis", {})

    return ResumeAnalysisResponse(
        resume_id=resume_id,
        ats_score=analysis.get("ats_score", 0),
        ats_feedback=analysis.get("ats_feedback", {}),
        skills_extracted=analysis.get("skills_extracted", []),
        experience_years=analysis.get("experience_years"),
        education_level=analysis.get("education_level"),
        keywords_found=analysis.get("keywords_found", []),
        suggestions=analysis.get("suggestions", []),
        processing_status=processing_status
    )

@router.post("/{resume_id}/compare", response_model=ResumeComparisonResponse)
async def compare_resume_to_job(
    resume_id: str,
    comparison_request: ResumeComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Compare resume against a job description.
    """
    # Verify resume exists and belongs to user
    resume_doc = await db.resumes.find_one({"id": resume_id, "user_id": current_user.id})
    if not resume_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    if resume_doc.get("processing_status") != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume analysis not completed yet"
        )

    # Perform comparison (mock implementation)
    resume_analysis = resume_doc.get("analysis", {})
    comparison_result = perform_resume_job_comparison(
        resume_analysis,
        comparison_request.job_description,
        comparison_request.job_title
    )

    # Store comparison result
    comparison_doc = {
        "id": str(uuid.uuid4()),
        "resume_id": resume_id,
        "user_id": current_user.id,
        "job_title": comparison_request.job_title,
        "job_description": comparison_request.job_description,
        "comparison_result": comparison_result,
        "created_at": datetime.utcnow()
    }

    await db.resume_comparisons.insert_one(comparison_doc)

    return ResumeComparisonResponse(
        resume_id=resume_id,
        job_title=comparison_request.job_title,
        **comparison_result
    )

@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete a resume and its analysis.
    """
    resume_doc = await db.resumes.find_one({"id": resume_id, "user_id": current_user.id})
    if not resume_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    # Delete file from storage
    file_path = resume_doc.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to delete resume file {file_path}: {e}")

    # Delete from database
    await db.resumes.delete_one({"id": resume_id, "user_id": current_user.id})

    # Delete related comparisons
    await db.resume_comparisons.delete_many({"resume_id": resume_id, "user_id": current_user.id})

    logger.info(f"Resume deleted: {resume_id} for user {current_user.email}")

    return {"message": "Resume deleted successfully"}

@router.get("/analytics/overview")
async def get_resume_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get resume analytics for the current user.
    """
    # Get resume statistics
    pipeline = [
        {"$match": {"user_id": current_user.id}},
        {"$group": {
            "_id": None,
            "total_resumes": {"$sum": 1},
            "processed_resumes": {"$sum": {"$cond": [{"$eq": ["$processing_status", "completed"]}, 1, 0]}},
            "average_ats_score": {"$avg": {"$cond": [{"$ne": ["$analysis.ats_score", None]}, "$analysis.ats_score", None]}},
            "total_file_size": {"$sum": "$file_size"}
        }}
    ]

    stats_result = await db.resumes.aggregate(pipeline).to_list(length=1)
    stats = stats_result[0] if stats_result else {
        "total_resumes": 0,
        "processed_resumes": 0,
        "average_ats_score": None,
        "total_file_size": 0
    }

    # Get ATS score distribution
    score_pipeline = [
        {"$match": {"user_id": current_user.id, "processing_status": "completed"}},
        {"$group": {
            "_id": {
                "$switch": {
                    "branches": [
                        {"case": {"$gte": ["$analysis.ats_score", 90]}, "then": "90-100"},
                        {"case": {"$gte": ["$analysis.ats_score", 80]}, "then": "80-89"},
                        {"case": {"$gte": ["$analysis.ats_score", 70]}, "then": "70-79"},
                        {"case": {"$gte": ["$analysis.ats_score", 60]}, "then": "60-69"}
                    ],
                    "default": "0-59"
                }
            },
            "count": {"$sum": 1}
        }}
    ]

    score_distribution = await db.resumes.aggregate(score_pipeline).to_list(length=None)
    score_dist_dict = {item["_id"]: item["count"] for item in score_distribution}

    # Get recent comparisons
    recent_comparisons_cursor = db.resume_comparisons.find({"user_id": current_user.id}).sort("created_at", -1).limit(5)
    recent_comparisons = await recent_comparisons_cursor.to_list(length=None)

    recent_jobs = []
    for comp in recent_comparisons:
        recent_jobs.append({
            "job_title": comp["job_title"],
            "match_score": comp["comparison_result"]["match_score"],
            "compared_at": comp["created_at"]
        })

    return {
        "stats": stats,
        "score_distribution": score_dist_dict,
        "recent_comparisons": recent_jobs,
        "insights": generate_resume_insights(stats, score_dist_dict)
    }

# Background processing functions
async def process_resume_background(resume_id: str):
    """Background task to process resume."""
    try:
        db = await get_database()

        # Get resume document
        resume_doc = await db.resumes.find_one({"id": resume_id})
        if not resume_doc:
            logger.error(f"Resume not found for processing: {resume_id}")
            return

        # Update status to processing
        await db.resumes.update_one(
            {"id": resume_id},
            {"$set": {"processing_status": "processing", "updated_at": datetime.utcnow()}}
        )

        # Download file from cloud storage for processing
        storage_info = resume_doc.get("storage_info", {})
        file_path = storage_info.get("file_path", "")
        file_content = await cloud_storage.download_file(file_path)

        if file_content is None:
            raise Exception("Failed to download resume file from storage")

        # Process the resume file content
        analysis_result = await process_resume_file_content(file_content, resume_doc)

        # Update resume with analysis results
        await db.resumes.update_one(
            {"id": resume_id},
            {
                "$set": {
                    "processing_status": "completed",
                    "analysis": analysis_result,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Resume processing completed: {resume_id}")

    except Exception as e:
        logger.error(f"Resume processing failed for {resume_id}: {e}")

        # Update status to failed
        await db.resumes.update_one(
            {"id": resume_id},
            {
                "$set": {
                    "processing_status": "failed",
                    "error_message": str(e),
                    "updated_at": datetime.utcnow()
                }
            }
        )

async def process_resume_file_content(file_content: bytes, resume_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Process resume file and extract information."""
    import re
    from typing import List, Set

    # Extract text from file based on type
    file_extension = resume_doc.get("file_extension", "").lower()
    text_content = ""

    try:
        if file_extension == ".pdf":
            # Extract text from PDF
            from PyPDF2 import PdfReader
            from io import BytesIO
            pdf_stream = BytesIO(file_content)
            pdf_reader = PdfReader(pdf_stream)

            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"

        elif file_extension in [".docx", ".doc"]:
            # Extract text from Word document
            from docx import Document
            from io import BytesIO
            doc_stream = BytesIO(file_content)
            doc = Document(doc_stream)
            text_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])

        elif file_extension == ".txt":
            # Plain text file
            text_content = file_content.decode('utf-8', errors='ignore')

        else:
            text_content = "Unsupported file format"

    except Exception as e:
        text_content = f"Error extracting text: {str(e)}"

    # Analyze the extracted text
    analysis = analyze_resume_text(text_content)

    return analysis

def analyze_resume_text(text: str) -> Dict[str, Any]:
    """Analyze resume text content."""
    import re
    from typing import List, Set, Dict

    # Clean and normalize text
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)

    # Define skill keywords (expandable)
    skill_keywords = {
        "programming_languages": ["python", "javascript", "java", "c++", "c#", "php", "ruby", "go", "rust", "typescript", "swift", "kotlin"],
        "web_technologies": ["html", "css", "react", "angular", "vue", "node.js", "express", "django", "flask", "spring"],
        "databases": ["mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle", "sql server"],
        "cloud_platforms": ["aws", "azure", "gcp", "heroku", "digitalocean", "docker", "kubernetes"],
        "tools": ["git", "jenkins", "jira", "slack", "postman", "figma", "photoshop"],
        "methodologies": ["agile", "scrum", "kanban", "waterfall", "tdd", "bdd", "ci/cd"]
    }

    # Extract skills
    skills_extracted = []
    for category, keywords in skill_keywords.items():
        for keyword in keywords:
            if keyword in text:
                skills_extracted.append(keyword.title())

    # Extract experience years (basic pattern matching)
    experience_years = extract_experience_years(text)

    # Extract education level
    education_level = extract_education_level(text)

    # Find common job-related keywords
    job_keywords = [
        "software engineer", "developer", "programmer", "analyst", "manager",
        "web development", "full stack", "backend", "frontend", "mobile",
        "api development", "database design", "system administration",
        "project management", "quality assurance", "devops"
    ]

    keywords_found = [kw for kw in job_keywords if kw in text]

    # Basic ATS scoring (simplified)
    ats_score = calculate_ats_score(text, skills_extracted, keywords_found, word_count)

    # Generate suggestions
    suggestions = generate_resume_suggestions(text, skills_extracted, keywords_found, word_count)

    # Detect sections
    sections_found = detect_resume_sections(text)

    # Calculate readability (basic)
    readability_score = calculate_readability_score(text)

    return {
        "ats_score": round(ats_score, 1),
        "ats_feedback": {
            "formatting_score": 75,  # Mock - would need more analysis
            "keyword_score": min(len(keywords_found) * 10, 100),
            "structure_score": len(sections_found) * 15,
            "readability_score": readability_score
        },
        "skills_extracted": list(set(skills_extracted)),  # Remove duplicates
        "experience_years": experience_years,
        "education_level": education_level,
        "keywords_found": keywords_found,
        "suggestions": suggestions,
        "sections_found": sections_found,
        "word_count": word_count,
        "readability_score": readability_score
    }

def extract_experience_years(text: str) -> float:
    """Extract years of experience from text."""
    import re

    # Look for patterns like "3 years", "5+ years", etc.
    year_patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
        r'experience\s*(?:of\s*)?(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years?\s*in\s*',
    ]

    max_years = 0
    for pattern in year_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                years = float(match)
                max_years = max(max_years, years)
            except ValueError:
                continue

    # If no specific years found, make educated guess based on keywords
    if max_years == 0:
        senior_keywords = ["senior", "lead", "principal", "architect", "manager"]
        mid_keywords = ["mid", "intermediate", "experienced"]
        junior_keywords = ["junior", "entry", "graduate", "intern"]

        if any(kw in text for kw in senior_keywords):
            max_years = 7.0
        elif any(kw in text for kw in mid_keywords):
            max_years = 4.0
        elif any(kw in text for kw in junior_keywords):
            max_years = 1.5
        else:
            max_years = 3.0  # Default assumption

    return max_years

def extract_education_level(text: str) -> str:
    """Extract highest education level from text."""
    education_levels = {
        "phd": ["phd", "ph.d", "doctorate", "doctoral"],
        "masters": ["masters", "master's", "ms", "ma", "msc", "mba", "mphil"],
        "bachelors": ["bachelors", "bachelor's", "bs", "ba", "bsc", "beng", "btech"],
        "associates": ["associates", "associate's", "aa", "aas"],
        "high_school": ["high school", "secondary school", "diploma"]
    }

    found_levels = []
    for level, keywords in education_levels.items():
        if any(keyword in text for keyword in keywords):
            found_levels.append(level)

    # Return highest level found
    level_hierarchy = ["high_school", "associates", "bachelors", "masters", "phd"]
    for level in reversed(level_hierarchy):
        if level in found_levels:
            return level.replace("_", " ").title()

    return "Not specified"

def calculate_ats_score(text: str, skills: List[str], keywords: List[str], word_count: int) -> float:
    """Calculate ATS compatibility score."""
    score = 50  # Base score

    # Skills factor (0-20 points)
    skill_score = min(len(skills) * 2, 20)
    score += skill_score

    # Keywords factor (0-15 points)
    keyword_score = min(len(keywords) * 3, 15)
    score += keyword_score

    # Length factor (0-10 points) - ATS prefers 400-800 words
    if 400 <= word_count <= 800:
        score += 10
    elif 200 <= word_count < 400:
        score += 5
    elif word_count > 800:
        score += 7  # Slightly penalize very long resumes

    # Contact info presence (0-5 points)
    contact_indicators = ["email", "phone", "linkedin", "@"]
    if any(indicator in text for indicator in contact_indicators):
        score += 5

    return min(score, 100)

def generate_resume_suggestions(text: str, skills: List[str], keywords: List[str], word_count: int) -> List[str]:
    """Generate improvement suggestions."""
    suggestions = []

    if len(skills) < 5:
        suggestions.append("Add more technical skills relevant to your target role")

    if len(keywords) < 3:
        suggestions.append("Include more industry-specific keywords")

    if word_count < 300:
        suggestions.append("Expand on your experience and achievements")
    elif word_count > 1000:
        suggestions.append("Consider condensing your resume to focus on the most relevant information")

    if "email" not in text and "phone" not in text:
        suggestions.append("Ensure contact information is clearly visible")

    if "quantified" not in text and "achievements" not in text:
        suggestions.append("Add quantifiable achievements and metrics")

    return suggestions[:5]  # Limit to 5 suggestions

def detect_resume_sections(text: str) -> List[str]:
    """Detect common resume sections."""
    sections = []
    section_keywords = {
        "contact": ["contact", "phone", "email", "address"],
        "summary": ["summary", "objective", "profile"],
        "experience": ["experience", "work", "employment", "job"],
        "education": ["education", "degree", "university", "college"],
        "skills": ["skills", "technologies", "competencies"],
        "projects": ["projects", "portfolio"],
        "certifications": ["certifications", "certificates", "licenses"],
        "awards": ["awards", "honors", "achievements"]
    }

    for section, keywords in section_keywords.items():
        if any(keyword in text for keyword in keywords):
            sections.append(section)

    return sections

def calculate_readability_score(text: str) -> float:
    """Calculate basic readability score."""
    sentences = re.split(r'[.!?]+', text)
    words = re.findall(r'\b\w+\b', text)

    if len(sentences) == 0 or len(words) == 0:
        return 0

    avg_words_per_sentence = len(words) / len(sentences)

    # Simple readability formula (lower is better readability)
    # Score between 0-100, where higher is better
    if avg_words_per_sentence <= 10:
        score = 90
    elif avg_words_per_sentence <= 15:
        score = 75
    elif avg_words_per_sentence <= 20:
        score = 60
    elif avg_words_per_sentence <= 25:
        score = 45
    else:
        score = 30

    return score

def perform_resume_job_comparison(
    resume_analysis: Dict[str, Any],
    job_description: str,
    job_title: str
) -> Dict[str, Any]:
    """Compare resume against job description."""
    # Mock implementation - in real implementation, use NLP and matching algorithms

    # Extract job requirements (mock)
    job_keywords = extract_job_keywords(job_description.lower())
    resume_keywords = set(resume_analysis.get("keywords_found", []))
    resume_skills = set(resume_analysis.get("skills_extracted", []))

    # Calculate matches
    keyword_matches = len(job_keywords.intersection(resume_keywords))
    skill_matches = len(job_keywords.intersection(resume_skills))

    # Calculate scores
    keyword_score = min((keyword_matches / max(len(job_keywords), 1)) * 100, 100)
    skill_score = min((skill_matches / max(len(job_keywords), 1)) * 100, 100)

    # Experience match
    required_experience = extract_experience_requirement(job_description)
    candidate_experience = resume_analysis.get("experience_years", 0)
    experience_score = min((candidate_experience / max(required_experience, 1)) * 100, 100)

    # Overall match score
    match_score = (keyword_score * 0.4 + skill_score * 0.4 + experience_score * 0.2)

    return {
        "match_score": round(match_score, 1),
        "skills_match": {
            "matched": list(resume_skills.intersection(job_keywords)),
            "missing": list(job_keywords - resume_skills),
            "score": skill_score
        },
        "experience_match": {
            "required_years": required_experience,
            "candidate_years": candidate_experience,
            "score": experience_score
        },
        "education_match": {
            "required_level": "Bachelor's Degree",  # Mock
            "candidate_level": resume_analysis.get("education_level"),
            "match": True  # Mock
        },
        "keyword_match": {
            "matched": list(resume_keywords.intersection(job_keywords)),
            "total_job_keywords": len(job_keywords),
            "score": keyword_score
        },
        "recommendations": generate_job_match_recommendations(
            match_score, job_keywords - resume_skills, required_experience - candidate_experience
        )
    }

def extract_job_keywords(job_description: str) -> set:
    """Extract keywords from job description."""
    # Mock implementation - in real implementation, use NLP
    common_keywords = {
        "python", "javascript", "java", "react", "node.js", "mongodb", "aws", "docker",
        "git", "agile", "scrum", "api", "database", "web development", "software engineer",
        "full stack", "backend", "frontend", "devops", "testing", "ci/cd"
    }

    found_keywords = set()
    desc_lower = job_description.lower()

    for keyword in common_keywords:
        if keyword in desc_lower:
            found_keywords.add(keyword)

    return found_keywords

def extract_experience_requirement(job_description: str) -> float:
    """Extract experience requirement from job description."""
    # Mock implementation
    desc_lower = job_description.lower()

    if "senior" in desc_lower or "lead" in desc_lower:
        return 5.0
    elif "mid" in desc_lower or "intermediate" in desc_lower:
        return 3.0
    elif "junior" in desc_lower or "entry" in desc_lower:
        return 1.0
    else:
        return 2.0  # Default

def generate_job_match_recommendations(
    match_score: float,
    missing_skills: set,
    experience_gap: float
) -> List[str]:
    """Generate recommendations for job matching."""
    recommendations = []

    if match_score < 50:
        recommendations.append("This job may not be the best fit. Consider roles that match your current skill set better.")

    if missing_skills:
        recommendations.append(f"Consider learning or highlighting these skills: {', '.join(list(missing_skills)[:5])}")

    if experience_gap > 1:
        recommendations.append(f"You may need approximately {experience_gap:.1f} more years of experience for this role.")

    if match_score >= 70:
        recommendations.append("This appears to be a good match! Highlight relevant experience and skills in your application.")

    return recommendations

def generate_resume_insights(stats: Dict[str, Any], score_distribution: Dict[str, Any]) -> List[str]:
    """Generate insights about resume performance."""
    insights = []

    avg_score = stats.get("average_ats_score")
    if avg_score:
        if avg_score >= 80:
            insights.append("Your resumes have excellent ATS scores on average!")
        elif avg_score >= 70:
            insights.append("Your resumes have good ATS scores. Minor improvements could help.")
        else:
            insights.append("Consider optimizing your resumes for better ATS performance.")

    total_resumes = stats.get("total_resumes", 0)
    processed_resumes = stats.get("processed_resumes", 0)

    if processed_resumes < total_resumes:
        insights.append(f"{total_resumes - processed_resumes} resume(s) are still being processed.")

    # Score distribution insights
    high_scores = score_distribution.get("90-100", 0) + score_distribution.get("80-89", 0)
    if high_scores > 0:
        insights.append(f"{high_scores} of your resumes score 80+ on ATS systems.")

    return insights
