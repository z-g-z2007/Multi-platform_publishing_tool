from . import db
from datetime import datetime

class PlatformAdaptation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('publish_task.id'), nullable=False)
    platform_type = db.Column(db.String(50), nullable=False)
    adapted_title = db.Column(db.String(500), nullable=True)
    adapted_content = db.Column(db.Text, nullable=True)
    original_title = db.Column(db.String(500), nullable=True)
    original_content = db.Column(db.Text, nullable=True)
    publish_status = db.Column(db.String(20), default='pending')
    retry_count = db.Column(db.Integer, default=0)
    max_retry = db.Column(db.Integer, default=3)
    error_message = db.Column(db.Text, nullable=True)
    published_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<PlatformAdaptation {self.platform_type}>'
    
    def can_retry(self):
        return self.retry_count < self.max_retry