"""
Region Classifier Module

Classifies countries into regions for portfolio analysis.
"""

from typing import Dict, Set


class RegionClassifier:
    """Classifies countries into geographical regions."""
    
    # Region mappings
    NORTH_AMERICA: Set[str] = {"United States", "Canada"}
    
    EUROPE: Set[str] = {
        "United Kingdom", "Germany", "France", "Switzerland",
        "Netherlands", "Sweden", "Spain", "Italy", "Ireland",
        "Belgium", "Austria", "Denmark", "Finland", "Norway",
        "Portugal", "Poland", "Czech Republic"
    }
    
    ASIA: Set[str] = {
        "Japan", "China", "Hong Kong", "India", "South Korea",
        "Taiwan", "Singapore", "Thailand", "Malaysia", "Indonesia",
        "Philippines", "Vietnam"
    }
    
    OCEANIA: Set[str] = {"Australia", "New Zealand"}
    
    LATIN_AMERICA: Set[str] = {
        "Brazil", "Mexico", "Argentina", "Chile", "Colombia", "Peru"
    }
    
    MIDDLE_EAST: Set[str] = {
        "Israel", "Saudi Arabia", "United Arab Emirates", "Qatar"
    }
    
    @classmethod
    def classify(cls, country: str) -> str:
        """
        Classify a country into a region.
        
        Args:
            country: Country name
            
        Returns:
            Region name
        """
        if not isinstance(country, str):
            return "Unknown"
        
        if country in cls.NORTH_AMERICA:
            return "North America"
        if country in cls.EUROPE:
            return "Europe"
        if country in cls.ASIA:
            return "Asia"
        if country in cls.OCEANIA:
            return "Oceania"
        if country in cls.LATIN_AMERICA:
            return "Latin America"
        if country in cls.MIDDLE_EAST:
            return "Middle East"
        
        return "Other"
    
    @classmethod
    def get_all_regions(cls) -> list:
        """Get list of all defined regions."""
        return [
            "North America",
            "Europe",
            "Asia",
            "Oceania",
            "Latin America",
            "Middle East",
            "Other"
        ]
    
    @classmethod
    def get_countries_by_region(cls) -> Dict[str, Set[str]]:
        """Get dictionary mapping regions to countries."""
        return {
            "North America": cls.NORTH_AMERICA,
            "Europe": cls.EUROPE,
            "Asia": cls.ASIA,
            "Oceania": cls.OCEANIA,
            "Latin America": cls.LATIN_AMERICA,
            "Middle East": cls.MIDDLE_EAST
        }
