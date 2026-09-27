"""Utility script to create DB tables using SQLAlchemy metadata.

Usage: python scripts/manage_db.py
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.app.core.database import engine, Base


def main():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done")


if __name__ == "__main__":
    main()
