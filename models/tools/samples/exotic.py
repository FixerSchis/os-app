from models.database.exotic_substances import ExoticSubstance
from models.enums import ScienceType


def get_sample_exotic_substance():
    """Get a sample exotic substance for template previews (not added to DB)"""
    return ExoticSubstance(
        name="Quark Plasma",
        type=ScienceType.ETHERIC,
        wiki_slug="exotic/quark-plasma",
        used_on="Devices",
        effect=(
            "Allows an item to use its powers without spending charges, but it becomes Broken "
            "when the duration expires"
        ),
        duration="5 minutes",
    )
