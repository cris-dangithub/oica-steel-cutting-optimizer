"""
OICA Database Models
SQLAlchemy ORM models for PostgreSQL
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models for easy access
from .uploaded_file import UploadedFile, ProcessingResult

__all__ = ['db', 'UploadedFile', 'ProcessingResult']
