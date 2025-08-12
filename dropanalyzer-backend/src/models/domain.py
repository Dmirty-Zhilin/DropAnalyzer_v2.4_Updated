from datetime import datetime
from src.extensions import db
from sqlalchemy.dialects.postgresql import JSONB


class Domain(db.Model):
    __tablename__ = 'domains'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    long_live = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Domain {self.name}>"

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domains.id', ondelete='CASCADE'), nullable=False, index=True)
    metrics = db.Column(JSONB, nullable=True)
    quality_score = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    domain = db.relationship('Domain', backref=db.backref('reports', lazy='dynamic'))
