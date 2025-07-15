import pytest
from src.config.settings import Settings

def test_settings_initialization():
    """Test that settings can be initialized"""
    settings = Settings()
    assert settings.chunk_size == 1000
    assert settings.chunk_overlap == 200
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000

def test_settings_environment_defaults():
    """Test default values"""
    settings = Settings()
    assert settings.chroma_host == "localhost"
    assert settings.chroma_port == 8000
    assert settings.temperature == 0.7
