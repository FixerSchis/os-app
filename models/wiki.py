from models.extensions import db
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Enum as SqlEnum
from .enums import SectionRestrictionType, WikiPageVersionStatus
from sqlalchemy.orm import relationship

class WikiPage(db.Model):
    slug = db.Column(db.String(200), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    versions = db.relationship('WikiPageVersion', backref='page', lazy='dynamic', cascade='all, delete-orphan', order_by='WikiPageVersion.version_number')
    tags = relationship('WikiTag', secondary='wiki_page_tags', back_populates='pages')

class WikiPageVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_slug = db.Column(db.String(200), db.ForeignKey('wiki_page.slug', ondelete='CASCADE'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    status = db.Column(SqlEnum(WikiPageVersionStatus), nullable=False, default=WikiPageVersionStatus.PUBLISHED)
    deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    sections = db.relationship('WikiSection', backref='version', lazy='dynamic', cascade='all, delete-orphan', order_by='WikiSection.order')
    diff = db.Column(db.Text, nullable=True)

class WikiSection(db.Model):
    __tablename__ = 'wiki_section'
    version_id = db.Column(db.Integer, db.ForeignKey('wiki_page_version.id', ondelete='CASCADE'), primary_key=True)
    id = db.Column(db.Integer, primary_key=True)  # Unique only within version_id
    order = db.Column(db.Integer, nullable=False, default=0)
    title = db.Column(db.String(200), nullable=True)  # Section title
    content = db.Column(db.Text, nullable=False)
    restriction_type = db.Column(SqlEnum(SectionRestrictionType), nullable=True)
    restriction_value = db.Column(db.String(100), nullable=True)

    @property
    def restriction_value_list(self):
        import json
        if self.restriction_value:
            try:
                return json.loads(self.restriction_value)
            except Exception:
                # fallback for legacy single-value storage
                return [self.restriction_value]
        return []

    @restriction_value_list.setter
    def restriction_value_list(self, value):
        import json
        self.restriction_value = json.dumps(value)

class WikiImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    mimetype = db.Column(db.String(50), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

# Association table for many-to-many between WikiChangeLog and WikiPageVersion
wiki_changelog_versions = db.Table(
    'wiki_changelog_versions',
    db.Column('changelog_id', db.Integer, db.ForeignKey('wiki_change_log.id'), primary_key=True),
    db.Column('version_id', db.Integer, db.ForeignKey('wiki_page_version.id'), primary_key=True)
)

class WikiChangeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='wiki_change_logs')
    message = db.Column(db.Text, nullable=False)
    versions = db.relationship('WikiPageVersion', secondary=wiki_changelog_versions, backref='change_logs')

# Association table for many-to-many WikiPage <-> WikiTag
wiki_page_tags = db.Table(
    'wiki_page_tags',
    db.Column('page_slug', db.String(200), db.ForeignKey('wiki_page.slug', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('wiki_tag.id', ondelete='CASCADE'), primary_key=True)
)

class WikiTag(db.Model):
    __tablename__ = 'wiki_tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    pages = relationship('WikiPage', secondary='wiki_page_tags', back_populates='tags')

def get_or_create_wiki_page(slug, default_title, created_by=None):
    page = WikiPage.query.filter_by(slug=slug).first()
    if page:
        return page
    # Create the page
    page = WikiPage(slug=slug, title=default_title)
    db.session.add(page)
    db.session.flush()
    version = WikiPageVersion(
        page_slug=slug,
        version_number=1,
        status=WikiPageVersionStatus.PUBLISHED,
        created_by=created_by,
    )
    db.session.add(version)
    db.session.flush()
    # Optionally, add a blank section
    section = WikiSection(
        version_id=version.id,
        id=1,
        order=0,
        title=default_title,
        content=""
    )
    db.session.add(section)
    db.session.flush()
    return page 