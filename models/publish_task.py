from . import db
from datetime import datetime

class PublishTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_title = db.Column(db.String(500), nullable=False)
    original_content = db.Column(db.Text, nullable=False)
    selected_platforms = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)
    
    user = db.relationship('User', backref=db.backref('publish_tasks', lazy=True))
    adaptations = db.relationship('PlatformAdaptation', backref='publish_task', lazy=True)
    
    def __repr__(self):
        return f'<PublishTask {self.id}>'