from models.extensions import db
from datetime import datetime

class ConditionStage(db.Model):
    __tablename__ = 'condition_stages'
    
    id = db.Column(db.Integer, primary_key=True)
    condition_id = db.Column(db.Integer, db.ForeignKey('conditions.id'), nullable=False)
    stage_number = db.Column(db.Integer, nullable=False)
    rp_effect = db.Column(db.String(500), nullable=False)
    diagnosis = db.Column(db.String(500), nullable=False)
    cure = db.Column(db.String(500), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Number of events
    
    # Relationship
    condition = db.relationship('Condition', back_populates='stages')
    
    __table_args__ = (
        db.UniqueConstraint('condition_id', 'stage_number', name='uix_condition_stage_number'),
    )
    
    def __repr__(self):
        return f'<ConditionStage {self.stage_number} of {self.condition.name}>'

class Condition(db.Model):
    __tablename__ = 'conditions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    stages = db.relationship('ConditionStage', back_populates='condition', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Condition {self.name}>' 