import pytest
import os
from services.advanced_cv_parser.ad_cv_parse import AdvancedCVParser


@pytest.mark.integration
class TestAdvancedCVParserIntegration:
    """Integration tests for the Advanced CV Parser."""
    
    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return AdvancedCVParser()
    
    def test_parse_txt_file(self, parser):
        """Test parsing with a text file."""
        test_file_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_cv.txt"
        )
        
        if not os.path.exists(test_file_path):
            pytest.skip(f"Test file {test_file_path} not found")
        
        with open(test_file_path, "rb") as file:
            result = parser.parse_cv(file, "sample_cv.txt")
        
        # Basic structure checks
        assert "personal_information" in result
        assert "skills" in result
        assert "work_experience" in result
        assert "education" in result
        
        # Verify some content
        assert result["personal_information"]["name"] == "John Doe"
        assert result["personal_information"]["email"] == "john.doe@example.com"
        assert len(result["skills"]["technical"]) > 0
        assert len(result["work_experience"]) > 0
    
    def test_parse_minimal_cv(self, parser):
        """Test parsing with a minimal CV."""
        test_file_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "minimal_cv.txt"
        )
        
        if not os.path.exists(test_file_path):
            pytest.skip(f"Test file {test_file_path} not found")
        
        with open(test_file_path, "rb") as file:
            result = parser.parse_cv(file, "minimal_cv.txt")
        
        # Verify basic personal information
        assert result["personal_information"]["name"] == "Jane Smith"
        assert result["personal_information"]["email"] == "jane.smith@example.com"
        
        # Verify key skills
        assert "Python" in result["skills"]["technical"]
        assert "Machine Learning" in result["skills"]["technical"] or "Machine Learning" in " ".join(result["skills"]["technical"])
        assert "Communication" in result["skills"]["soft"]
    
    def test_parse_malformed_cv(self, parser):
        """Test parsing with a malformed CV."""
        test_file_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "malformed_cv.txt"
        )
        
        if not os.path.exists(test_file_path):
            pytest.skip(f"Test file {test_file_path} not found")
        
        with open(test_file_path, "rb") as file:
            result = parser.parse_cv(file, "malformed_cv.txt")
        
        # Should handle gracefully
        assert result["personal_information"]["name"] == "Alex Johnson"
        assert result["personal_information"]["email"] == "alex@example.com"
        assert isinstance(result["skills"]["technical"], list)
        assert isinstance(result["work_experience"], list)
