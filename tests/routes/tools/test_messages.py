import os
import sys
from unittest.mock import patch

from models.tools.message import Message

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))


class TestMessagesRoutes:
    """Test cases for messages routes"""

    def test_messages_page_npc(self, test_client, npc_user, sample_character, db):
        """Test messages page for NPC users"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(npc_user.id)
            sess["_fresh"] = True

        # Create a message without response
        message = Message(
            sender_id=sample_character.id,
            recipient_name="Test Recipient",
            content="Test message content",
        )
        db.session.add(message)
        db.session.commit()

        response = test_client.get("/messages/messages", follow_redirects=True)
        assert response.status_code == 200
        assert b"Test message content" in response.data

    def test_messages_page_regular_user(self, test_client, sample_user, sample_character, db):
        """Test messages page for regular users"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(sample_user.id)
            sess["_fresh"] = True

        # Create a message for the user's character
        message = Message(
            sender_id=sample_character.id,
            recipient_name="Test Recipient",
            content="Test message content",
        )
        db.session.add(message)
        db.session.commit()

        response = test_client.get("/messages/messages", follow_redirects=True)
        assert response.status_code == 200
        assert b"Test message content" in response.data

    def test_messages_page_no_active_character(self, test_client, regular_user):
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(regular_user.id)
            sess["_fresh"] = True
        response = test_client.get("/messages/messages")
        assert response.status_code == 302  # Redirect to index
        assert "/index" in response.location or response.location.endswith("/")

    def test_send_message_npc(self, test_client, npc_user, sample_character, db):
        """Test sending message as NPC"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(npc_user.id)
            sess["_fresh"] = True
        # Give character some funds
        sample_character.ec = 20
        db.session.commit()
        response = test_client.post(
            "/messages/messages/send",
            data={
                "sender_id": sample_character.id,
                "recipient_name": "Test Recipient",
                "content": "Test message content",
                "paid_in_cash": "true",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Message sent successfully" in response.data
        # Check message was created
        message = Message.query.filter_by(sender_id=sample_character.id).first()
        assert message is not None
        assert message.recipient_name == "Test Recipient"
        assert message.content == "Test message content"

    def test_send_message_regular_user(self, test_client, sample_user, sample_character, db):
        """Test sending message as regular user"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(sample_user.id)
            sess["_fresh"] = True
        # Give character some funds
        sample_character.bank_account = 20
        db.session.commit()
        db.session.refresh(sample_user)
        db.session.refresh(sample_character)
        response = test_client.post(
            "/messages/messages/send",
            data={
                "recipient_name": "Test Recipient",
                "content": "Test message content",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Message sent successfully" in response.data
        # Check message was created and funds deducted
        message = Message.query.filter_by(sender_id=sample_character.id).first()
        assert message is not None
        assert message.recipient_name == "Test Recipient"
        assert message.content == "Test message content"
        db.session.refresh(sample_character)
        assert sample_character.bank_account == 10  # 20 - 10

    def test_send_message_insufficient_funds(self, test_client, sample_user, sample_character, db):
        """Test sending message with insufficient funds"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(sample_user.id)
            sess["_fresh"] = True
        # Character has no funds
        sample_character.bank_account = 0
        db.session.commit()
        response = test_client.post(
            "/messages/messages/send",
            data={
                "recipient_name": "Test Recipient",
                "content": "Test message content",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Insufficient funds" in response.data

    def test_send_message_with_group_funds(
        self, test_client, sample_user, sample_character, group, db
    ):
        """Test sending message using group funds when character has insufficient funds"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(sample_user.id)
            sess["_fresh"] = True

        # Add character to group and set balances
        sample_character.group = group
        sample_character.bank_account = 5  # Not enough for 10 ec message
        group.bank_account = 20
        db.session.commit()
        db.session.refresh(sample_character)
        db.session.refresh(group)

        response = test_client.post(
            "/messages/messages/send",
            data={
                "recipient_name": "Test Recipient",
                "content": "Test message content",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Message sent successfully" in response.data

        # Check message was created
        message = Message.query.filter_by(sender_id=sample_character.id).first()
        assert message is not None
        assert message.recipient_name == "Test Recipient"
        assert message.content == "Test message content"

        # Check funds were deducted correctly (5 from character, 5 from group)
        db.session.refresh(sample_character)
        db.session.refresh(group)
        assert sample_character.bank_account == 0  # 5 - 5
        assert group.bank_account == 15  # 20 - 5

    def test_send_message_group_funds_only(
        self, test_client, sample_user, sample_character, group, db
    ):
        """Test sending message using only group funds when character has zero balance"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(sample_user.id)
            sess["_fresh"] = True

        # Add character to group and set balances
        sample_character.group = group
        sample_character.bank_account = 0  # No character funds
        group.bank_account = 20
        db.session.commit()
        db.session.refresh(sample_character)
        db.session.refresh(group)

        response = test_client.post(
            "/messages/messages/send",
            data={
                "recipient_name": "Test Recipient",
                "content": "Test message content",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Message sent successfully" in response.data

        # Check message was created
        message = Message.query.filter_by(sender_id=sample_character.id).first()
        assert message is not None

        # Check funds were deducted from group only
        db.session.refresh(sample_character)
        db.session.refresh(group)
        assert sample_character.bank_account == 0  # Still 0
        assert group.bank_account == 10  # 20 - 10

    def test_send_message_missing_fields(self, test_client, npc_user, sample_character):
        """Test sending message with missing fields"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(npc_user.id)
            sess["_fresh"] = True
        response = test_client.post(
            "/messages/messages/send",
            data={
                "sender_id": sample_character.id,
                "content": "Test message content",
                # Missing recipient_name
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"All fields are required" in response.data

    def test_send_message_invalid_sender(self, test_client, npc_user):
        """Test sending message with invalid sender ID"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(npc_user.id)
            sess["_fresh"] = True
        response = test_client.post(
            "/messages/messages/send",
            data={
                "sender_id": 99999,  # Non-existent character
                "recipient_name": "Test Recipient",
                "content": "Test message content",
                "paid_in_cash": "true",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Invalid sender" in response.data

    def test_respond_to_message(self, test_client, npc_user, sample_character, db):
        """Test responding to a message"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(npc_user.id)
            sess["_fresh"] = True
        # Create a message
        message = Message(
            sender_id=sample_character.id,
            recipient_name="Test Recipient",
            content="Test question",
        )
        db.session.add(message)
        db.session.commit()
        response = test_client.post(
            f"/messages/messages/{message.id}/respond",
            data={"response": "Test response"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Response sent successfully" in response.data
        db.session.refresh(message)
        assert message.response == "Test response"
        db.session.refresh(sample_character)
        assert "messages" in sample_character.character_pack
        assert len(sample_character.character_pack["messages"]) == 1
        assert sample_character.character_pack["messages"][0]["type"] == "sms_response"

    def test_respond_to_message_empty_response(self, test_client, npc_user, sample_character, db):
        """Test responding to message with empty response"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(npc_user.id)
            sess["_fresh"] = True
        # Create a message
        message = Message(
            sender_id=sample_character.id,
            recipient_name="Test Recipient",
            content="Test question",
        )
        db.session.add(message)
        db.session.commit()
        response = test_client.post(
            f"/messages/messages/{message.id}/respond",
            data={"response": ""},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Response cannot be empty" in response.data

    def test_respond_to_message_not_found(self, test_client, npc_user):
        """Test responding to non-existent message"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(npc_user.id)
            sess["_fresh"] = True

        response = test_client.post(
            "/messages/messages/99999/respond",
            data={"response": "Test response"},
            follow_redirects=True,
        )

        assert response.status_code == 404

    def test_respond_to_message_unauthorized(self, test_client, sample_user, sample_character, db):
        """Test responding to message as non-NPC user"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(sample_user.id)
            sess["_fresh"] = True

        # Create a message
        message = Message(
            sender_id=sample_character.id,
            recipient_name="Test Recipient",
            content="Test question",
        )
        db.session.add(message)
        db.session.commit()

        response = test_client.post(
            f"/messages/messages/{message.id}/respond",
            data={"response": "Test response"},
            follow_redirects=True,
        )

        # Should be forbidden for non-NPC users
        assert response.status_code in [403, 302]  # 403 Forbidden or redirect

    def test_message_response_sends_notification(self, test_client, npc_user, sample_character, db):
        """Test that responding to a message sends a notification email to the user."""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(npc_user.id)
            sess["_fresh"] = True
        # Create a message
        message = Message(
            sender_id=sample_character.id,
            recipient_name="Test Recipient",
            content="Test question",
        )
        db.session.add(message)
        db.session.commit()
        # Patch send_notification_email and render_email_template
        with (
            patch("utils.email.send_email") as mock_send,
            patch("utils.email.render_email_template") as mock_render,
        ):
            mock_render.return_value = ("text", "<p>html</p>")
            response = test_client.post(
                f"/messages/messages/{message.id}/respond",
                data={"response": "Test response"},
                follow_redirects=True,
            )
            assert response.status_code == 200
            # Should have called send_email with correct subject
            mock_send.assert_any_call(
                "Orion Sphere LRP - Message Response Received",
                [sample_character.user.email],
                "text",
                "<p>html</p>",
            )
