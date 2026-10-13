from models.database.medicaments import Medicament


def get_sample_medicament():
    medicament = Medicament(
        id=1,
        name="Radiation Nanosponges",
        wiki_slug="medicament/radiation-nanosponges",
        summary="Protects from or treats Radiation",
    )
    medicament.modes_list = [
        {"name": "TREAT", "effect": "After 1hr of Rest, treats one RADIATION Condition."},
        {
            "name": "RESIST",
            "effect": (
                "Grants MAJOR RADIATION Protection for 1hr. "
                "Roleplay Effect: You feel slightly itchy."
            ),
        },
    ]
    return medicament
