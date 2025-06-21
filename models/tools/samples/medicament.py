from models.database.medicaments import Medicament


def get_sample_medicament():
    return Medicament(id=1, name="StimPak", wiki_slug="stimpak")
