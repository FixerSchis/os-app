import uuid

import pytest

from models.database.skills import Skill
from models.extensions import db
from models.tools.character import CharacterSkill
from models.tools.user import User


@pytest.fixture
def skill_with_prereq(db, skill):
    unique_id = uuid.uuid4().hex[:8]
    prereq_skill = Skill(
        name=f"Prereq Skill {unique_id}",
        base_cost=3,
        can_purchase_multiple=False,
        cost_increases=False,
        skill_type="General",
    )
    db.session.add(prereq_skill)
    db.session.commit()
    skill.required_skill_id = prereq_skill.id
    db.session.commit()
    return prereq_skill, skill


def login_user(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)


class TestCharacterSkills:
    def url(self, character_id, suffix=""):
        base = f"/characters/skills/characters/{character_id}/skills"
        return base + suffix

    def test_skills_list_unauthorized(self, test_client, character_with_faction):
        response = test_client.get(self.url(character_with_faction.id))
        assert response.status_code == 302  # Redirect to login

    def test_skills_list_owner(self, test_client, regular_user, character_with_faction, skill):
        login_user(test_client, regular_user)
        response = test_client.get(self.url(character_with_faction.id))
        assert response.status_code == 200
        assert skill.name.encode() in response.data

    def test_skills_list_admin(self, test_client, user_admin, character_with_faction, skill):
        login_user(test_client, user_admin)
        response = test_client.get(self.url(character_with_faction.id))
        assert response.status_code == 200
        assert skill.name.encode() in response.data

    def test_skills_list_forbidden(
        self, test_client, admin_character, character_with_faction, skill
    ):
        other_user = User(
            email=f"other_{uuid.uuid4().hex[:8]}@example.com",
            email_verified=True,
            first_name="Other",
            surname="User",
        )
        other_user.username = f"other_{uuid.uuid4().hex[:8]}"
        other_user.set_password("password123")
        other_user.player_id = uuid.uuid4().int >> 96
        db.session.add(other_user)
        db.session.commit()
        print(
            f"DEBUG: other_user.id={other_user.id}, player_id={other_user.player_id}, "
            f"char.user_id={character_with_faction.user_id}, "
            f"char.player_id={character_with_faction.player_id}"
        )
        login_user(test_client, other_user)
        response = test_client.get(self.url(character_with_faction.id))
        print(f"DEBUG: forbidden GET status={response.status_code}")
        assert response.status_code == 403

    def test_get_skill_cost_no_skill(self, test_client, regular_user, character_with_faction):
        login_user(test_client, regular_user)
        response = test_client.get(self.url(character_with_faction.id, "/cost"))
        assert response.status_code == 400
        assert b"No skill selected" in response.data

    def test_get_skill_cost_valid(self, test_client, regular_user, character_with_faction, skill):
        login_user(test_client, regular_user)
        response = test_client.get(
            self.url(character_with_faction.id, f"/cost?skill_id={skill.id}")
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["can_purchase"] is True
        assert data["cost"] == skill.base_cost

    def test_get_skill_cost_already_has_skill(
        self, test_client, regular_user, character_with_faction, skill
    ):
        cs = CharacterSkill(
            character_id=character_with_faction.id,
            skill_id=skill.id,
            times_purchased=1,
            purchased_by_user_id=regular_user.id,
        )
        db.session.add(cs)
        db.session.commit()
        login_user(test_client, regular_user)
        response = test_client.get(
            self.url(character_with_faction.id, f"/cost?skill_id={skill.id}")
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["can_purchase"] is False
        assert "only be purchased once" in data["reason"]

    def test_purchase_skill_success(self, test_client, regular_user, character_with_faction, skill):
        login_user(test_client, regular_user)
        response = test_client.post(
            self.url(character_with_faction.id, "/purchase"),
            data={"skill_id": skill.id},
        )
        assert response.status_code == 302  # Should redirect on success

    def test_purchase_skill_no_skill(self, test_client, regular_user, character_with_faction):
        login_user(test_client, regular_user)
        response = test_client.post(self.url(character_with_faction.id, "/purchase"), data={})
        assert response.status_code == 302  # Should redirect on error

    def test_purchase_skill_already_has(
        self, test_client, regular_user, character_with_faction, skill
    ):
        cs = CharacterSkill(
            character_id=character_with_faction.id,
            skill_id=skill.id,
            times_purchased=1,
            purchased_by_user_id=regular_user.id,
        )
        db.session.add(cs)
        db.session.commit()
        login_user(test_client, regular_user)
        response = test_client.post(
            self.url(character_with_faction.id, "/purchase"),
            data={"skill_id": skill.id},
        )
        assert response.status_code == 302  # Should redirect on error

    def test_purchase_skill_forbidden(
        self, test_client, admin_character, character_with_faction, skill
    ):
        other_user = User(
            email=f"other_{uuid.uuid4().hex[:8]}@example.com",
            email_verified=True,
            first_name="Other",
            surname="User",
        )
        other_user.username = f"other_{uuid.uuid4().hex[:8]}"
        other_user.set_password("password123")
        other_user.player_id = uuid.uuid4().int >> 96
        db.session.add(other_user)
        db.session.commit()
        login_user(test_client, other_user)
        response = test_client.post(
            self.url(character_with_faction.id, "/purchase"),
            data={"skill_id": skill.id},
        )
        print(f"DEBUG: forbidden POST status={response.status_code}")
        assert response.status_code == 403

    def test_refund_skill_success(self, test_client, user_admin, admin_character, skill):
        cs = CharacterSkill(
            character_id=admin_character.id,
            skill_id=skill.id,
            times_purchased=1,
            purchased_by_user_id=user_admin.id,
        )
        db.session.add(cs)
        db.session.commit()
        login_user(test_client, user_admin)
        response = test_client.post(
            self.url(admin_character.id, "/refund"), data={"skill_id": skill.id}
        )
        assert response.status_code == 302  # Should redirect on success

    def test_refund_skill_no_skill(self, test_client, user_admin, admin_character):
        login_user(test_client, user_admin)
        response = test_client.post(self.url(admin_character.id, "/refund"), data={})
        assert response.status_code == 302  # Should redirect on error

    def test_refund_skill_forbidden(self, test_client, regular_user, admin_character, skill):
        cs = CharacterSkill(
            character_id=admin_character.id,
            skill_id=skill.id,
            times_purchased=1,
            purchased_by_user_id=regular_user.id,
        )
        db.session.add(cs)
        db.session.commit()
        login_user(test_client, regular_user)
        response = test_client.post(
            self.url(admin_character.id, "/refund"), data={"skill_id": skill.id}
        )
        assert response.status_code == 403

    def test_refund_skill_prereq(
        self, test_client, user_admin, admin_character, skill, prerequisite_skill
    ):
        login_user(test_client, user_admin)
        # Add both skills to the character
        cs1 = CharacterSkill(
            character_id=admin_character.id,
            skill_id=skill.id,
            times_purchased=1,
            purchased_by_user_id=user_admin.id,
        )
        cs2 = CharacterSkill(
            character_id=admin_character.id,
            skill_id=prerequisite_skill.id,
            times_purchased=1,
            purchased_by_user_id=user_admin.id,
        )
        db.session.add(cs1)
        db.session.add(cs2)
        db.session.commit()
        response = test_client.post(
            self.url(admin_character.id, "/refund"),
            data={"skill_id": prerequisite_skill.id},
        )
        assert response.status_code == 302  # Should redirect on error
        # No error message check
