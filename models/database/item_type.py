from models.extensions import db
from sqlalchemy.orm import validates
import re

class ItemType(db.Model):
    __tablename__ = 'item_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    id_prefix = db.Column(db.String(2), nullable=False, unique=False)
    
    @validates('id_prefix')
    def validate_id_prefix(self, key, id_prefix):
        if not id_prefix:
            raise ValueError("ID prefix is required")
        if not re.match(r'^[A-Z0-9]{2}$', id_prefix):
            raise ValueError("ID prefix must be exactly 2 characters (letters or numbers)")
        return id_prefix.upper()
    
    def __repr__(self):
        return f'<ItemType {self.name} ({self.id_prefix})>' 