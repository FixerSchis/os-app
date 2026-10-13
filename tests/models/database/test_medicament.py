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
    assert retrieved_medicament.modes_list == []


def test_medicament_rules(db):
    medicament = Medicament(
        name="Rules-o-Cure",
        wiki_slug="rules-o-cure",
        summary="Treats things",
        effect="Shared rules.",
    )
    medicament.modes_list = [
        {"name": "TREAT", "effect": "Treats one condition."},
        {"name": "RESIST", "effect": "Protects for 1hr."},
    ]
    db.session.add(medicament)
    db.session.commit()

    db.session.expire_all()
    retrieved = Medicament.query.filter_by(name="Rules-o-Cure").first()
    assert retrieved.summary == "Treats things"
    assert retrieved.effect == "Shared rules."
    assert [mode["name"] for mode in retrieved.modes_list] == ["TREAT", "RESIST"]

    retrieved.modes_list = []
    assert retrieved.modes is None
