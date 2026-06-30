import enum
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


class PlanEnum(str, enum.Enum):
    free = 'free'
    premium = 'premium'
    admin = 'admin'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    plan = db.Column(db.String(20), nullable=False, default=PlanEnum.free.value)

    def __init__(self, **kwargs):
        if 'plan' not in kwargs:
            kwargs['plan'] = PlanEnum.free.value
        super().__init__(**kwargs)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    projects = db.relationship(
        'Project',
        backref='owner',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    def set_password(self, password: str) -> None:
        """Hash and store the password using werkzeug."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def is_premium(self) -> bool:
        """Return True if the user has a premium or admin plan."""
        return self.plan in (PlanEnum.premium.value, PlanEnum.admin.value)

    def is_admin(self) -> bool:
        """Return True if the user has an admin plan."""
        return self.plan == PlanEnum.admin.value

    def __repr__(self) -> str:
        return f'<User {self.username} ({self.plan})>'


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    current_phase = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    discovery_data = db.Column(db.Text, nullable=True)   # JSON
    definition_data = db.Column(db.Text, nullable=True)  # JSON
    development_data = db.Column(db.Text, nullable=True) # JSON
    delivery_data = db.Column(db.Text, nullable=True)    # JSON

    completed = db.Column(db.Boolean, nullable=False, default=False)

    def get_discovery_data(self):
        """Return discovery_data parsed from JSON, or empty dict."""
        return self._parse_json_field(self.discovery_data)

    def set_discovery_data(self, data: dict) -> None:
        from flask import json as fjson
        self.discovery_data = fjson.dumps(data, ensure_ascii=False)

    def get_definition_data(self):
        return self._parse_json_field(self.definition_data)

    def set_definition_data(self, data: dict) -> None:
        from flask import json as fjson
        self.definition_data = fjson.dumps(data, ensure_ascii=False)

    def get_development_data(self):
        return self._parse_json_field(self.development_data)

    def set_development_data(self, data: dict) -> None:
        from flask import json as fjson
        self.development_data = fjson.dumps(data, ensure_ascii=False)

    def get_delivery_data(self):
        return self._parse_json_field(self.delivery_data)

    def set_delivery_data(self, data: dict) -> None:
        from flask import json as fjson
        self.delivery_data = fjson.dumps(data, ensure_ascii=False)

    @staticmethod
    def _parse_json_field(field):
        import json
        if not field:
            return {}
        try:
            return json.loads(field)
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def phase_name(self):
        phases = {
            0: 'Início',
            1: 'Descobrir',
            2: 'Definir',
            3: 'Desenvolver',
            4: 'Entregar',
        }
        return phases.get(self.current_phase, 'Desconhecida')

    def advance_phase(self) -> None:
        """Move to the next phase (max 4). If finishing phase 4, mark completed."""
        if self.current_phase < 4:
            self.current_phase += 1
        if self.current_phase == 4:
            self.completed = True

    def __repr__(self) -> str:
        return f'<Project {self.id} {self.name!r} phase={self.current_phase}>'
