## App Factory

```python
# app/__init__.py
from flask import Flask
from app.extensions import db, migrate, jwt
from app.config import Config
from app.errors import register_error_handlers
from app.blueprints.users import users_bp
from app.blueprints.auth import auth_bp

def create_app(config_class: type = Config) -> Flask:
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register blueprints
    app.register_blueprint(users_bp, url_prefix="/api/v1/users")
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")

    register_error_handlers(app)
    return app
```

---

## Extensions (Singleton Pattern)

```python
# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
```

---

## Blueprint + Route

```python
# app/blueprints/users/routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.user_service import UserService
from app.schemas.user import UserCreateSchema, UserResponseSchema

users_bp = Blueprint("users", __name__)
create_schema = UserCreateSchema()
response_schema = UserResponseSchema()

@users_bp.route("/", methods=["POST"])
def create_user():
    """Create a new user account."""
    data = create_schema.load(request.json)  # validates + deserialises
    user = UserService.create_user(**data)
    return response_schema.dump(user), 201

@users_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id: int):
    """Get a user by ID."""
    user = UserService.get_user(user_id)
    return response_schema.dump(user), 200
```

---

## Application Context & `g`

The `g` object stores **request-scoped** data (resources created and torn down per request).
It is **not** a cross-request cache — data on `g` dies when the request ends.

```python
# app/database.py
from flask import g
from app.extensions import db

def get_db_connection():
    """Return the same DB connection for the entire request, create if missing."""
    if "db_conn" not in g:
        g.db_conn = db.engine.connect()
    return g.db_conn

# Register teardown — always closes the connection even if view raised an exception
def teardown_db(exception: BaseException | None) -> None:
    """Close DB connection when app context pops (end of request or CLI command)."""
    conn = g.pop("db_conn", None)
    if conn is not None:
        conn.close()

# Register in factory:
# app.teardown_appcontext(teardown_db)
```

**Pattern — get_X / teardown_X:**
```python
# Any resource that should be created once per request follows this pattern:
# 1. get_X() — creates and caches on g if not already there
# 2. teardown_X() — closes/releases; registered with @app.teardown_appcontext

from werkzeug.local import LocalProxy
db_conn = LocalProxy(get_db_connection)  # access db_conn like a normal object
```

**Rules:**
- Use `g` for request-scoped resources (DB connections, current user cache, feature flags).
- Use `session` for data that must persist across requests (user login state).
- Use `current_app.extensions["my_ext"]` for app-level shared state.
- `g` is reset fresh for every request and every CLI command invocation.

---
