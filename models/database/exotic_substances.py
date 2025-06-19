from models.extensions import db
from models.enums import ScienceType

class ExoticSubstance(db.Model):
    __tablename__ = 'exotic_substances'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum(
        ScienceType,
        native_enum=False,
        values_callable=lambda obj: [e.value for e in obj]
    ), nullable=False)
    wiki_slug = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<ExoticSubstance {self.name}>' 