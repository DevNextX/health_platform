from src.app import create_app
from src.extensions import db, migrate
from flask_migrate import migrate as migrate_cmd, upgrade as upgrade_cmd
import sys

app = create_app()
with app.app_context():
    print("Running initial upgrade...")
    try:
        upgrade_cmd()
        print("Initial upgrade done.")
        print("Running migrate...")
        migrate_cmd(message="add threshold config models")
        print("Migrate done.")
        print("Running upgrade...")
        upgrade_cmd()
        print("Upgrade done.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
