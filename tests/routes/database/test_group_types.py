import pytest

from models.database.group_type import GroupType


class TestGroupTypeRoutes:
    def test_list_group_types_authenticated(self, test_client, authenticated_user):
        """Test that authenticated users can view group types list."""
        response = test_client.get("/db/group-types/")
        assert response.status_code == 200
        assert b"Group Types" in response.data

    def test_list_group_types_unauthenticated(self, test_client):
        """Test that unauthenticated users are redirected to login."""
        response = test_client.get("/db/group-types/")
        assert response.status_code == 302  # Redirect to login

    def test_create_group_type_rules_team_required(self, test_client, authenticated_user):
        """Test that non-rules-team users cannot access create page."""
        response = test_client.get("/db/group-types/create")
        assert response.status_code == 403  # Forbidden

    def test_create_group_type_rules_team_allowed(self, test_client, rules_team_user):
        """Test that rules team users can access create page."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(rules_team_user.id)
            sess["_fresh"] = True
        response = test_client.get("/db/group-types/create")
        assert response.status_code == 200
        assert b"Create Group Type" in response.data

    def test_create_group_type_post_success(self, test_client, rules_team_user):
        """Test successful group type creation."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(rules_team_user.id)
            sess["_fresh"] = True
        data = {
            "name": "Test Group Type",
            "description": "A test group type",
            "income_items_discount": "50",
            "income_substances": "on",
            "income_substance_cost": "10",
            "income_medicaments": "on",
            "income_medicament_cost": "5",
            "items_ratio": "50",
            "chits_ratio": "50",
        }
        response = test_client.post("/db/group-types/create", data=data)
        assert response.status_code == 302  # Redirect after success

        # Verify the group type was created
        group_type = GroupType.query.filter_by(name="Test Group Type").first()
        assert group_type is not None
        assert group_type.description == "A test group type"
        assert group_type.income_items_discount == 0.5
        assert group_type.income_substances is True
        assert group_type.income_distribution_dict == {"items": 50, "chits": 50}

    def test_create_group_type_duplicate_name(self, test_client, rules_team_user, db):
        """Test that duplicate names are rejected."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(rules_team_user.id)
            sess["_fresh"] = True
        # Create first group type
        group_type1 = GroupType(
            name="Duplicate Name",
            description="First",
            income_items_list=[],
            income_items_discount=0.5,
            income_substances=False,
            income_substance_cost=0,
            income_medicaments=False,
            income_medicament_cost=0,
            income_distribution_dict={},
        )
        db.session.add(group_type1)
        db.session.commit()

        # Try to create second with same name
        data = {
            "name": "Duplicate Name",
            "description": "Second",
            "income_items_discount": "50",
            "income_substances": "",
            "income_substance_cost": "0",
            "income_medicaments": "",
            "income_medicament_cost": "0",
            "items_ratio": "0",
            "chits_ratio": "0",
        }
        response = test_client.post("/db/group-types/create", data=data)
        assert response.status_code == 302  # Redirect after error

        # Verify only one group type exists
        group_types = GroupType.query.filter_by(name="Duplicate Name").all()
        assert len(group_types) == 1

    def test_edit_group_type_rules_team_required(self, test_client, authenticated_user, db):
        """Test that non-rules-team users cannot access edit page."""
        group_type = GroupType(
            name="Test Type",
            description="Test",
            income_items_list=[],
            income_items_discount=0.5,
            income_substances=False,
            income_substance_cost=0,
            income_medicaments=False,
            income_medicament_cost=0,
            income_distribution_dict={},
        )
        db.session.add(group_type)
        db.session.commit()

        response = test_client.get(f"/db/group-types/{group_type.id}/edit")
        assert response.status_code == 403  # Forbidden

    def test_edit_group_type_success(self, test_client, rules_team_user, db):
        """Test successful group type editing."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(rules_team_user.id)
            sess["_fresh"] = True
        group_type = GroupType(
            name="Original Name",
            description="Original",
            income_items_list=[],
            income_items_discount=0.5,
            income_substances=False,
            income_substance_cost=0,
            income_medicaments=False,
            income_medicament_cost=0,
            income_distribution_dict={},
        )
        db.session.add(group_type)
        db.session.commit()

        data = {
            "name": "Updated Name",
            "description": "Updated description",
            "income_items_discount": "75",
            "income_substances": "on",
            "income_substance_cost": "15",
            "income_medicaments": "",
            "income_medicament_cost": "0",
            "items_ratio": "60",
            "chits_ratio": "40",
        }
        response = test_client.post(f"/db/group-types/{group_type.id}/edit", data=data)
        assert response.status_code == 302  # Redirect after success

        # Verify the group type was updated
        db.session.refresh(group_type)
        assert group_type.name == "Updated Name"
        assert group_type.description == "Updated description"
        assert group_type.income_items_discount == 0.75
        assert group_type.income_substances is True
        assert group_type.income_distribution_dict == {"items": 60, "chits": 40}
