from models.enums import ScienceType


def login_user(client, email, password):
    from models.tools.user import User

    user = User.query.filter_by(email=email).first()
    print("DEBUG: login_user: user found in db:", user is not None)
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def login_rules_team_user(test_client, rules_team_user):
    with test_client.session_transaction() as session:
        session["_user_id"] = rules_team_user.id
        session["_fresh"] = True


class TestSkillsList:
    """Test the skills list endpoint."""

    def test_skills_list_unauthorized(self, test_client, db):
        """Test skills list without authentication."""
        response = test_client.get("/db/skills/")
        assert response.status_code == 200
        assert b"Test Skill" in response.data or b"Skills" in response.data

    def test_skills_list_authorized(self, test_client, rules_team_user, db):
        """Test skills list with rules team user."""
        login_rules_team_user(test_client, rules_team_user)
        response = test_client.get("/db/skills/")
        assert response.status_code == 200
        assert b"Test Skill" in response.data or b"Skills" in response.data

    def test_skills_list_with_skills(self, test_client, skill, db):
        """Test skills list with existing skills."""
        response = test_client.get("/db/skills/")
        assert response.status_code == 200
        assert skill.name.encode() in response.data


class TestEditSkill:
    """Test the edit skill endpoints."""

    def test_edit_skill_get_unauthorized(self, test_client, skill, db):
        """Test edit skill GET without authentication."""
        response = test_client.get(f"/db/skills/{skill.id}/edit")
        assert response.status_code == 302  # Redirect to login

    def test_edit_skill_get_wrong_role(self, test_client, regular_user, skill, db, wiki_index_page):
        """Test edit skill GET with wrong role."""
        login_user(test_client, regular_user.email, "password123")
        response = test_client.get(f"/db/skills/{skill.id}/edit")
        assert response.status_code == 302  # Redirect to index

    def test_edit_skill_get_authorized(self, test_client, rules_team_user, skill, db):
        login_rules_team_user(test_client, rules_team_user)
        response = test_client.get(f"/db/skills/{skill.id}/edit")
        assert response.status_code == 200
        assert bytes(skill.name, "utf-8") in response.data

    def test_edit_skill_get_nonexistent(self, test_client, rules_team_user, db):
        login_rules_team_user(test_client, rules_team_user)
        response = test_client.get("/db/skills/99999/edit")
        assert response.status_code == 404

    def test_edit_skill_post_unauthorized(self, test_client, skill, db):
        """Test edit skill POST without authentication."""
        response = test_client.post(
            f"/db/skills/{skill.id}/edit",
            data={
                "name": "Updated Skill",
                "description": "Updated description",
                "skill_type": "GENERAL",
                "base_cost": "15",
            },
        )
        assert response.status_code == 302  # Redirect to login

    def test_edit_skill_post_wrong_role(
        self, test_client, regular_user, skill, db, wiki_index_page
    ):
        """Test edit skill POST with wrong role."""
        login_user(test_client, regular_user.email, "password123")
        response = test_client.post(
            f"/db/skills/{skill.id}/edit",
            data={
                "name": "Updated Skill",
                "description": "Updated description",
                "skill_type": "GENERAL",
                "base_cost": "15",
            },
        )
        assert response.status_code == 302  # Redirect to index

    def test_edit_skill_post_valid_data(
        self, test_client, rules_team_user, skill, species, faction, character_tag, db
    ):
        login_rules_team_user(test_client, rules_team_user)
        response = test_client.post(
            f"/db/skills/{skill.id}/edit",
            data={
                "name": "Updated Skill",
                "description": "Updated description",
                "skill_type": "ENGINEERING",
                "base_cost": "15",
                "can_purchase_multiple": "on",
                "cost_increases": "on",
                "required_species": [str(species.id)],
                "required_factions": [str(faction.id)],
                "required_character_tags": [str(character_tag.id)],
                "prerequisite_skills": [],
                "science_type": "GENERIC",
                "character_sheet_values": '{"test": "value"}',
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Updated Skill" in response.data

    def test_edit_skill_post_missing_required_fields(self, test_client, rules_team_user, skill, db):
        login_rules_team_user(test_client, rules_team_user)
        response = test_client.post(
            f"/db/skills/{skill.id}/edit",
            data={"name": "", "description": "", "skill_type": "", "base_cost": ""},
        )
        assert response.status_code == 200
        assert b"Name, description, skill type, and base cost are required." in response.data

    def test_edit_skill_post_with_prerequisite(
        self, test_client, rules_team_user, skill, prerequisite_skill, db
    ):
        login_rules_team_user(test_client, rules_team_user)
        response = test_client.post(
            f"/db/skills/{skill.id}/edit",
            data={
                "name": "Updated Skill",
                "description": "Updated description",
                "skill_type": "GENERAL",
                "base_cost": "15",
                "prerequisite_skills": [str(prerequisite_skill.id)],
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Updated Skill" in response.data

    def test_edit_skill_post_with_new_tag(self, test_client, rules_team_user, skill, db):
        login_rules_team_user(test_client, rules_team_user)
        response = test_client.post(
            f"/db/skills/{skill.id}/edit",
            data={
                "name": "Updated Skill",
                "description": "Updated description",
                "skill_type": "GENERAL",
                "base_cost": "15",
                "new_character_tag": "New Tag",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Updated Skill" in response.data

    def test_edit_skill_post_with_character_sheet_values(
        self, test_client, rules_team_user, skill, db
    ):
        login_rules_team_user(test_client, rules_team_user)
        character_sheet_values = {"test_field": "test_value", "another_field": 123}
        response = test_client.post(
            f"/db/skills/{skill.id}/edit",
            data={
                "name": "Updated Skill",
                "description": "Updated description",
                "skill_type": "GENERAL",
                "base_cost": "15",
                "character_sheet_values": str(character_sheet_values),
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Updated Skill" in response.data


class TestNewSkill:
    """Test the new skill endpoints."""

    def test_new_skill_get_unauthorized(self, test_client, db):
        """Test new skill GET without authentication."""
        response = test_client.get("/db/skills/new")
        assert response.status_code == 302  # Redirect to login

    def test_new_skill_get_wrong_role(self, test_client, regular_user, db, wiki_index_page):
        """Test new skill GET with wrong role."""
        login_user(test_client, regular_user.email, "password123")
        response = test_client.get("/db/skills/new")
        assert response.status_code == 302  # Redirect to index

    def test_new_skill_get_authorized(self, test_client, rules_team_user, db):
        login_rules_team_user(test_client, rules_team_user)
        response = test_client.get("/db/skills/new")
        assert response.status_code == 200
        assert b"Create Skill" in response.data

    def test_new_skill_post_unauthorized(self, test_client, db):
        """Test new skill POST without authentication."""
        response = test_client.post(
            "/db/skills/new",
            data={
                "name": "New Skill",
                "description": "New skill description",
                "skill_type": "GENERAL",
                "base_cost": "10",
            },
        )
        assert response.status_code == 302  # Redirect to login

    def test_new_skill_post_wrong_role(self, test_client, regular_user, db, wiki_index_page):
        """Test new skill POST with wrong role."""
        login_user(test_client, regular_user.email, "password123")
        response = test_client.post(
            "/db/skills/new",
            data={
                "name": "Test Skill",
                "description": "Test description",
                "skill_type": "GENERAL",
                "base_cost": "10",
            },
        )
        assert response.status_code == 302  # Redirect to index

    def test_new_skill_post_valid_data(
        self, test_client, rules_team_user, species, faction, character_tag, db
    ):
        login_rules_team_user(test_client, rules_team_user)
        response = test_client.post(
            "/db/skills/new",
            data={
                "name": "New Skill",
                "description": "New skill description",
                "skill_type": "GENERAL",
                "base_cost": "10",
                "can_purchase_multiple": "on",
                "cost_increases": "on",
                "required_species": [str(species.id)],
                "required_factions": [str(faction.id)],
                "required_character_tags": [str(character_tag.id)],
                "prerequisite_skills": [],
                "science_type": "GENERIC",
                "character_sheet_values": '{"test": "value"}',
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"New Skill" in response.data

    def test_new_skill_post_missing_required_fields(self, test_client, rules_team_user, db):
        login_rules_team_user(test_client, rules_team_user)
        response = test_client.post(
            "/db/skills/new",
            data={"name": "", "description": "", "skill_type": "", "base_cost": ""},
        )
        assert response.status_code == 200
        assert b"Name, description, skill type, and base cost are required." in response.data

    def test_new_skill_post_with_prerequisite(
        self, test_client, rules_team_user, skill, prerequisite_skill, db
    ):
        login_rules_team_user(test_client, rules_team_user)
        response = test_client.post(
            "/db/skills/new",
            data={
                "name": "New Skill",
                "description": "New skill description",
                "skill_type": "GENERAL",
                "base_cost": "10",
                "prerequisite_skills": [str(prerequisite_skill.id)],
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"New skill description" in response.data

    def test_new_skill_post_with_new_tag(self, test_client, rules_team_user, db):
        login_rules_team_user(test_client, rules_team_user)
        response = test_client.post(
            "/db/skills/new",
            data={
                "name": "New Skill",
                "description": "New skill description",
                "skill_type": "GENERAL",
                "base_cost": "10",
                "new_character_tag": "New Tag",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"New Skill" in response.data

    def test_new_skill_post_with_character_sheet_values(self, test_client, rules_team_user, db):
        login_rules_team_user(test_client, rules_team_user)
        character_sheet_values = {"test_field": "test_value", "another_field": 123}
        response = test_client.post(
            "/db/skills/new",
            data={
                "name": "New Skill",
                "description": "New skill description",
                "skill_type": "GENERAL",
                "base_cost": "10",
                "character_sheet_values": str(character_sheet_values),
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"New Skill" in response.data
