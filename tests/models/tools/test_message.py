import pytest
from models.tools.message import Message
from models.tools.character import Character
from datetime import datetime

def test_new_message_with_response(db, character):
    """Test creation of a new Message and adding a response."""
    recipient_name = "NPC Test"
    content = "Hello, this is a test message."
    
    message = Message(
        sender_id=character.id,
        recipient_name=recipient_name,
        content=content
    )
    
    db.session.add(message)
    db.session.commit()
    
    # Retrieve and assert
    retrieved_message = Message.query.filter_by(sender_id=character.id).first()
    
    assert retrieved_message is not None
    assert retrieved_message.sender_id == character.id
    assert retrieved_message.recipient_name == recipient_name
    assert retrieved_message.content == content
    assert retrieved_message.response is None
    assert retrieved_message.responded_at is None
    assert retrieved_message.id is not None
    
    # Test the add_response method
    response_text = "This is a test response."
    retrieved_message.add_response(response_text)
    db.session.commit()
    
    # Check that response was added
    assert retrieved_message.response == response_text
    assert retrieved_message.responded_at is not None
    assert isinstance(retrieved_message.responded_at, datetime) 
