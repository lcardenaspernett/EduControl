from . import db
from datetime import datetime

class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))
    data_type = db.Column(db.String(20), default='string')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def typed_value(self):
        if self.data_type == 'int':
            return int(self.value or 0)
        elif self.data_type == 'float':
            return float(self.value or 0.0)
        elif self.data_type == 'bool':
            return self.value.lower() in ['true', '1', 'yes'] if self.value else False
        return self.value

    def __repr__(self):
        return f'<Config {self.key}: {self.value}>'
