from models.extensions import db
from datetime import datetime
from models.enums import ScienceType
from models.tools.group import Group

# Association table for many-to-many relationship between Sample and SampleTag
sample_sample_tags = db.Table('sample_sample_tags',
    db.Column('sample_id', db.Integer, db.ForeignKey('sample.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('sample_tag.id'), primary_key=True)
)

class SampleTag(db.Model):
    __tablename__ = 'sample_tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<SampleTag {self.name}>'

class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum(
        ScienceType,
        native_enum=False,
        values_callable=lambda obj: [e.value for e in obj]
    ), nullable=False)
    is_researched = db.Column(db.Boolean, nullable=False, default=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now())
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    group = db.relationship('Group', back_populates='samples')

    # Relationship to sample tags through the association table
    tags = db.relationship('SampleTag', secondary=sample_sample_tags, backref=db.backref('samples', lazy='dynamic'))

    def __repr__(self):
        return f'<Sample {self.name}>' 