import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db

if __name__ == "__main__":
    print("Initializing SQLite database...")
    init_db()
    print("Done!")