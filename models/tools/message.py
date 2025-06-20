from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models.extensions import db

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('character.id'), nullable=False)
    recipient_name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime)
    
    # Relationships
    sender = relationship('Character', backref='sent_messages')
    
    def __init__(self, sender_id, recipient_name, content):
        self.sender_id = sender_id
        self.recipient_name = recipient_name
        self.content = content
    
    def add_response(self, response_text):
        self.response = response_text
        self.responded_at = datetime.utcnow() 