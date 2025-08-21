"""
Data Access Layer - שכבת גישה לנתונים
"""

from .mongo_client import mongo_client
from .query_builder import MongoQueryBuilder

__all__ = [
    "mongo_client",
    "MongoQueryBuilder"
]