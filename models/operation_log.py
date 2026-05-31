from . import db
from datetime import datetime


class OperationLog(db.Model):
    """操作日志表 - 记录适配、发布、重试等操作"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    task_id = db.Column(db.Integer, nullable=True)
    platform_type = db.Column(db.String(50), nullable=True)
    operation = db.Column(db.String(50), nullable=False)  # adapt/publish/retry/error
    status = db.Column(db.String(20), default='info')  # info/success/warning/error
    message = db.Column(db.Text, nullable=True)
    detail = db.Column(db.Text, nullable=True)  # JSON格式详情
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<OperationLog {self.operation} {self.status}>'