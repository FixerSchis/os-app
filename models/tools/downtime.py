from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from models.extensions import db
from models.enums import  DowntimeStatus, DowntimeTaskStatus

class DowntimePeriod(db.Model):
    __tablename__ = 'downtime_periods'
    
    id = Column(Integer, primary_key=True)
    status = db.Column(db.Enum(DowntimeStatus, native_enum=False, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    event_id = Column(Integer, ForeignKey('events.id'))
    
    packs = relationship('DowntimePack', back_populates='period', cascade='all, delete-orphan')
    event = relationship('Event', backref='downtime_periods')
    
    def to_dict(self):
        return {
            'id': self.id,
            'status': self.status.value,
            'event_id': self.event_id,
        }

class DowntimePack(db.Model):
    __tablename__ = 'downtime_packs'
    
    id = Column(Integer, primary_key=True)
    period_id = Column(Integer, ForeignKey('downtime_periods.id'), nullable=False)
    character_id = Column(Integer, ForeignKey('character.id'), nullable=False)
    status = db.Column(db.Enum(DowntimeTaskStatus, native_enum=False, values_callable=lambda obj: [e.value for e in obj]), nullable=False)

    # Pack contents
    energy_credits = Column(Integer, default=0)
    items = Column(JSON, default=list)
    exotic_substances = Column(JSON, default=list)
    conditions = Column(JSON, default=list)
    samples = Column(JSON, default=list)
    cybernetics = Column(JSON, default=list)
    research_teams = Column(JSON, default=list)  # List of faction IDs

    purchases = Column(JSON, default=list)
    modifications = Column(JSON, default=list)
    engineering = Column(JSON, default=list)
    science = Column(JSON, default=list)
    research = Column(JSON, default=list)
    reputation = Column(JSON, default=list)

    review_data = Column(JSON, default=dict)
    
    period = relationship('DowntimePeriod', back_populates='packs')
    character = relationship('Character', back_populates='downtime_packs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'period_id': self.period_id,
            'character_id': self.character_id,
            'status': self.status.value,
            'energy_credits': self.energy_credits,
            'items': self.items,
            'exotic_substances': self.exotic_substances,
            'conditions': self.conditions,
            'samples': self.samples,
            'cybernetics': self.cybernetics,
            'research_teams': self.research_teams,
            'purchases': self.purchases,
            'modifications': self.modifications,
            'engineering': self.engineering,
            'science': self.science,
            'research': self.research,
            'reputation': self.reputation,
            'review_data': self.review_data,
        }
