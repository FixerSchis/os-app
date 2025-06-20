from models.database.exotic_substances import ExoticSubstance
from models.enums import ScienceType

def get_sample_exotic_substance():
    """Get a sample exotic substance for template previews (not added to DB)"""
    return ExoticSubstance(
        name="Void Essence",
        type=ScienceType.ETHERIC,
        wiki_slug="void-essence"
    ) 