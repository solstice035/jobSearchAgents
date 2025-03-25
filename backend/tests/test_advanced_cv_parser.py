import pytest
import os
import io
from unittest.mock import MagicMock, patch
from services.advanced_cv_parser.advanced_cv_parser import AdvancedCVParser


class TestAdvancedCVParser:
    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return AdvancedCVParser()
    
    @pytest.fixture
    def sample_cv_text(self):
        """Sample CV text for testing extraction methods."""
        return """
        John Doe
        john.doe@example.com
        (123) 456-7890
        San Francisco, CA
        https://johndoe.com
        linkedin.com/in/johndoe
        github.com/johndoe
        
        SUMMARY
        Experienced software engineer with a focus on web development and cloud solutions.
        
        SKILLS
        • JavaScript, Python, React, Node.js
        • AWS, Docker, Kubernetes
        • Leadership, Communication, Teamwork
        
        EXPERIENCE
        Senior Software Engineer, TechCorp Inc., San Francisco, CA
        January 2020 - Present
        • Developed scalable web applications using React and Node.js
        • Led a team of 5 engineers on cloud migration projects
        • Implemented CI/CD pipelines using GitHub Actions
        
        Software Developer, StartupXYZ, Oakland, CA
        March 2017 - December 2019
        • Built and maintained RESTful APIs
        • Collaborated with UX designers to implement responsive interfaces
        
        EDUCATION
        Master of Computer Science, Stanford University
        2015 - 2017
        GPA: 3.8/4.0
        
        Bachelor of Science in Computer Engineering, UC Berkeley
        2011 - 2015
        
        CERTIFICATIONS
        AWS Certified Solutions Architect, 2021
        Issued by Amazon Web Services
        
        LANGUAGES
        English (Native), Spanish (Intermediate), French (Basic)
        
        PROJECTS
        Personal Website (2022)
        • Built with React, Next.js, and Tailwind CSS
        • Features a blog, portfolio, and contact form
        """
    
    def test_extract_personal_information(self, parser, sample_cv_text):
        """Test extraction of personal information."""
        result = parser._extract_personal_information(sample_cv_text)
        
        assert result["name"] == "John Doe"
        assert result["email"] == "john.doe@example.com"
        assert result["phone"] == "(123) 456-7890"
        assert result["location"] == "San Francisco, CA"
        assert result["linkedin"] == "linkedin.com/in/johndoe"
        assert result["github"] == "github.com/johndoe"
        assert result["website"] == "https://johndoe.com"

    def test_extract_skills(self, parser, sample_cv_text):
        """Test extraction of skills."""
        result = parser._extract_skills(sample_cv_text)
        
        # Test technical skills extraction
        assert "JavaScript" in result["technical"]
        assert "Python" in result["technical"]
        assert "React" in result["technical"]
        assert "Node.js" in result["technical"]
        assert "AWS" in result["technical"]
        assert "Docker" in result["technical"]
        
        # Test soft skills extraction
        assert "Leadership" in result["soft"]
        assert "Communication" in result["soft"]
        assert "Teamwork" in result["soft"]

    def test_extract_work_experience(self, parser, sample_cv_text):
        """Test extraction of work experience."""
        result = parser._extract_work_experience(sample_cv_text)
        
        assert len(result) == 2  # Two job entries
        
        # Check first job
        assert result[0]["position"] == "Senior Software Engineer"
        assert result[0]["company"] == "TechCorp Inc."
        assert result[0]["location"] == "San Francisco, CA"
        assert result[0]["duration"] == "January 2020 - Present"
        assert len(result[0]["responsibilities"]) == 3
        
        # Check second job
        assert result[1]["position"] == "Software Developer"
        assert result[1]["company"] == "StartupXYZ"
        assert result[1]["location"] == "Oakland, CA"
        assert result[1]["duration"] == "March 2017 - December 2019"
        assert len(result[1]["responsibilities"]) == 2

    def test_extract_education(self, parser, sample_cv_text):
        """Test extraction of education."""
        result = parser._extract_education(sample_cv_text)
        
        assert len(result) == 2  # Two education entries
        
        # Check first education entry
        assert result[0]["institution"] == "Stanford University"
        assert result[0]["degree"] == "Master of Computer Science"
        assert result[0]["duration"] == "2015 - 2017"
        assert result[0]["gpa"] == "3.8/4.0"
        
        # Check second education entry
        assert result[1]["institution"] == "UC Berkeley"
        assert result[1]["degree"] == "Bachelor of Science"
        assert result[1]["field"] == "Computer Engineering"
        assert result[1]["duration"] == "2011 - 2015"

    def test_extract_certifications(self, parser, sample_cv_text):
        """Test extraction of certifications."""
        result = parser._extract_certifications(sample_cv_text)
        
        assert len(result) == 1
        assert result[0]["name"] == "AWS Certified Solutions Architect"
        assert result[0]["date"] == "2021"
        assert result[0]["issuer"] == "Amazon Web Services"

    def test_extract_languages(self, parser, sample_cv_text):
        """Test extraction of languages."""
        result = parser._extract_languages(sample_cv_text)
        
        assert len(result) == 3
        
        assert result[0]["language"] == "English"
        assert result[0]["proficiency"] == "Native"
        
        assert result[1]["language"] == "Spanish"
        assert result[1]["proficiency"] == "Intermediate"
        
        assert result[2]["language"] == "French"
        assert result[2]["proficiency"] == "Basic"

    def test_extract_projects(self, parser, sample_cv_text):
        """Test extraction of projects."""
        result = parser._extract_projects(sample_cv_text)
        
        assert len(result) == 1
        assert result[0]["name"] == "Personal Website (2022)"
        assert "React" in result[0]["technologies"]
        assert len(result[0]["technologies"]) >= 2  # At least React and CSS

    def test_extract_summary(self, parser, sample_cv_text):
        """Test extraction of summary."""
        result = parser._extract_summary(sample_cv_text)
        
        assert "Experienced software engineer" in result
        assert "web development" in result

    def test_parse_cv_integration(self, parser, sample_cv_text):
        """Test the complete CV parsing process with a file."""
        # Create a sample CV file in memory
        file_obj = io.BytesIO(sample_cv_text.encode('utf-8'))
        
        # Mock the document parser to return our sample text
        with patch.object(parser.base_parser, 'parse_document', return_value=sample_cv_text):
            result = parser.parse_cv(file_obj, "sample_cv.pdf")
        
        # Verify the structure of the result
        assert "personal_information" in result
        assert "skills" in result
        assert "work_experience" in result
        assert "education" in result
        assert "certifications" in result
        assert "languages" in result
        assert "projects" in result
        assert "summary" in result
        
        # Check that personal info is extracted correctly
        assert result["personal_information"]["name"] == "John Doe"
        assert result["personal_information"]["email"] == "john.doe@example.com"
        
        # Check that we have the right number of entries in each section
        assert len(result["skills"]["technical"]) >= 6
        assert len(result["skills"]["soft"]) >= 3
        assert len(result["work_experience"]) == 2
        assert len(result["education"]) == 2
        assert len(result["certifications"]) == 1
        assert len(result["languages"]) == 3
        assert len(result["projects"]) == 1

    @pytest.mark.skipif(AdvancedCVParser().embedding_model is None, 
                        reason="Sentence transformer not available")
    def test_embedding_based_skill_extraction(self, parser, sample_cv_text):
        """Test embedding-based skill extraction if available."""
        # This test will be skipped if embedding model isn't available
        
        # Add a skill that's semantically similar but not exactly matching our keywords
        modified_cv = sample_cv_text + "\nFamiliar with cloud infrastructure management"
        
        result = parser._extract_skills(modified_cv)
        
        # Check if semantically similar terms are matched via embeddings
        assert any(item for item in ["AWS", "GCP", "Azure"] if item in result["technical"])

    def test_empty_cv_text(self, parser):
        """Test handling of empty CV text."""
        with pytest.raises(ValueError):
            parser.parse_cv(io.BytesIO(b""), "empty.pdf")

    def test_minimal_cv(self, parser):
        """Test parsing with minimal information."""
        minimal_cv = "John Smith\njohn@example.com\nSoftware Developer"
        
        with patch.object(parser.base_parser, 'parse_document', return_value=minimal_cv):
            result = parser.parse_cv(io.BytesIO(b"minimal"), "minimal.txt")
        
        assert result["personal_information"]["name"] == "John Smith"
        assert result["personal_information"]["email"] == "john@example.com"

    def test_document_parser_error(self, parser):
        """Test handling of document parser errors."""
        with patch.object(parser.base_parser, 'parse_document', side_effect=Exception("Parser error")):
            with pytest.raises(ValueError) as excinfo:
                parser.parse_cv(io.BytesIO(b"content"), "error.pdf")
            
            assert "Failed to parse CV" in str(excinfo.value)

    def test_malformed_sections(self, parser):
        """Test handling of malformed sections."""
        malformed_cv = """
        John Doe
        john@example.com
        
        SKILLS
        (no actual skills listed)
        
        EXPERIENCE
        (empty experience section)
        
        EDUCATION
        Some College
        """
        
        with patch.object(parser.base_parser, 'parse_document', return_value=malformed_cv):
            result = parser.parse_cv(io.BytesIO(b"malformed"), "malformed.txt")
        
        # Should handle empty sections gracefully
        assert result["skills"]["technical"] == []
        assert result["skills"]["soft"] == []
        assert result["work_experience"] == []
        assert len(result["education"]) <= 1

    def test_openai_enhancement_disabled(self, parser, sample_cv_text):
        """Test that OpenAI enhancement is not used by default."""
        with patch.object(parser.base_parser, 'parse_document', return_value=sample_cv_text):
            with patch.object(parser, '_enhance_with_ai') as mock_enhance:
                parser.parse_cv(io.BytesIO(b"content"), "cv.pdf")
                mock_enhance.assert_not_called()

    @patch.dict(os.environ, {"USE_LLM_ENHANCEMENT": "true"})
    def test_openai_enhancement_enabled(self, parser, sample_cv_text):
        """Test that OpenAI enhancement is used when enabled."""
        # Mock the OpenAI client
        parser.api_key = "test_key"
        parser.openai_client = MagicMock()
        
        # Setup the mock response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = '{}'
        mock_response.choices = [mock_choice]
        parser.openai_client.chat.completions.create.return_value = mock_response
        
        with patch.object(parser.base_parser, 'parse_document', return_value=sample_cv_text):
            with patch.object(parser, '_enhance_with_ai', wraps=parser._enhance_with_ai) as mock_enhance:
                parser.parse_cv(io.BytesIO(b"content"), "cv.pdf")
                mock_enhance.assert_called_once()
