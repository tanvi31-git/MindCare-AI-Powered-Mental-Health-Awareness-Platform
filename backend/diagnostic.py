#!/usr/bin/env python3
"""
MindCare Diagnostic Script
This script tests all backend components and MongoDB connection
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("MindCare Backend Diagnostic")
print("=" * 60)

# Test 1: Check if modules can be imported
print("\n✓ Testing imports...")
try:
    from flask import Flask
    print("  ✓ Flask imported successfully")
except ImportError as e:
    print(f"  ✗ Flask import failed: {e}")
    sys.exit(1)

try:
    from flask_pymongo import PyMongo
    print("  ✓ Flask-PyMongo imported successfully")
except ImportError as e:
    print(f"  ✗ Flask-PyMongo import failed: {e}")
    sys.exit(1)

try:
    from config import Config
    print("  ✓ Config imported successfully")
except ImportError as e:
    print(f"  ✗ Config import failed: {e}")
    sys.exit(1)

try:
    from scoring_engine import ScoringEngine
    print("  ✓ ScoringEngine imported successfully")
except ImportError as e:
    print(f"  ✗ ScoringEngine import failed: {e}")
    sys.exit(1)

try:
    from nlp_model import NLPAnalyzer
    print("  ✓ NLPAnalyzer imported successfully")
except ImportError as e:
    print(f"  ✗ NLPAnalyzer import failed: {e}")
    sys.exit(1)

try:
    from decision_engine import DecisionEngine
    print("  ✓ DecisionEngine imported successfully")
except ImportError as e:
    print(f"  ✗ DecisionEngine import failed: {e}")
    sys.exit(1)

# Test 2: Check MongoDB connection
print("\n✓ Testing MongoDB connection...")
try:
    from pymongo import MongoClient
    
    mongo_uri = Config.MONGO_URI
    print(f"  MongoDB URI: {mongo_uri}")
    
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    # Force connection
    client.admin.command('ismaster')
    print("  ✓ MongoDB connected successfully!")
    
    # Check if database exists
    db_name = mongo_uri.split('/')[-1].split('?')[0] or 'mindcare_db'
    print(f"  Database: {db_name}")
    
    # List collections
    db = client[db_name]
    collections = db.list_collection_names()
    print(f"  Collections: {collections if collections else 'No collections yet'}")
    
    client.close()
except Exception as e:
    print(f"  ✗ MongoDB connection failed: {e}")
    print("  Make sure MongoDB is running:")
    print("    Windows: mongod")
    sys.exit(1)

# Test 3: Initialize Flask app
print("\n✓ Testing Flask app initialization...")
try:
    # Import the actual app from app.py instead of creating a blank one
    from app import app
    print("  ✓ Flask app and PyMongo initialized successfully")
except Exception as e:
    print(f"  ✗ Flask app initialization failed: {e}")
    sys.exit(1)

# Test 4: Initialize AI components
print("\n✓ Testing AI components...")
try:
    nlp = NLPAnalyzer()
    print("  ✓ NLPAnalyzer initialized successfully")
    
    scoring = ScoringEngine()
    print("  ✓ ScoringEngine initialized successfully")
    
    decision = DecisionEngine()
    print("  ✓ DecisionEngine initialized successfully")
except Exception as e:
    print(f"  ✗ AI component initialization failed: {e}")
    sys.exit(1)

# Test 5: Test API endpoints
print("\n✓ Testing API endpoints...")
try:
    with app.app_context():
        # Test health endpoint
        with app.test_client() as client:
            response = client.get('/api/health')
            if response.status_code == 200:
                print("  ✓ GET /api/health: OK")
            else:
                print(f"  ✗ GET /api/health: {response.status_code}")
            
            # Test questions endpoint
            response = client.get('/api/questions')
            if response.status_code == 200:
                print("  ✓ GET /api/questions: OK")
            else:
                print(f"  ✗ GET /api/questions: {response.status_code}")
except Exception as e:
    print(f"  ✗ API endpoint test failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All diagnostics passed!")
print("=" * 60)
print("\nYour backend is ready to run!")
print("\nNext steps:")
print("  1. Start the backend: python app.py")
print("  2. Start the frontend: python -m http.server 8000")
print("  3. Open browser: http://localhost:8000/frontend/landing_page.html")
print("\n" + "=" * 60)
