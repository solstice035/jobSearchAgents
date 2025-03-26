"""
CV Parser Agent

This agent provides CV parsing capabilities using advanced text extraction
and AI-powered analysis to extract structured information from CVs/resumes.
"""

import io
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, BinaryIO
from datetime import datetime

from ..base_agent import BaseAgent
from ..protocols.agent_protocol import AgentCapability, AgentStatus
from ..message_bus import Message, MessageType, MessageBus
from services.document_parser.document_parser import DocumentParser

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    np = None
    SentenceTransformer = None


class CVParserAgent(BaseAgent):
    """Agent that provides CV parsing capabilities"""

    # Class attributes for skill keywords
    TECHNICAL_SKILLS_KEYWORDS = {
        "python",
        "java",
        "javascript",
        "typescript",
        "c++",
        "c#",
        "ruby",
        "go",
        "php",
        "html",
        "css",
        "react",
        "angular",
        "vue",
        "node.js",
        "express",
        "django",
        "flask",
        "sql",
        "nosql",
        "postgresql",
        "mysql",
        "mongodb",
        "pandas",
        "numpy",
        "tensorflow",
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "terraform",
        "jenkins",
        "linux",
        "machine learning",
        "ai",
        "data science",
        "automation",
        "ci/cd",
        "git",
    }

    SOFT_SKILLS_KEYWORDS = {
        "communication",
        "teamwork",
        "leadership",
        "problem solving",
        "critical thinking",
        "time management",
        "organization",
        "adaptability",
        "creativity",
        "collaboration",
    }

    def __init__(self, message_bus: MessageBus):
        super().__init__(agent_type="cv_parser", message_bus=message_bus)

        # Initialize document parser
        self.doc_parser = DocumentParser()

        # Initialize OpenAI client if API key exists
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            from openai import OpenAI

            self.openai_client = OpenAI(api_key=self.api_key)
        else:
            self.openai_client = None
            self.logger.warning(
                "OpenAI API key not found. Advanced parsing features will be limited."
            )

        # Initialize embedding model if available
        if SentenceTransformer is not None:
            try:
                self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                # Precompute embeddings for known skills
                self.technical_skills_embeddings = {
                    skill: self.embedding_model.encode(skill)
                    for skill in self.TECHNICAL_SKILLS_KEYWORDS
                }
                self.soft_skills_embeddings = {
                    skill: self.embedding_model.encode(skill)
                    for skill in self.SOFT_SKILLS_KEYWORDS
                }
            except Exception as e:
                self.logger.warning(
                    f"Failed to initialize SentenceTransformer: {str(e)}"
                )
                self.embedding_model = None
        else:
            self.embedding_model = None

        # Register capabilities
        self._register_capabilities()

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def _register_capabilities(self):
        """Register the agent's capabilities"""
        self.register_capability(
            AgentCapability(
                name="parse_cv",
                description="Parse a CV/resume and extract structured information",
                parameters={
                    "file_content": "bytes",
                    "filename": "str",
                    "use_ai_enhancement": "bool",
                },
                required_resources=["document_parser"],
            )
        )

        self.register_capability(
            AgentCapability(
                name="get_supported_formats",
                description="Get list of supported CV file formats",
                parameters={},
                required_resources=[],
            )
        )

    async def initialize(self) -> bool:
        """Initialize the CV parser agent"""
        try:
            # Initialize base agent
            if not await super().initialize():
                return False

            # Subscribe to relevant topics
            await self.subscribe_to_topic("cv.parse")
            await self.subscribe_to_topic("cv.formats")

            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize CV parser agent: {str(e)}")
            await self.update_status(AgentStatus.ERROR, str(e))
            return False

    async def handle_message(self, message: Message) -> Dict[str, Any]:
        """Handle incoming messages"""
        try:
            if message.message_type == MessageType.COMMAND:
                return await self._handle_command(message)

            elif message.message_type == MessageType.QUERY:
                return await self._handle_query(message)

            else:
                return {
                    "status": "error",
                    "error": f"Unsupported message type: {message.message_type}",
                }

        except Exception as e:
            self.logger.error(f"Error handling message: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _handle_command(self, message: Message) -> Dict[str, Any]:
        """Handle command messages"""
        if message.topic == "cv.parse":
            # Extract file content and filename from payload
            file_content = message.payload.get("file_content")
            filename = message.payload.get("filename")
            use_ai = message.payload.get("use_ai_enhancement", False)

            if not file_content or not filename:
                return {
                    "status": "error",
                    "error": "Missing required parameters: file_content and filename",
                }

            # Update status to busy
            await self.update_status(AgentStatus.BUSY)

            try:
                # Convert bytes to file-like object
                file_obj = io.BytesIO(file_content)

                # Parse the CV
                parsed_data = await self._parse_cv(file_obj, filename, use_ai)

                # Update status back to ready
                await self.update_status(AgentStatus.READY)

                return {"status": "success", "data": parsed_data}

            except Exception as e:
                await self.update_status(AgentStatus.ERROR, str(e))
                return {"status": "error", "error": str(e)}

        return {
            "status": "error",
            "error": f"Unsupported command topic: {message.topic}",
        }

    async def _handle_query(self, message: Message) -> Dict[str, Any]:
        """Handle query messages"""
        if message.topic == "cv.formats":
            return {
                "status": "success",
                "data": {"supported_formats": ["pdf", "docx", "doc", "txt", "rtf"]},
            }

        return {"status": "error", "error": f"Unsupported query topic: {message.topic}"}

    async def _parse_cv(
        self, file_obj: BinaryIO, filename: str, use_ai: bool = False
    ) -> Dict[str, Any]:
        """
        Parse a CV file and extract structured information.

        Args:
            file_obj: File-like object containing the CV
            filename: Original filename
            use_ai: Whether to use AI enhancement for parsing

        Returns:
            Structured CV data including personal info, skills, experience, etc.
        """
        try:
            # Extract text content
            cv_text = self.doc_parser.parse_document(file_obj, filename)

            if not cv_text or len(cv_text.strip()) < 20:
                raise ValueError(
                    "Extracted text is too short or empty. Check document format."
                )

            # Extract structured data
            structured_data = self._extract_structured_data(cv_text, filename)

            # Use AI enhancement if enabled and available
            if use_ai and self.api_key and self.openai_client:
                enhanced_data = await self._enhance_with_ai(cv_text, structured_data)
                structured_data = enhanced_data

            # Add metadata
            structured_data["metadata"] = {
                "parsed_by": self.agent_id,
                "parsed_at": datetime.now().isoformat(),
                "filename": filename,
                "ai_enhanced": use_ai and self.api_key is not None,
            }

            return structured_data

        except Exception as e:
            self.logger.error(f"Error parsing CV: {str(e)}")
            raise Exception(f"Failed to parse CV: {str(e)}")

    def _extract_structured_data(
        self, cv_text: str, filename: str = ""
    ) -> Dict[str, Any]:
        """Extract structured data from CV text using rule-based methods"""
        structured_data = {
            "personal_information": {
                "name": None,
                "email": None,
                "phone": None,
                "location": None,
                "linkedin": None,
                "github": None,
                "website": None,
            },
            "skills": {"technical": [], "soft": []},
            "work_experience": [],
            "education": [],
            "certifications": [],
            "projects": [],
            "languages": [],
            "summary": None,
        }

        # Extract each component
        structured_data["personal_information"] = self._extract_personal_information(
            cv_text
        )
        structured_data["skills"] = self._extract_skills(cv_text)
        structured_data["work_experience"] = self._extract_work_experience(cv_text)
        structured_data["education"] = self._extract_education(cv_text)
        structured_data["certifications"] = self._extract_certifications(cv_text)
        structured_data["projects"] = self._extract_projects(cv_text)
        structured_data["languages"] = self._extract_languages(cv_text)
        structured_data["summary"] = self._extract_summary(cv_text)

        return structured_data

    def _apply_ai_enhancement(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply AI-powered enhancement to the structured data"""
        # This method should be implemented to apply AI-powered enhancement
        # For now, we'll just return the structured data as is
        return structured_data

    def _extract_personal_information(self, cv_text: str) -> Dict[str, Optional[str]]:
        """Extract personal information from CV text"""
        personal_info = {
            "name": None,
            "email": None,
            "phone": None,
            "location": None,
            "linkedin": None,
            "github": None,
            "website": None,
        }

        # Extract email
        email_matches = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", cv_text)
        if email_matches:
            personal_info["email"] = email_matches[0]

        # Extract phone number
        phone_patterns = [
            r"(?:\+\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){1,2}\d{3,4}[-.\s]?\d{3,4}",
            r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}",
            r"\(\d{3}\)\s*\d{3}[-.\s]?\d{4}",
            r"\d{10,12}",
        ]
        for pattern in phone_patterns:
            phone_matches = re.findall(pattern, cv_text)
            if phone_matches:
                personal_info["phone"] = phone_matches[0]
                break

        # Extract LinkedIn profile
        linkedin_patterns = [
            r"linkedin\.com/in/[\w-]+",
            r"linkedin\.com/profile/[\w-]+",
        ]
        for pattern in linkedin_patterns:
            linkedin_matches = re.findall(pattern, cv_text, re.IGNORECASE)
            if linkedin_matches:
                personal_info["linkedin"] = linkedin_matches[0]
                break

        # Extract GitHub profile
        github_matches = re.findall(r"github\.com/[\w-]+", cv_text, re.IGNORECASE)
        if github_matches:
            personal_info["github"] = github_matches[0]

        # Extract website
        website_patterns = [
            r"https?://(?!(?:www\.)?(?:linkedin\.com|github\.com))[\w.-]+\.\w{2,}(?:/\S*)?",
            r"(?:portfolio|website|site|blog):\s*(https?://[\w.-]+\.\w{2,}(?:/\S*)?)",
            r"(?:www\.)?[\w-]+\.\w{2,}(?:/\S*)?",
        ]
        for pattern in website_patterns:
            website_matches = re.findall(pattern, cv_text, re.IGNORECASE)
            if website_matches:
                for url in website_matches:
                    if isinstance(url, tuple):
                        url = url[0]
                    if (
                        "linkedin.com" not in url.lower()
                        and "github.com" not in url.lower()
                    ):
                        personal_info["website"] = url
                        break
                if personal_info["website"]:
                    break

        # Extract location
        location_patterns = [
            r"(?:Location|Address|City|Located in|Based in):\s*([A-Za-z\s]+,\s*[A-Za-z\s]+)",
            r"([A-Za-z\s]+,\s*[A-Z]{2})",
            r"([A-Za-z\s]+,\s*[A-Za-z\s]+)",
        ]
        for pattern in location_patterns:
            location_matches = re.findall(pattern, cv_text, re.IGNORECASE)
            if location_matches:
                personal_info["location"] = location_matches[0].strip()
                break

        # Extract name from first few lines
        lines = cv_text.split("\n")
        for i in range(min(5, len(lines))):
            line = lines[i].strip()
            if line and not any(
                term in line.lower() for term in ["resume", "cv", "curriculum", "vitae"]
            ):
                if (
                    re.match(r"^[A-Z][a-z]+(?: [A-Z][a-z]+){1,2}$", line)
                    and "@" not in line
                    and "://" not in line
                    and not re.search(r"\d", line)
                ):
                    personal_info["name"] = line
                    break

        return personal_info

    def _extract_skills(self, cv_text: str) -> Dict[str, List[str]]:
        """Extract technical and soft skills using rule-based and embedding-based methods"""
        skills = {"technical": [], "soft": []}

        # Extract skills section
        skills_section = self._extract_section(
            cv_text,
            [
                "skills",
                "technical skills",
                "technical expertise",
                "core competencies",
                "proficiencies",
                "qualifications",
            ],
            [
                "experience",
                "work experience",
                "employment",
                "education",
                "projects",
                "certifications",
                "awards",
            ],
        )

        if skills_section:
            # Extract technical skills
            technical_skills = set()
            for skill in self.TECHNICAL_SKILLS_KEYWORDS:
                if re.search(
                    r"\b" + re.escape(skill) + r"\b", skills_section, re.IGNORECASE
                ):
                    technical_skills.add(skill)

            # Extract soft skills
            soft_skills = set()
            for skill in self.SOFT_SKILLS_KEYWORDS:
                if re.search(
                    r"\b" + re.escape(skill) + r"\b", skills_section, re.IGNORECASE
                ):
                    soft_skills.add(skill)

            # Extract skills from bullet points
            bullet_skills = re.findall(
                r"(?:^|\n)(?:\s*[\•\-\*\✓\+\>\★]|\d+\.)\s*([^,\n]+)(?:,|$|\n)",
                skills_section,
            )

            # Extract skills from comma-separated lists
            comma_skills = []
            comma_lists = re.findall(
                r"(?:^|\n)([^\•\-\*\✓\+\>\★\n]+(?:,[^,\n]+){2,})(?:$|\n)",
                skills_section,
            )
            for skill_list in comma_lists:
                comma_skills.extend([s.strip() for s in skill_list.split(",")])

            # Categorize extracted skills
            for skill in bullet_skills + comma_skills:
                skill_lower = skill.strip().lower()
                if any(
                    tech_skill in skill_lower
                    for tech_skill in self.TECHNICAL_SKILLS_KEYWORDS
                ):
                    technical_skills.add(skill_lower)
                elif any(
                    soft_skill in skill_lower
                    for soft_skill in self.SOFT_SKILLS_KEYWORDS
                ):
                    soft_skills.add(skill_lower)

            skills["technical"] = list(technical_skills)
            skills["soft"] = list(soft_skills)

        # Use embedding model if available
        if self.embedding_model:
            candidate_text = skills_section if skills_section else cv_text
            candidates = re.split(r"[\n,;]+", candidate_text)
            for candidate in candidates:
                candidate = candidate.strip()
                if len(candidate) < 3:
                    continue
                try:
                    candidate_embedding = self.embedding_model.encode(candidate)
                except Exception:
                    continue

                # Compare with technical skills
                for tech_skill, tech_emb in self.technical_skills_embeddings.items():
                    similarity = self._cosine_similarity(candidate_embedding, tech_emb)
                    if similarity > 0.65:
                        skills["technical"].append(tech_skill)

                # Compare with soft skills
                for soft_skill, soft_emb in self.soft_skills_embeddings.items():
                    similarity = self._cosine_similarity(candidate_embedding, soft_emb)
                    if similarity > 0.65:
                        skills["soft"].append(soft_skill)

        # Standardize and deduplicate skills
        skills["technical"] = list(
            dict.fromkeys(
                [self._standardize_skill(skill) for skill in skills["technical"]]
            )
        )
        skills["soft"] = list(
            dict.fromkeys([self._standardize_skill(skill) for skill in skills["soft"]])
        )

        return skills

    def _cosine_similarity(self, vec1, vec2) -> float:
        """Compute cosine similarity between two vectors"""
        if np is None:
            return 0.0
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
        return dot_product / (norm_vec1 * norm_vec2)

    def _standardize_skill(self, skill: str) -> str:
        """Standardize the skill name format"""
        common_capitalizations = {
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "nodejs": "Node.js",
            "node.js": "Node.js",
            "react": "React",
            "react.js": "React",
            "reactjs": "React",
            "vue": "Vue.js",
            "vuejs": "Vue.js",
            "angular": "Angular",
            "angularjs": "AngularJS",
            "jquery": "jQuery",
            "php": "PHP",
            "html": "HTML",
            "css": "CSS",
            "sass": "SASS",
            "scss": "SCSS",
            "aws": "AWS",
            "azure": "Azure",
            "gcp": "GCP",
            "graphql": "GraphQL",
            "postgresql": "PostgreSQL",
            "mysql": "MySQL",
            "mongodb": "MongoDB",
            "nosql": "NoSQL",
            "sql": "SQL",
            "restful": "RESTful",
            "rest": "REST",
            "api": "API",
            "json": "JSON",
            "xml": "XML",
            "ci/cd": "CI/CD",
            "cicd": "CI/CD",
            "docker": "Docker",
            "kubernetes": "Kubernetes",
            "python": "Python",
            "java": "Java",
            "c#": "C#",
            "c++": "C++",
            "ruby": "Ruby",
            "rails": "Rails",
            "ruby on rails": "Ruby on Rails",
            "go": "Go",
            "golang": "Go",
            "scala": "Scala",
            "swift": "Swift",
            "kotlin": "Kotlin",
            "rust": "Rust",
            "r": "R",
            "matlab": "MATLAB",
            "numpy": "NumPy",
            "pandas": "pandas",
            "scikit-learn": "scikit-learn",
            "tensorflow": "TensorFlow",
            "pytorch": "PyTorch",
            "keras": "Keras",
            "git": "Git",
            "github": "GitHub",
            "gitlab": "GitLab",
        }
        skill_lower = skill.lower()
        if skill_lower in common_capitalizations:
            return common_capitalizations[skill_lower]
        return skill.title()

    def _extract_section(
        self, text: str, section_names: List[str], end_sections: List[str]
    ) -> Optional[str]:
        """
        Extract a section from CV text.

        Args:
            text: The CV text
            section_names: Possible names for the target section
            end_sections: Names of sections that indicate the end of the target section

        Returns:
            Extracted section text or None if not found
        """
        section_pattern = "|".join(section_names)
        end_pattern = "|".join(end_sections)

        header_formats = [
            rf"(?:^|\n)(?:#+\s*)?({section_pattern})(?:[\s:-]+|\n+)",
            rf"(?:^|\n)(?:#+\s*)?({section_pattern})(?:\s*[-–]|\s+–\s+|\s*:|\s*$|\n+)",
        ]

        for format_pattern in header_formats:
            matches = list(re.finditer(format_pattern, text, re.IGNORECASE))
            for match in matches:
                start_pos = match.end()
                end_matches = list(
                    re.finditer(
                        rf"(?:^|\n)(?:#+\s*)?({end_pattern})(?:\s*[-–]|\s+–\s+|\s*:|\s*$|\n+)",
                        text[start_pos:],
                        re.IGNORECASE,
                    )
                )

                if end_matches:
                    end_pos = start_pos + end_matches[0].start()
                    section_text = text[start_pos:end_pos].strip()
                    return section_text
                else:
                    section_text = text[start_pos:].strip()
                    return section_text

        return None

    async def _enhance_with_ai(
        self, cv_text: str, structured_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance the extracted data using OpenAI's language model.

        Args:
            cv_text: The CV text
            structured_data: The structured data extracted using rule-based methods

        Returns:
            Enhanced structured data
        """
        if not self.openai_client:
            return structured_data

        prompt = f"""
        Please analyze this CV text and extract structured information as accurately as possible.
        
        I've already extracted some information using rule-based methods, but I need your help to improve it and fill in any gaps.
        
        Here is what I've extracted so far:
        ```
        {json.dumps(structured_data, indent=2)}
        ```
        
        Please analyze the following CV text and provide an improved structured extraction in the same JSON format.
        Focus especially on:
        1. Correctly identifying personal information
        2. Separating technical skills from soft skills
        3. Extracting work experience with proper company, position, and date information
        4. Correctly parsing education details
        5. Adding any missing certifications, projects, or languages
        
        Only include information that is clearly stated in the CV. Do not invent or hallucinate information.
        
        Here is the CV text:
        ```
        {cv_text}
        ```
        
        Return just the JSON with no additional explanation. Keep the same JSON structure as shown above.
        """

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert CV analyzer that extracts structured information with high accuracy.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            enhanced_data = json.loads(response.choices[0].message.content)
            validated_data = self._validate_and_sanitize(enhanced_data, structured_data)
            return validated_data

        except Exception as e:
            self.logger.error(f"Error enhancing data with AI: {str(e)}")
            self.logger.info("Falling back to rule-based extraction results")
            return structured_data

    def _validate_and_sanitize(
        self, enhanced_data: Dict[str, Any], original_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate and sanitize the AI-enhanced data to ensure it matches our expected structure.

        Args:
            enhanced_data: The data returned by the AI
            original_data: The original rule-based extraction for fallback

        Returns:
            Validated and sanitized data
        """
        validated = original_data.copy()

        if "personal_information" in enhanced_data:
            for key in validated["personal_information"]:
                if (
                    key in enhanced_data["personal_information"]
                    and enhanced_data["personal_information"][key]
                ):
                    validated["personal_information"][key] = enhanced_data[
                        "personal_information"
                    ][key]

        if "skills" in enhanced_data:
            if (
                "technical" in enhanced_data["skills"]
                and enhanced_data["skills"]["technical"]
            ):
                validated["skills"]["technical"] = enhanced_data["skills"]["technical"]
            if "soft" in enhanced_data["skills"] and enhanced_data["skills"]["soft"]:
                validated["skills"]["soft"] = enhanced_data["skills"]["soft"]

        if "work_experience" in enhanced_data and enhanced_data["work_experience"]:
            validated["work_experience"] = enhanced_data["work_experience"]

        if "education" in enhanced_data and enhanced_data["education"]:
            validated["education"] = enhanced_data["education"]

        if "certifications" in enhanced_data and enhanced_data["certifications"]:
            validated["certifications"] = enhanced_data["certifications"]

        if "projects" in enhanced_data and enhanced_data["projects"]:
            validated["projects"] = enhanced_data["projects"]

        if "languages" in enhanced_data and enhanced_data["languages"]:
            validated["languages"] = enhanced_data["languages"]

        if "summary" in enhanced_data and enhanced_data["summary"]:
            validated["summary"] = enhanced_data["summary"]

        validated["metadata"] = {
            "parsing_method": (
                "ai_enhanced" if enhanced_data != original_data else "rule_based"
            ),
            "timestamp": datetime.now().isoformat(),
        }

        return validated

    def _extract_work_experience(self, cv_text: str) -> List[Dict[str, Any]]:
        """Extract work experience from CV text"""
        experience_list = []
        experience_section = self._extract_section(
            cv_text,
            [
                "experience",
                "work experience",
                "professional experience",
                "employment history",
                "career history",
                "work history",
                "professional history",
            ],
            [
                "education",
                "skills",
                "projects",
                "certifications",
                "awards",
                "publications",
                "references",
                "languages",
            ],
        )

        if not experience_section:
            return experience_list

        # Try to split the experience section into individual job entries
        experience_chunks = []

        # First, try to split by date patterns
        date_pattern = r"(?:^|\n)(?:\s*)?(?:\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}-\d{1,2}-\d{2,4}|\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4})\s*[-–—]\s*(?:\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}-\d{1,2}-\d{2,4}|\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4}|Present|Current|Now)"
        date_matches = list(
            re.finditer(date_pattern, experience_section, re.IGNORECASE)
        )

        if len(date_matches) > 1:
            for i in range(len(date_matches)):
                start_pos = date_matches[i].start()
                end_pos = (
                    date_matches[i + 1].start()
                    if i < len(date_matches) - 1
                    else len(experience_section)
                )
                chunk = experience_section[start_pos:end_pos].strip()
                if chunk:
                    experience_chunks.append(chunk)

        # If date pattern splitting didn't work, try to split by job title patterns
        if not experience_chunks:
            job_title_pattern = r"(?:^|\n)(?:\s*)?(?:[A-Z][a-z]+\s*)+(?:Developer|Engineer|Manager|Director|Consultant|Analyst|Designer|Administrator|Specialist|Coordinator|Assistant|Lead|Head|Officer|Architect)"
            job_matches = list(re.finditer(job_title_pattern, experience_section))

            if len(job_matches) > 1:
                for i in range(len(job_matches)):
                    start_pos = job_matches[i].start()
                    end_pos = (
                        job_matches[i + 1].start()
                        if i < len(job_matches) - 1
                        else len(experience_section)
                    )
                    chunk = experience_section[start_pos:end_pos].strip()
                    if chunk:
                        experience_chunks.append(chunk)

        # If still no chunks found, try another approach with bullet points
        if not experience_chunks:
            # Look for company names with locations
            company_pattern = r"(?:^|\n)(?:\s*)?([A-Z][A-Za-z0-9\s&.,]+)(?:,|\s+[-–—]\s+|\s*\()([A-Za-z\s,]+)(?:\)|$|\n)"
            company_matches = list(re.finditer(company_pattern, experience_section))

            if len(company_matches) > 1:
                for i in range(len(company_matches)):
                    start_pos = company_matches[i].start()
                    end_pos = (
                        company_matches[i + 1].start()
                        if i < len(company_matches) - 1
                        else len(experience_section)
                    )
                    chunk = experience_section[start_pos:end_pos].strip()
                    if chunk:
                        experience_chunks.append(chunk)

        # Process each experience chunk
        for chunk in experience_chunks:
            experience_item = self._parse_experience_chunk(chunk)
            if experience_item.get("position") or experience_item.get("company"):
                experience_list.append(experience_item)

        return experience_list

    def _parse_experience_chunk(self, chunk: str) -> Dict[str, Any]:
        """Parse a chunk of text containing a job experience"""
        experience = {
            "position": None,
            "company": None,
            "location": None,
            "duration": None,
            "start_date": None,
            "end_date": None,
            "responsibilities": [],
        }

        lines = chunk.split("\n")
        clean_lines = [line.strip() for line in lines if line.strip()]
        if not clean_lines:
            return experience

        # Extract position and company from the first few lines
        for i in range(min(3, len(clean_lines))):
            line = clean_lines[i]

            # Look for position-company patterns
            position_company_match = re.search(
                r"([A-Za-z\s&]+)(?:\s+at|\s+[-–—]\s+|\s*,\s*)([A-Za-z0-9\s&.,]+)", line
            )
            if position_company_match:
                potential_position = position_company_match.group(1).strip()
                if re.search(
                    r"\b(?:Developer|Engineer|Manager|Director|Consultant|Analyst|Designer|Administrator|Specialist|Coordinator|Assistant|Lead|Head|Officer|Architect)\b",
                    potential_position,
                    re.IGNORECASE,
                ):
                    experience["position"] = potential_position
                    experience["company"] = position_company_match.group(2).strip()
                    break

            # If no position-company pattern found, look for patterns in isolation
            if not experience["position"] and re.search(
                r"\b(?:Developer|Engineer|Manager|Director|Consultant|Analyst|Designer|Administrator|Specialist|Coordinator|Assistant|Lead|Head|Officer|Architect)\b",
                line,
                re.IGNORECASE,
            ):
                experience["position"] = line
            elif not experience["company"] and re.search(
                r"[A-Z][a-z]+(?:\s+[A-Z][a-z]*)+|[A-Z]{2,}", line
            ):
                experience["company"] = line

        # Extract location
        location_pattern = r"(?:[A-Za-z\s]+,\s*[A-Z]{2}|[A-Za-z\s]+,\s*[A-Za-z\s]+)"
        for line in clean_lines[:4]:  # Check first few lines
            location_match = re.search(location_pattern, line)
            if location_match:
                potential_location = location_match.group(0).strip()
                if (
                    experience["company"]
                    and potential_location not in experience["company"]
                ):
                    experience["location"] = potential_location
                    break

        # Extract duration with start and end dates
        date_pattern = r"((?:\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}-\d{1,2}-\d{2,4}|\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4}))\s*[-–—]\s*((?:\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}-\d{1,2}-\d{2,4}|\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4}|Present|Current|Now))"
        for line in clean_lines[:4]:  # Check first few lines
            date_match = re.search(date_pattern, line, re.IGNORECASE)
            if date_match:
                experience["duration"] = line[
                    date_match.start() : date_match.end()
                ].strip()
                experience["start_date"] = date_match.group(1).strip()
                experience["end_date"] = date_match.group(2).strip()
                break

        # Extract responsibilities
        responsibility_lines = []
        responsibility_mode = False

        for line in clean_lines:
            # Skip header lines we've already processed
            if (
                (experience["position"] and line == experience["position"])
                or (experience["company"] and line == experience["company"])
                or (experience["duration"] and experience["duration"] in line)
            ):
                continue

            # Look for bullet points
            if (
                line.startswith("•")
                or line.startswith("-")
                or line.startswith("*")
                or re.match(r"^\d+\.", line)
            ):
                responsibility_mode = True
                clean_line = re.sub(r"^[\•\-\*\✓\+\>\★]|\d+\.\s*", "", line).strip()
                if clean_line:
                    responsibility_lines.append(clean_line)
            # Or consider paragraph text
            elif responsibility_mode or len(clean_lines) > 5:
                if len(line) > 20 and not any(
                    date_marker in line.lower()
                    for date_marker in [
                        "january",
                        "february",
                        "march",
                        "april",
                        "may",
                        "june",
                        "july",
                        "august",
                        "september",
                        "october",
                        "november",
                        "december",
                    ]
                ):
                    responsibility_lines.append(line)

        # If we have too many responsibilities, keep only the first 10
        if responsibility_lines:
            experience["responsibilities"] = responsibility_lines[:10]

        return experience

    def _extract_education(self, cv_text: str) -> List[Dict[str, Any]]:
        """Extract education from CV text"""
        education_list = []
        education_section = self._extract_section(
            cv_text,
            [
                "education",
                "academic background",
                "academic qualifications",
                "educational background",
                "educational qualifications",
            ],
            [
                "experience",
                "skills",
                "projects",
                "certifications",
                "awards",
                "publications",
                "references",
            ],
        )

        if not education_section:
            return education_list

        degree_patterns = [
            r"(?:B\.?S\.?|Bachelor of Science|Bachelor\'s)",
            r"(?:B\.?A\.?|Bachelor of Arts)",
            r"(?:M\.?S\.?|Master of Science|Master\'s)",
            r"(?:M\.?B\.?A\.?|Master of Business Administration)",
            r"(?:M\.?A\.?|Master of Arts)",
            r"(?:Ph\.?D\.?|Doctor of Philosophy|Doctorate)",
            r"(?:B\.?Tech\.?|Bachelor of Technology)",
            r"(?:M\.?Tech\.?|Master of Technology)",
            r"(?:B\.?E\.?|Bachelor of Engineering)",
            r"(?:Associate\'s|Associate|A\.?A\.?|A\.?S\.?)",
        ]
        combined_pattern = "|".join(f"({pattern})" for pattern in degree_patterns)

        education_chunks = []
        current_chunk = ""
        lines = education_section.split("\n")
        in_education_item = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if re.search(combined_pattern, line, re.IGNORECASE) or re.search(
                r"(?:University|College|Institute|School)", line, re.IGNORECASE
            ):
                if in_education_item and current_chunk:
                    education_chunks.append(current_chunk)
                    current_chunk = ""
                in_education_item = True

            if in_education_item:
                current_chunk += line + "\n"

        if current_chunk:
            education_chunks.append(current_chunk)

        for chunk in education_chunks:
            education_item = self._parse_education_chunk(chunk)
            if education_item.get("institution") or education_item.get("degree"):
                education_list.append(education_item)

        return education_list

    def _parse_education_chunk(self, chunk: str) -> Dict[str, Any]:
        """Parse a chunk of text containing education information"""
        education = {
            "institution": None,
            "degree": None,
            "field": None,
            "duration": None,
            "gpa": None,
            "location": None,
            "achievements": [],
        }

        lines = chunk.split("\n")
        clean_lines = [line.strip() for line in lines if line.strip()]
        if not clean_lines:
            return education

        # Extract institution
        for i in range(min(2, len(clean_lines))):
            if re.search(
                r"(?:University|College|Institute|School)",
                clean_lines[i],
                re.IGNORECASE,
            ):
                education["institution"] = clean_lines[i]
                break

        # Extract degree and field
        degree_patterns = [
            r"(?:B\.?S\.?|Bachelor of Science|Bachelor\'s)",
            r"(?:B\.?A\.?|Bachelor of Arts)",
            r"(?:M\.?S\.?|Master of Science|Master\'s)",
            r"(?:M\.?B\.?A\.?|Master of Business Administration)",
            r"(?:M\.?A\.?|Master of Arts)",
            r"(?:Ph\.?D\.?|Doctor of Philosophy|Doctorate)",
            r"(?:B\.?Tech\.?|Bachelor of Technology)",
            r"(?:M\.?Tech\.?|Master of Technology)",
            r"(?:B\.?E\.?|Bachelor of Engineering)",
            r"(?:Associate\'s|Associate|A\.?A\.?|A\.?S\.?)",
            r"(?:High School Diploma)",
        ]
        combined_pattern = "|".join(f"({pattern})" for pattern in degree_patterns)

        for line in clean_lines:
            degree_match = re.search(combined_pattern, line, re.IGNORECASE)
            if degree_match:
                degree_type = next((m for m in degree_match.groups() if m), None)
                if degree_type:
                    education["degree"] = degree_type
                    after_degree = line[degree_match.end() :].strip()
                    field = re.sub(
                        r"^in\s+", "", after_degree, flags=re.IGNORECASE
                    ).strip()
                    field = re.sub(r",?\s*(?:19[8-9]\d|20\d{2}).*$", "", field).strip()
                    if field:
                        education["field"] = field
                    break

        # Extract duration
        for line in clean_lines:
            date_match = re.search(
                r"((?:\d{1,2}/\d{1,2}|\d{1,2}-\d{1,2}|\d{1,2}\.\d{1,2}|\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4})\s*[-–—]\s*(?:\d{1,2}/\d{1,2}|\d{1,2}-\d{1,2}|\d{1,2}\.\d{1,2}|\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4}|Present|Current|Now))",
                line,
                re.IGNORECASE,
            )
            if date_match:
                education["duration"] = date_match.group(1).strip()
                break

            year_match = re.search(
                r"(?:graduate|graduation|completed|expected|class of|completed).*?((?:19[8-9]\d|20\d{2}))",
                line,
                re.IGNORECASE,
            )
            if year_match:
                education["duration"] = year_match.group(1).strip()
                break

        # Extract GPA
        gpa_match = re.search(
            r"(?:gpa|grade point average)[:\s]*([0-4]\.[0-9]+|[0-9]\.[0-9]+/[0-9]\.[0-9]+)",
            chunk,
            re.IGNORECASE,
        )
        if gpa_match:
            education["gpa"] = gpa_match.group(1).strip()

        # Extract location
        location_match = re.search(r"(?:[^,]+, [A-Z]{2}|[^,]+, [A-Za-z]+)", chunk)
        if location_match:
            possible_location = location_match.group(0).strip()
            if not education.get("field") or possible_location != education["field"]:
                education["location"] = possible_location

        # Extract achievements
        achievements = []
        bullet_points = re.findall(r"(?:^|\n)\s*(?:[\•\-\*\✓\+\>\★])\s*([^\n]+)", chunk)
        if bullet_points:
            achievements.extend([point.strip() for point in bullet_points])

        honor_matches = re.findall(
            r"(?:honor|award|scholar|dean\'s list|distinction)[^\n,;.]*",
            chunk,
            re.IGNORECASE,
        )
        if honor_matches:
            achievements.extend([honor.strip() for honor in honor_matches])

        if achievements:
            education["achievements"] = achievements

        return education

    def _extract_certifications(self, cv_text: str) -> List[Dict[str, Any]]:
        """Extract certifications from CV text"""
        certification_list = []
        certs_section = self._extract_section(
            cv_text,
            [
                "certifications",
                "certificates",
                "professional certifications",
                "licenses",
                "credentials",
                "qualifications",
            ],
            [
                "experience",
                "education",
                "skills",
                "projects",
                "awards",
                "publications",
                "references",
            ],
        )

        if not certs_section:
            return certification_list

        lines = certs_section.split("\n")
        current_cert = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if re.match(
                r"^(certifications|certificates|credentials|qualifications|licenses)[\s:]*$",
                line,
                re.IGNORECASE,
            ):
                continue

            clean_line = re.sub(r"^\s*[\•\-\*\✓\+\>\★]|\d+\.\s*", "", line).strip()
            if len(clean_line) > 10 and (
                re.search(
                    r"certificate|certification|certified|license",
                    clean_line,
                    re.IGNORECASE,
                )
                or re.search(r"\b[A-Z]{2,}(?:-[A-Z]+)?\b", clean_line)
            ):
                current_cert = {"name": clean_line, "issuer": None, "date": None}

                # Extract issuer
                issuer_match = re.search(
                    r"(?:by|from|issued by)\s+([A-Za-z][\w\s&,.]+)",
                    clean_line,
                    re.IGNORECASE,
                )
                if issuer_match:
                    current_cert["issuer"] = issuer_match.group(1).strip()
                    current_cert["name"] = clean_line[: issuer_match.start()].strip()

                # Extract date
                date_match = re.search(
                    r"(?:19[8-9]\d|20\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4})",
                    clean_line,
                )
                if date_match:
                    current_cert["date"] = date_match.group(0).strip()
                    if not issuer_match:
                        current_cert["name"] = clean_line[: date_match.start()].strip()

                certification_list.append(current_cert)

            elif current_cert:
                if re.search(
                    r"^(?:issued by|issuer|certification authority|issued)[\s:]",
                    line,
                    re.IGNORECASE,
                ):
                    issuer_text = re.sub(
                        r"^(?:issued by|issuer|certification authority|issued)[\s:]*",
                        "",
                        line,
                        re.IGNORECASE,
                    ).strip()
                    current_cert["issuer"] = issuer_text
                elif re.search(
                    r"^(?:date|issued|received|completed|obtained)[\s:]",
                    line,
                    re.IGNORECASE,
                ):
                    date_text = re.sub(
                        r"^(?:date|issued|received|completed|obtained)[\s:]*",
                        "",
                        line,
                        re.IGNORECASE,
                    ).strip()
                    current_cert["date"] = date_text

        return certification_list

    def _extract_projects(self, cv_text: str) -> List[Dict[str, Any]]:
        """Extract projects from CV text"""
        project_list = []
        projects_section = self._extract_section(
            cv_text,
            [
                "projects",
                "personal projects",
                "academic projects",
                "key projects",
                "relevant projects",
            ],
            [
                "experience",
                "education",
                "skills",
                "certifications",
                "awards",
                "publications",
                "references",
            ],
        )

        if not projects_section:
            return project_list

        bullet_matches = re.finditer(
            r"(?:^|\n)\s*(?:[\•\-\*\✓\+\>\★]|\d+\.)\s*([^\n]+(?:\n(?!\s*[\•\-\*\✓\+\>\★]|\d+\.).*)*)",
            projects_section,
        )

        for match in bullet_matches:
            project_text = match.group(1).strip()
            if len(project_text) < 15:
                continue

            project = {"name": None, "description": None, "technologies": []}
            lines = project_text.split("\n")

            if lines:
                project["name"] = lines[0].strip()
                if len(lines) > 1:
                    project["description"] = " ".join(
                        [line.strip() for line in lines[1:]]
                    )

                # Extract technologies
                tech_match = re.search(
                    r"(?:technologies|tech stack|tools|languages|frameworks|built with|developed using|created using|implemented using)[\s:]+([^\n]+)",
                    project_text,
                    re.IGNORECASE,
                )
                if tech_match:
                    tech_text = tech_match.group(1)
                    project["technologies"] = [
                        tech.strip() for tech in re.split(r"[,;]", tech_text)
                    ]
                else:
                    # Try to find technologies in the text
                    tech_keywords = [
                        "python",
                        "java",
                        "javascript",
                        "typescript",
                        "c++",
                        "c#",
                        "ruby",
                        "go",
                        "php",
                        "swift",
                        "react",
                        "angular",
                        "vue",
                        "node.js",
                        "jquery",
                        "html",
                        "css",
                        "sass",
                        "bootstrap",
                        "tailwind",
                        "django",
                        "flask",
                        "spring",
                        "asp.net",
                        "laravel",
                        "express",
                        "postgresql",
                        "mysql",
                        "mongodb",
                        "sqlite",
                        "redis",
                        "firebase",
                        "aws",
                        "azure",
                        "gcp",
                        "docker",
                        "kubernetes",
                        "git",
                        "github",
                    ]
                    found_techs = []
                    for tech in tech_keywords:
                        if re.search(
                            r"\b" + re.escape(tech) + r"\b", project_text, re.IGNORECASE
                        ):
                            found_techs.append(tech)
                    if found_techs:
                        project["technologies"] = [
                            self._standardize_skill(tech) for tech in found_techs
                        ]

            project_list.append(project)

        return project_list

    def _extract_languages(self, cv_text: str) -> List[Dict[str, Any]]:
        """Extract languages from CV text"""
        languages = []
        lang_section = self._extract_section(
            cv_text,
            ["languages", "language skills", "language proficiency"],
            [
                "experience",
                "education",
                "skills",
                "projects",
                "certifications",
                "awards",
                "publications",
                "references",
            ],
        )

        if not lang_section:
            return languages

        for line in lang_section.split("\n"):
            line = line.strip()
            if not line or line.lower() == "languages":
                continue

            clean_line = re.sub(r"^\s*[\•\-\*\✓\+\>\★]|\d+\.\s*", "", line).strip()
            lang_match = re.match(
                r"([A-Za-z\s]+)(?:\s*[\(:]?\s*([A-Za-z\s]+)[\)]?)?", clean_line
            )
            if lang_match:
                language = lang_match.group(1).strip()
                proficiency = (
                    lang_match.group(2).strip() if lang_match.group(2) else "Fluent"
                )
                languages.append({"language": language, "proficiency": proficiency})

        return languages

    def _extract_summary(self, cv_text: str) -> Optional[str]:
        """Extract summary/profile section from CV text"""
        summary_section = self._extract_section(
            cv_text,
            [
                "summary",
                "profile",
                "professional summary",
                "career summary",
                "personal statement",
                "objective",
                "career objective",
                "about me",
                "overview",
                "professional profile",
            ],
            [
                "experience",
                "education",
                "skills",
                "projects",
                "certifications",
                "awards",
                "publications",
                "references",
            ],
        )

        if summary_section:
            summary = re.sub(
                r"^(?:summary|profile|professional summary|career summary|personal statement|objective|career objective|about me|overview|professional profile)[\s:]*",
                "",
                summary_section,
                re.IGNORECASE,
            ).strip()
            return summary

        return None
