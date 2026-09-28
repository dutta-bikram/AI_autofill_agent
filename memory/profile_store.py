import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from config import settings

class Education(BaseModel):
    institution: str = "Stanford University"
    degree: str = "B.S. in Computer Science"
    graduation_year: str = "2023"
    gpa: str = "3.85 / 4.0"

class Experience(BaseModel):
    company: str = "Apex AI Technologies"
    role: str = "Software Engineer"
    start_date: str = "2023"
    end_date: str = "Present"
    description: str = "Developed high-throughput distributed microservices, agentic workflows, and LLM-powered enterprise automation pipelines using Python, FastAPI, and Playwright."

class UserProfile(BaseModel):
    # Personal Information
    first_name: str = "Alex"
    last_name: str = "Rivera"
    full_name: str = "Alex Rivera"
    email: str = "alex.rivera@example.com"
    phone: str = "+1 (555) 234-5678"
    gender: str = "Decline to identify"
    
    # Address
    address_line1: str = "742 Evergreen Terrace"
    city: str = "San Francisco"
    state: str = "CA"
    postal_code: str = "94107"
    country: str = "United States"

    # Social & Web Links
    linkedin: str = "https://linkedin.com/in/alexrivera-ai"
    github: str = "https://github.com/alexrivera-ai"
    portfolio_website: str = "https://alexrivera.dev"
    twitter: str = "https://twitter.com/alexrivera_ai"

    # Professional & Work Status
    current_title: str = "Software Engineer"
    current_company: str = "Apex AI Technologies"
    years_of_experience: str = "4"
    skills: List[str] = Field(default_factory=lambda: [
        "Python", "FastAPI", "Playwright", "LLMs", "RAG", "LangChain", 
        "PostgreSQL", "Docker", "TypeScript", "React", "Git"
    ])
    primary_skill: str = "Python & Browser Automation"
    highest_education_level: str = "Bachelor's Degree"
    work_authorization_us: str = "Yes"
    require_visa_sponsorship: str = "No"
    notice_period: str = "2 weeks"
    desired_salary: str = "$145,000 USD / year"
    willing_to_relocate: str = "Yes"

    # Detailed structured history
    education_history: List[Education] = Field(default_factory=lambda: [Education()])
    experience_history: List[Experience] = Field(default_factory=lambda: [Experience()])

    # Custom Q&A and preferences
    custom_answers: Dict[str, str] = Field(default_factory=lambda: {
        "why_work_here": "I am passionate about applying cutting-edge AI and agentic automation to solve real-world workflows at scale.",
        "greatest_strength": "Deep expertise in full-stack Python systems, autonomous agent architectures, and resilient browser automation.",
        "biggest_challenge": "Migrated legacy synchronous crawling pipelines to asynchronous event-driven Playwright microservices, boosting throughput 4x while handling complex dynamic SPAs.",
        "referral_source": "LinkedIn Job Board"
    })

class ProfileStore:
    def __init__(self, profile_path: Optional[Path] = None):
        self.profile_path = profile_path or settings.USER_PROFILE_PATH
        self.profile = self.load()

    def load(self) -> UserProfile:
        if self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return UserProfile(**data)
            except Exception as e:
                print(f"[ProfileStore] Warning loading profile ({e}). Using default profile.")
                return UserProfile()
        else:
            default_profile = UserProfile()
            self.save(default_profile)
            return default_profile

    def save(self, profile: Optional[UserProfile] = None) -> None:
        if profile is not None:
            self.profile = profile
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.profile_path, "w", encoding="utf-8") as f:
            f.write(self.profile.model_dump_json(indent=2))

    def update(self, updates: Dict[str, Any]) -> UserProfile:
        current_data = self.profile.model_dump()
        for k, v in updates.items():
            if k in current_data:
                current_data[k] = v
            else:
                current_data["custom_answers"][k] = str(v)
        self.profile = UserProfile(**current_data)
        self.save()
        return self.profile

    def get_summary_text(self) -> str:
        """Outputs a concise markdown summary of the user's structured profile for LLM context."""
        skills_str = ", ".join(self.profile.skills)
        return (
            f"**Candidate Name**: {self.profile.full_name}\n"
            f"**Email**: {self.profile.email} | **Phone**: {self.profile.phone}\n"
            f"**Location**: {self.profile.city}, {self.profile.state}, {self.profile.country} ({self.profile.postal_code})\n"
            f"**Current Role**: {self.profile.current_title} at {self.profile.current_company}\n"
            f"**Experience**: {self.profile.years_of_experience} years | **Primary Skills**: {skills_str}\n"
            f"**Education**: {self.profile.highest_education_level} ({self.profile.education_history[0].degree} from {self.profile.education_history[0].institution})\n"
            f"**Work Authorization**: Authorized in US: {self.profile.work_authorization_us} | Visa Sponsorship: {self.profile.require_visa_sponsorship}\n"
            f"**Notice Period**: {self.profile.notice_period} | **Desired Salary**: {self.profile.desired_salary} | **Relocation**: {self.profile.willing_to_relocate}\n"
            f"**Profiles**: LinkedIn: {self.profile.linkedin}, GitHub: {self.profile.github}, Portfolio: {self.profile.portfolio_website}\n"
        )
