"""
Shared Firebase Admin SDK initialization.
All Python modules should import `db` from this module.

Usage:
    from firebase_config import db
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore

# Path to the service account key JSON file
_CRED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(_CRED_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()
