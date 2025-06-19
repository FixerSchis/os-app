from models.extensions import db

class Medicament(db.Model):
    __tablename__ = 'medicaments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    wiki_slug = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<Medicament {self.name}>' 