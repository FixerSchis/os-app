import pytest
from flask import url_for

from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType
from models.enums import CharacterAuditAction, CharacterStatus
from models.tools.character import Character, CharacterAuditLog, CharacterBackground
from models.tools.character_inventory import (
    CharacterItem,
    ItemTransferRequest,
    ItemTransferRequestItem,
    ItemTransferStatus,
)


class TestItemsRoutes:
    """Test the items routes for character inventory management."""

    def test_items_list_user_view(self, test_client, regular_user, db_session):
        """Test that regular users see their character inventories."""
        # Create a character for the user
        character = Character(
            user_id=regular_user.id,
            name="Test Character",
            status=CharacterStatus.ACTIVE.value,
        )
        db_session.add(character)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        response = test_client.get("/tools/items/")
        assert response.status_code == 200
        assert b"Test Character" in response.data
        assert b"My Items" in response.data

    def test_items_list_admin_view(self, test_client, user_admin, db_session):
        """Test that admins see all character inventories."""
        # Create a character
        character = Character(
            user_id=user_admin.id,
            name="Test Character",
            status=CharacterStatus.ACTIVE.value,
        )
        db_session.add(character)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        response = test_client.get("/tools/items/")
        assert response.status_code == 200
        assert b"Items - Admin View" in response.data
        assert b"Test Character" in response.data

    def test_character_inventory_view(self, test_client, user_admin, db_session):
        """Test the character inventory admin view."""
        # Create a character
        character = Character(
            user_id=user_admin.id,
            name="Test Character",
            status=CharacterStatus.ACTIVE.value,
        )
        db_session.add(character)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        response = test_client.get(f"/tools/items/character/{character.id}/inventory")
        assert response.status_code == 200
        assert b"Test Character's Inventory" in response.data

    def test_assign_item_to_character(self, test_client, user_admin, db_session):
        """Test assigning an item to a character."""
        # Create a character
        character = Character(
            user_id=user_admin.id,
            name="Test Character",
            status=CharacterStatus.ACTIVE.value,
        )
        db_session.add(character)
        db_session.commit()

        # Create an item blueprint and item
        item_type = ItemType(name="Test Type", id_prefix="TT")
        db_session.add(item_type)
        db_session.flush()

        blueprint = ItemBlueprint(
            name="Test Item",
            blueprint_id=1,
            item_type_id=item_type.id,
            base_cost=100,
        )
        db_session.add(blueprint)
        db_session.flush()

        item = Item(blueprint_id=blueprint.id, item_id=1)
        db_session.add(item)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        # Assign item to character
        response = test_client.post(
            f"/tools/items/character/{character.id}/assign-item",
            data={"item_id": item.id},
        )
        assert response.status_code == 302  # Redirect

        # Check that item was assigned
        character_item = CharacterItem.query.filter_by(
            character_id=character.id, item_id=item.id
        ).first()
        assert character_item is not None

        # Check that audit log was created
        audit_log = CharacterAuditLog.query.filter_by(
            character_id=character.id,
            action=CharacterAuditAction.STATUS_CHANGE.value,
        ).first()
        assert audit_log is not None
        assert "Item assigned" in audit_log.changes

    def test_remove_item_from_character(self, test_client, user_admin, db_session):
        """Test removing an item from a character."""
        # Create a character
        character = Character(
            user_id=user_admin.id,
            name="Test Character",
            status=CharacterStatus.ACTIVE.value,
        )
        db_session.add(character)
        db_session.commit()

        # Create an item blueprint and item
        item_type = ItemType(name="Test Type", id_prefix="TT")
        db_session.add(item_type)
        db_session.flush()

        blueprint = ItemBlueprint(
            name="Test Item",
            blueprint_id=1,
            item_type_id=item_type.id,
            base_cost=100,
        )
        db_session.add(blueprint)
        db_session.flush()

        item = Item(blueprint_id=blueprint.id, item_id=1)
        db_session.add(item)
        db_session.commit()

        # Assign item to character
        character_item = CharacterItem(
            character_id=character.id,
            item_id=item.id,
            assigned_by_user_id=user_admin.id,
        )
        db_session.add(character_item)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        # Remove item from character
        response = test_client.post(
            f"/tools/items/character/{character.id}/remove-item",
            data={"character_item_id": character_item.id},
        )
        assert response.status_code == 302  # Redirect

        # Check that item was removed
        character_item = CharacterItem.query.filter_by(
            character_id=character.id, item_id=item.id
        ).first()
        assert character_item is None

        # Check that audit log was created
        audit_log = CharacterAuditLog.query.filter_by(
            character_id=character.id,
            action=CharacterAuditAction.STATUS_CHANGE.value,
        ).first()
        assert audit_log is not None
        assert "Item removed" in audit_log.changes

    def test_create_transfer_request(self, test_client, regular_user, db_session):
        """Test creating a transfer request."""
        # Create two characters
        character1 = Character(
            user_id=regular_user.id,
            name="Character 1",
            status=CharacterStatus.ACTIVE.value,
        )
        character2 = Character(
            user_id=regular_user.id,
            name="Character 2",
            status=CharacterStatus.ACTIVE.value,
        )
        db_session.add(character1)
        db_session.add(character2)
        db_session.commit()

        # Create an item and assign it to character1
        item_type = ItemType(name="Test Type", id_prefix="TT")
        db_session.add(item_type)
        db_session.flush()

        blueprint = ItemBlueprint(
            name="Test Item",
            blueprint_id=1,
            item_type_id=item_type.id,
            base_cost=100,
        )
        db_session.add(blueprint)
        db_session.flush()

        item = Item(blueprint_id=blueprint.id, item_id=1)
        db_session.add(item)
        db_session.commit()

        character_item = CharacterItem(
            character_id=character1.id,
            item_id=item.id,
            assigned_by_user_id=regular_user.id,
        )
        db_session.add(character_item)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        # Create transfer request
        response = test_client.post(
            "/tools/items/transfer-request",
            data={
                "requesting_character_id": character1.id,
                "target_character_id": character2.id,
                "item_ids[]": [character_item.id],
                "notes": "Test transfer request",
            },
        )
        assert response.status_code == 302  # Redirect

        # Check that transfer request was created
        transfer_request = ItemTransferRequest.query.filter_by(
            requesting_character_id=character1.id,
            target_character_id=character2.id,
        ).first()
        assert transfer_request is not None
        assert transfer_request.status == ItemTransferStatus.PENDING
        assert transfer_request.notes == "Test transfer request"

        # Check that transfer request item was created
        transfer_item = ItemTransferRequestItem.query.filter_by(
            transfer_request_id=transfer_request.id
        ).first()
        assert transfer_item is not None

    def test_process_transfer_request_approve(self, test_client, user_admin, db_session):
        """Test approving a transfer request."""
        # Create two characters
        character1 = Character(
            user_id=user_admin.id,
            name="Character 1",
            status=CharacterStatus.ACTIVE.value,
        )
        character2 = Character(
            user_id=user_admin.id,
            name="Character 2",
            status=CharacterStatus.ACTIVE.value,
        )
        db_session.add(character1)
        db_session.add(character2)
        db_session.commit()

        # Create an item and assign it to character1
        item_type = ItemType(name="Test Type", id_prefix="TT")
        db_session.add(item_type)
        db_session.flush()

        blueprint = ItemBlueprint(
            name="Test Item",
            blueprint_id=1,
            item_type_id=item_type.id,
            base_cost=100,
        )
        db_session.add(blueprint)
        db_session.flush()

        item = Item(blueprint_id=blueprint.id, item_id=1)
        db_session.add(item)
        db_session.commit()

        character_item = CharacterItem(
            character_id=character1.id,
            item_id=item.id,
            assigned_by_user_id=user_admin.id,
        )
        db_session.add(character_item)
        db_session.commit()

        # Create transfer request
        transfer_request = ItemTransferRequest(
            requesting_character_id=character1.id,
            target_character_id=character2.id,
            status=ItemTransferStatus.PENDING,
        )
        db_session.add(transfer_request)
        db_session.flush()

        transfer_item = ItemTransferRequestItem(
            transfer_request_id=transfer_request.id,
            character_item_id=character_item.id,
        )
        db_session.add(transfer_item)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        # Approve transfer request
        response = test_client.post(
            f"/tools/items/transfer-request/{transfer_request.id}/process",
            data={
                "action": "approve",
                "notes": "Approved transfer",
            },
        )
        assert response.status_code == 302  # Redirect

        # Check that transfer request was approved
        db_session.refresh(transfer_request)
        assert transfer_request.status == ItemTransferStatus.APPROVED
        assert transfer_request.notes == "Approved transfer"

        # Check that item was transferred
        character_item = CharacterItem.query.filter_by(
            character_id=character2.id, item_id=item.id
        ).first()
        assert character_item is not None

        # Check that audit logs were created
        audit_logs = CharacterAuditLog.query.filter_by(
            character_id=character1.id,
            action=CharacterAuditAction.STATUS_CHANGE.value,
        ).all()
        assert len(audit_logs) > 0
        assert any("Item transferred to" in log.changes for log in audit_logs)

        audit_logs = CharacterAuditLog.query.filter_by(
            character_id=character2.id,
            action=CharacterAuditAction.STATUS_CHANGE.value,
        ).all()
        assert len(audit_logs) > 0
        assert any("Item received from" in log.changes for log in audit_logs)

    def test_process_transfer_request_deny(self, test_client, user_admin, db_session):
        """Test denying a transfer request."""
        # Create two characters
        character1 = Character(
            user_id=user_admin.id,
            name="Character 1",
            status=CharacterStatus.ACTIVE.value,
        )
        character2 = Character(
            user_id=user_admin.id,
            name="Character 2",
            status=CharacterStatus.ACTIVE.value,
        )
        db_session.add(character1)
        db_session.add(character2)
        db_session.commit()

        # Create an item and assign it to character1
        item_type = ItemType(name="Test Type", id_prefix="TT")
        db_session.add(item_type)
        db_session.flush()

        blueprint = ItemBlueprint(
            name="Test Item",
            blueprint_id=1,
            item_type_id=item_type.id,
            base_cost=100,
        )
        db_session.add(blueprint)
        db_session.flush()

        item = Item(blueprint_id=blueprint.id, item_id=1)
        db_session.add(item)
        db_session.commit()

        character_item = CharacterItem(
            character_id=character1.id,
            item_id=item.id,
            assigned_by_user_id=user_admin.id,
        )
        db_session.add(character_item)
        db_session.commit()

        # Create transfer request
        transfer_request = ItemTransferRequest(
            requesting_character_id=character1.id,
            target_character_id=character2.id,
            status=ItemTransferStatus.PENDING,
        )
        db_session.add(transfer_request)
        db_session.flush()

        transfer_item = ItemTransferRequestItem(
            transfer_request_id=transfer_request.id,
            character_item_id=character_item.id,
        )
        db_session.add(transfer_item)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        # Deny transfer request
        response = test_client.post(
            f"/tools/items/transfer-request/{transfer_request.id}/process",
            data={
                "action": "deny",
                "notes": "Denied transfer",
            },
        )
        assert response.status_code == 302  # Redirect

        # Check that transfer request was denied
        db_session.refresh(transfer_request)
        assert transfer_request.status == ItemTransferStatus.DENIED
        assert transfer_request.notes == "Denied transfer"

        # Check that item was not transferred
        character_item = CharacterItem.query.filter_by(
            character_id=character1.id, item_id=item.id
        ).first()
        assert character_item is not None

        character_item = CharacterItem.query.filter_by(
            character_id=character2.id, item_id=item.id
        ).first()
        assert character_item is None

    def test_api_characters(self, test_client, regular_user, db_session):
        """Test the API endpoint for character search."""
        # Create a character
        character = Character(
            user_id=regular_user.id,
            name="Test Character",
            status=CharacterStatus.ACTIVE.value,
        )
        db_session.add(character)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        # Test character search
        response = test_client.get("/tools/items/api/characters?q=Test")
        assert response.status_code == 200

        data = response.get_json()
        assert "results" in data
        assert len(data["results"]) > 0
        assert "Test Character" in data["results"][0]["text"]

    def test_api_active_character_items(self, test_client, regular_user, db_session):
        """Test the API active character items endpoint."""
        # Create a character for the user
        character = Character(
            user_id=regular_user.id,
            character_id=1,
            name="Test Character",
            status=CharacterStatus.ACTIVE.value,
        )
        db_session.add(character)
        db_session.flush()

        # Set as active character
        regular_user.active_character_id = character.id
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        response = test_client.get("/tools/items/api/active-character-items")
        assert response.status_code == 200
        assert response.content_type == "application/json"

        data = response.get_json()
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_api_active_character_items_no_active_character(
        self, test_client, regular_user, db_session
    ):
        """Test the API active character items endpoint when user has no active character."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = regular_user.id
            sess["_fresh"] = True

        response = test_client.get("/tools/items/api/active-character-items")
        assert response.status_code == 200
        assert response.content_type == "application/json"

        data = response.get_json()
        assert "results" in data
        assert data["results"] == []


class TestCharacterBackgroundAuditLogging:
    """Test character background audit logging functionality."""

    def test_background_changes_audit_logged(self, test_client, user_admin, db_session):
        """Test that background changes are audit logged during character editing."""
        # Create required faction and species for the test
        from models.database.faction import Faction
        from models.database.species import Species

        faction = Faction(
            name="Test Faction",
            wiki_slug="test-faction",
            allow_player_characters=True,
        )
        db_session.add(faction)
        db_session.flush()

        species = Species(
            name="Test Species",
            wiki_page="test-species",
            body_hits_type="locational",
            body_hits=3,
            death_count=1,
            permitted_factions_list=[faction.id],
        )
        db_session.add(species)
        db_session.flush()

        # Create a character with the required faction and species
        character = Character(
            user_id=user_admin.id,
            name="Test Character",
            status=CharacterStatus.ACTIVE.value,
            faction_id=faction.id,
            species_id=species.id,
        )
        db_session.add(character)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        # Get the edit form to get required fields
        response = test_client.get(f"/characters/{character.id}/edit")
        assert response.status_code == 200

        # Submit form with background changes
        data = {
            "name": "Test Character",
            "pronouns_subject": "they",
            "pronouns_object": "them",
            "faction": str(faction.id),
            "species_id": str(species.id),
            "background": "Updated background content",
            "goals": "Updated goals content",
            "concept": "Updated concept content",
        }

        response = test_client.post(f"/characters/{character.id}/edit", data=data)
        assert response.status_code == 302  # Redirect

        # Check that audit log was created for background changes
        audit_logs = CharacterAuditLog.query.filter_by(
            character_id=character.id,
            action=CharacterAuditAction.EDIT.value,
        ).all()

        background_changes = [
            log
            for log in audit_logs
            if "Background updated" in log.changes
            or "Goals updated" in log.changes
            or "Concept updated" in log.changes
        ]
        assert len(background_changes) > 0

    def test_background_review_audit_logged(self, test_client, user_admin, db_session):
        """Test that background changes during review are audit logged."""
        # Create a character
        character = Character(
            user_id=user_admin.id,
            name="Test Character",
            status=CharacterStatus.ACTIVE.value,
        )
        db_session.add(character)
        db_session.commit()

        # Create a background review entry
        background = CharacterBackground(
            character_id=character.id,
            background="Original background",
            goals="Original goals",
            concept="Original concept",
            needs_review=True,
        )
        db_session.add(background)
        db_session.commit()

        with test_client.session_transaction() as sess:
            sess["_user_id"] = user_admin.id
            sess["_fresh"] = True

        # Submit review with changes
        response = test_client.post(
            f"/tools/character-backgrounds/{background.id}/review",
            data={
                "background": "Updated background during review",
                "goals": "Updated goals during review",
                "concept": "Updated concept during review",
                "mark_done": "on",
            },
        )
        assert response.status_code == 302  # Redirect

        # Check that audit log was created for background changes
        audit_logs = CharacterAuditLog.query.filter_by(
            character_id=character.id,
            action=CharacterAuditAction.EDIT.value,
        ).all()

        background_changes = [
            log
            for log in audit_logs
            if "Background updated during review" in log.changes
            or "Goals updated during review" in log.changes
            or "Concept updated during review" in log.changes
        ]
        assert len(background_changes) > 0

        # Check that character was updated
        db_session.refresh(character)
        assert character.background == "Updated background during review"
        assert character.goals == "Updated goals during review"
        assert character.concept == "Updated concept during review"
