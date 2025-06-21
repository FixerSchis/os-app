from models.database.medicaments import Medicament


def test_new_medicament(db):
    """Test creation of a new Medicament."""
    medicament_name = "Test-o-Cure"
    wiki_slug = "test-o-cure"

    medicament = Medicament(name=medicament_name, wiki_slug=wiki_slug)

    db.session.add(medicament)
    db.session.commit()

    # Retrieve and assert
    retrieved_medicament = Medicament.query.filter_by(name=medicament_name).first()

    assert retrieved_medicament is not None
    assert retrieved_medicament.name == medicament_name
    assert retrieved_medicament.wiki_slug == wiki_slug
    assert retrieved_medicament.id is not None
