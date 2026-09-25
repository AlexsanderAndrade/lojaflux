from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from .commands import register_commands
from .extensions import db
from .routes import bp


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    database_path = Path(app.instance_path) / "lojaflux.db"

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("LOJAFLUX_SECRET_KEY", "dev-local-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "LOJAFLUX_DATABASE_URL", f"sqlite:///{database_path.as_posix()}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    app.register_blueprint(bp)
    register_commands(app)

    with app.app_context():
        db.create_all()

    return app

