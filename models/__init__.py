from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .material import Material
from .publish_task import PublishTask
from .platform_adaptation import PlatformAdaptation
from .operation_log import OperationLog