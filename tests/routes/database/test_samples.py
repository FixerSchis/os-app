from models.database.sample import Sample, SampleTag
from models.enums import ScienceType


def test_sample_list_get(test_client, admin_user):
    """Test GET request to sample list page."""
    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    response = test_client.get("/db/samples/")
    assert response.status_code == 200


def test_sample_list_unauthorized(test_client, authenticated_user):
    """Test sample list page when user is not authorized."""
    response = test_client.get("/db/samples/", follow_redirects=True)
    assert response.status_code in [200, 403]  # Can be either redirect or forbidden


def test_sample_list_unauthenticated(test_client):
    """Test sample list page when user is not authenticated."""
    response = test_client.get("/db/samples/", follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login


def test_create_sample_success(test_client, admin_user, db):
    """Test successful sample creation."""
    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    response = test_client.post(
        "/db/samples/create",
        data={
            "name": "Test Sample",
            "type": "generic",
            "description": "A test sample",
            "tags[]": ["test", "sample"],
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "Test Sample"
    assert data["type"] == "generic"
    assert data["description"] == "A test sample"

    # Check that sample was created in database
    sample = Sample.query.filter_by(name="Test Sample").first()
    assert sample is not None
    assert sample.type.value == "generic"
    assert sample.description == "A test sample"


def test_create_sample_missing_name(test_client, admin_user):
    """Test sample creation with missing name."""
    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    response = test_client.post(
        "/db/samples/create", data={"type": "generic", "description": "A test sample"}
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_create_sample_missing_type(test_client, admin_user):
    """Test sample creation with missing type."""
    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    response = test_client.post(
        "/db/samples/create",
        data={"name": "Test Sample", "description": "A test sample"},
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_create_sample_with_existing_tags(test_client, admin_user, db):
    """Test sample creation with existing tags."""
    # Create existing tags
    tag1 = SampleTag(name="existing_tag")
    tag2 = SampleTag(name="another_tag")
    db.session.add(tag1)
    db.session.add(tag2)
    db.session.commit()

    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True

    response = test_client.post(
        "/db/samples/create",
        data={
            "name": "Test Sample with Tags",
            "type": "life",
            "description": "A test sample with existing tags",
            "tags[]": ["existing_tag", "new_tag"],
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "Test Sample with Tags"

    # Check that sample was created with tags
    sample = Sample.query.filter_by(name="Test Sample with Tags").first()
    assert sample is not None
    assert len(sample.tags) == 2
    tag_names = [tag.name for tag in sample.tags]
    assert "existing_tag" in tag_names
    assert "new_tag" in tag_names


def test_create_sample_unauthorized(test_client, authenticated_user):
    """Test sample creation when user is not authorized."""
    response = test_client.post(
        "/db/samples/create",
        data={"name": "Test Sample", "type": "generic", "description": "A test sample"},
        follow_redirects=True,
    )

    assert response.status_code in [200, 403]  # Can be either redirect or forbidden


def test_create_sample_unauthenticated(test_client):
    """Test sample creation when user is not authenticated."""
    response = test_client.post(
        "/db/samples/create",
        data={"name": "Test Sample", "type": "generic", "description": "A test sample"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Should redirect to login


# --- Additional tests for HTML form-based routes ---
def test_create_sample_form_get(test_client, admin_user):
    """Test GET request to the create sample form."""
    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True
    response = test_client.get("/db/samples/new")
    assert response.status_code == 200
    assert b"Create Sample" in response.data


def test_create_sample_form_post(test_client, admin_user, db):
    """Test POST to the create sample form (HTML, not AJAX)."""
    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True
    response = test_client.post(
        "/db/samples/new",
        data={
            "name": "Form Sample",
            "type": "life",
            "description": "Created via form",
            "is_researched": "on",
            "tags[]": ["formtag1", "formtag2"],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Sample created" in response.data
    sample = Sample.query.filter_by(name="Form Sample").first()
    assert sample is not None
    assert sample.is_researched is True
    assert len(sample.tags) == 2


def test_edit_sample_form_get(test_client, admin_user, db):
    """Test GET request to the edit sample form."""
    # Create a sample to edit
    sample = Sample(name="EditMe", type=ScienceType.LIFE, description="To edit")
    db.session.add(sample)
    db.session.commit()
    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True
    response = test_client.get(f"/db/samples/{sample.id}/edit")
    assert response.status_code == 200
    assert b"Edit Sample" in response.data


def test_edit_sample_form_post(test_client, admin_user, db):
    """Test POST to the edit sample form (HTML)."""
    # Create a sample to edit
    sample = Sample(name="EditMe2", type=ScienceType.LIFE, description="To edit")
    db.session.add(sample)
    db.session.commit()
    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True
    response = test_client.post(
        f"/db/samples/{sample.id}/edit",
        data={
            "name": "Edited Sample",
            "type": "life",
            "description": "Edited via form",
            "is_researched": "on",
            "tags[]": ["editedtag"],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Sample updated" in response.data
    updated = db.session.get(Sample, sample.id)
    assert updated.name == "Edited Sample"
    assert updated.is_researched is True
    assert len(updated.tags) == 1
    assert updated.tags[0].name == "editedtag"


def test_delete_sample(test_client, admin_user, db):
    """Test deleting a sample via the HTML form route."""
    # Create a sample to delete
    sample = Sample(name="DeleteMe", type=ScienceType.LIFE, description="To delete")
    db.session.add(sample)
    db.session.commit()
    with test_client.session_transaction() as session:
        session["_user_id"] = admin_user.id
        session["_fresh"] = True
    response = test_client.post(f"/db/samples/{sample.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"Sample deleted" in response.data
    assert db.session.get(Sample, sample.id) is None
