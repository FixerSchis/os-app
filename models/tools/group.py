from datetime import datetime
from models.extensions import db
from models.enums import GroupType

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum(GroupType, native_enum=False, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    bank_account = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now())

    # Relationships
    characters = db.relationship('Character', back_populates='group', lazy=True)
    invites = db.relationship('GroupInvite', back_populates='group', cascade='all, delete-orphan')
    samples = db.relationship('Sample', back_populates='group', lazy='dynamic')

    def __repr__(self):
        return f'<Group {self.name}>'

    @property
    def type_enum(self):
        return GroupType(self.type)

    @type_enum.setter
    def type_enum(self, type):
        if isinstance(type, GroupType):
            self.type = type.value
        else:
            self.type = type

class GroupInvite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now())

    # Relationships
    group = db.relationship('Group', back_populates='invites')
    character = db.relationship('Character')

    __table_args__ = (
        db.UniqueConstraint('group_id', 'character_id', name='uix_group_character_invite'),
    )

    def __repr__(self):
        return f'<GroupInvite {self.group.name} -> {self.character.name}>' 