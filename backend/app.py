"""
MindCare Backend System
Main Flask application with API endpoints

This file serves as the entry point for the MindCare mental health assessment system.
It orchestrates the entire assessment pipeline by coordinating between different modules.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_pymongo import PyMongo
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid
import os
from bson.objectid import ObjectId
import json
import logging
import bcrypt

# Import custom modules
from config import Config
from nlp_model import NLPAnalyzer
from decision_engine import DecisionEngine
from wellness_engine import WellnessEngine
from result_formatter import ResultFormatter

# Logger setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)


# Initialize MongoDB (Flask-PyMongo for legacy, PyMongo for direct access)
mongo = PyMongo(app)
MONGO_URI = app.config.get("MONGO_URI") or os.environ.get("MONGO_URI") or "mongodb://localhost:27017/mindcare"
client = MongoClient(MONGO_URI)
db = client["mindcare"]
assessments_col = db["assessments"]



# Enable CORS for frontend integration
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE"], "allow_headers": ["Content-Type"]}})

# Configure frontend path
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), '..', 'frontend')

# Initialize service components with Hugging Face integration
nlp_analyzer = NLPAnalyzer(
    hf_token=app.config.get('HUGGINGFACE_TOKEN'),
    hf_model=app.config.get('HUGGINGFACE_MODEL'),
    use_huggingface=bool(app.config.get('HUGGINGFACE_TOKEN'))
)
decision_engine = DecisionEngine()
wellness_engine = WellnessEngine(db_client=client)

# Open-ended questions for NLP analysis
OPEN_ENDED_QUESTIONS = [
    "Describe how you've been feeling emotionally in the past week.",
    "What situations or thoughts have been causing you stress recently?",
    "How has your energy and motivation been affecting your daily activities?"
]

# Frontend Routes
@app.route('/')
def serve_landing_page():
    """Serve the landing page"""
    return send_from_directory(FRONTEND_PATH, 'landing_page.html')

@app.route('/assessment')
def serve_assessment():
    """Serve the assessment page"""
    return send_from_directory(FRONTEND_PATH, 'assessment.html')

@app.route('/results')
def serve_results():
    """Serve the results page"""
    return send_from_directory(FRONTEND_PATH, 'results.html')

@app.route('/results-wellness')
def serve_results_wellness():
    """Serve the wellness results page"""
    return send_from_directory(FRONTEND_PATH, 'results-wellness.html')

@app.route('/crisis')
def serve_crisis():
    """Serve the crisis page"""
    return send_from_directory(FRONTEND_PATH, 'crisis.html')

@app.route('/profile')
def serve_profile():
    """Serve the profile page"""
    return send_from_directory(FRONTEND_PATH, 'profile.html')

@app.route('/auth')
def serve_auth():
    """Serve the auth page"""
    return send_from_directory(FRONTEND_PATH, 'index.html')

@app.route('/registration')
def serve_registration():
    """Serve the registration page"""
    return send_from_directory(FRONTEND_PATH, 'registration.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, assets)"""
    return send_from_directory(FRONTEND_PATH, filename)

# API Routes
@app.route('/api/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        if not data or not all(key in data for key in ['name', 'email', 'password']):
            return jsonify({"error": "Missing fields"}), 400
        
        # Check if user already exists
        if mongo.db.users.find_one({"email": data['email']}):
            return jsonify({"error": "User already exists"}), 400
        
        # Hash password using bcrypt
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        user_record = {
            "name": data['name'],
            "email": data['email'],
            "password": hashed_password,  # Now storing hashed password
            "created_at": datetime.now(),
            "assessments_taken": 0
        }
        result = mongo.db.users.insert_one(user_record)
        
        return jsonify({
            "success": True,
            "user": {
                "id": str(result.inserted_id),
                "name": data['name'],
                "email": data['email'],
                "avatar": f"https://ui-avatars.com/api/?name={data['name'].replace(' ', '+')}&background=8B5CF6&color=fff"
            }
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/login', methods=['POST'])
def login_user():
    """
    Login a user.
    
    Expected JSON payload:
    {
        "email": "user@gmail.com",
        "password": "password123"
    }
    
    Returns:
        JSON: Login response with user info
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not all(key in data for key in ['email', 'password']):
            return jsonify({"error": "Missing required fields: email, password"}), 400
        
        # Find user
        user = mongo.db.users.find_one({"email": data['email']})
        
        # Check if user exists and password is correct
        if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
            return jsonify({"error": "Invalid email or password"}), 401
        
        return jsonify({
            "success": True,
            "user": {
                "id": str(user['_id']),
                "name": user['name'],
                "email": user['email'],
                "avatar": f"https://ui-avatars.com/api/?name={user['name'].replace(' ', '+')}&background=8B5CF6&color=fff"
            },
            "message": "Login successful"
        }), 200
    
    except Exception as e:
        error_msg = str(e)
        app.logger.error(f"Error logging in user: {error_msg}")
        print(f"Login Error: {error_msg}")  # Print to console
        return jsonify({"error": f"Login failed: {error_msg}"}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify API status.
    
    Returns:
        JSON: API status and timestamp
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }), 200


@app.route('/api/questions', methods=['GET'])
def get_questions():
    """
    Retrieve the open-ended questions for the assessment.
    
    Returns:
        JSON: List of open-ended questions
    """
    return jsonify({
        "questions": OPEN_ENDED_QUESTIONS,
        "count": len(OPEN_ENDED_QUESTIONS)
    }), 200


@app.route('/api/user/<user_id>', methods=['GET'])
def get_user_profile(user_id):
    """
    Retrieve user profile information with assessment statistics.
    
    Args:
        user_id: MongoDB user ID
    
    Returns:
        JSON: User profile with assessments summary
    """
    try:
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        # Get user's assessment statistics
        assessment_count = mongo.db.assessments.count_documents({"user_id": user_id})
        
        # Get latest assessment
        latest_assessment = mongo.db.assessments.find_one(
            {"user_id": user_id},
            sort=[("timestamp", -1)]
        )
        
        # Prepare user profile response
        user_profile = {
            "user_id": str(user['_id']),
            "name": user.get('name'),
            "email": user.get('email'),
            "created_at": user.get('created_at').isoformat() if user.get('created_at') else None,
            "assessments_taken": user.get('assessments_taken', 0),
            "last_assessment": user.get('last_assessment', None).isoformat() if user.get('last_assessment') else None,
            "last_assessment_result": user.get('last_assessment_result', None),
            "latest_assessment": None
        }
        
        # Include latest assessment summary
        if latest_assessment:
            user_profile["latest_assessment"] = {
                "assessment_id": str(latest_assessment['_id']),
                "timestamp": latest_assessment['timestamp'].isoformat(),
                "risk_level": latest_assessment.get('final_result', {}).get('risk_level'),
                "score": latest_assessment.get('questionnaire', {}).get('score')
            }
        
        return jsonify({
            "success": True,
            "user": user_profile
        }), 200
    
    except Exception as e:
        app.logger.error(f"Error retrieving user profile: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/user/<user_id>', methods=['PUT'])
def update_user_profile(user_id):
    """
    Update user profile information.
    
    Expected JSON payload:
    {
        "name": "Updated Name",
        "email": "newemail@gmail.com"
    }
    
    Returns:
        JSON: Updated user profile
    """
    try:
        data = request.get_json()
        
        # Validate user exists
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        # Check if new email already exists
        if 'email' in data and data['email'] != user['email']:
            existing = mongo.db.users.find_one({"email": data['email']})
            if existing:
                return jsonify({
                    "success": False,
                    "error": "Email already in use"
                }), 400
        
        # Update allowed fields
        update_data = {}
        allowed_fields = ['name', 'email']
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        update_data['updated_at'] = datetime.now()
        
        # Perform update
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "user": {
                "user_id": str(user['_id']),
                "name": update_data.get('name', user.get('name')),
                "email": update_data.get('email', user.get('email'))
            }
        }), 200
    
    except Exception as e:
        app.logger.error(f"Error updating user profile: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/api/submit-assessment', methods=['POST'])
def submit_assessment():
    """
    Submit and store assessment with comprehensive data.
    
    Expected JSON payload:
    {
        "user_id": "user_id_string",
        "responses": {all questionnaire responses},
        "g1": "Section G text response (optional)",
        "g2": "Section G text response (optional)",
        "g3": "Section G text response (optional)"
    }
    
    Returns:
        JSON: Assessment result with stored assessment ID
    """
    try:
        data = request.get_json()
        
        # Validate user_id
        user_id = data.get('user_id')
        if not user_id or str(user_id).startswith('guest_'):
            logger.warning(f"Invalid user submission: {user_id}")
            return jsonify({
                "success": False,
                "message": "Invalid or guest user not allowed"
            }), 400
        
        # Verify user exists in database
        try:
            user_obj_id = ObjectId(user_id)
        except:
            return jsonify({
                "success": False,
                "message": "Invalid user ID format"
            }), 400
        
        user = mongo.db.users.find_one({"_id": user_obj_id})
        if not user:
            logger.warning(f"User not found: {user_id}")
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        # Get all responses
        all_responses = data.get('responses', {})
        
        # Extract open-ended text responses from Section G
        text_responses = [
            all_responses.get('g1', ''),
            all_responses.get('g2', ''),
            all_responses.get('g3', '')
        ]
        # Filter out empty responses
        text_responses = [r for r in text_responses if r and r.strip()]
        
        # Extract questionnaire responses (skip reflection section)
        questionnaire_responses = {
            k: v for k, v in all_responses.items() 
            if k not in ['g1', 'g2', 'g3']  # g1, g2, g3 are reflection section
        }
        
        # Use WellnessEngine for comprehensive assessment processing
        logger.info(f"Processing comprehensive assessment with {len(questionnaire_responses)} questionnaire responses")
        
        # Get activities completed count (handle both list and int formats)
        activities_data = data.get('activities_completed', 0)
        if isinstance(activities_data, list):
            activities_completed = len(activities_data)  # Convert list to count
        else:
            activities_completed = int(activities_data) if activities_data else 0
        
        logger.info(f"Activities data received: {activities_data} (type: {type(activities_data).__name__})")
        logger.info(f"Activities completed: {activities_completed}")
        
        # Call wellness_engine.process_assessment for complete assessment
        wellness_result = wellness_engine.process_assessment(
            user_id=str(user_obj_id),
            questionnaire_responses=questionnaire_responses,
            text_responses=text_responses,
            activities_completed=activities_completed
        )
        
        # Extract results from wellness_engine
        final_score = wellness_result.get('final_score', 0)
        risk_level = wellness_result.get('risk_level', 'Unknown')
        assessment_id = wellness_result.get('assessment_id', str(uuid.uuid4()))
        raw_breakdown = wellness_result.get('breakdown', {})
        
        logger.info(f"Raw breakdown from wellness_engine: {raw_breakdown}")
        logger.info(f"Activity score in breakdown: {raw_breakdown.get('activity', 'MISSING')}")
        
        emotions = wellness_result.get('emotions', {})
        timestamp = wellness_result.get('timestamp', datetime.now(timezone.utc))
        
        # Format breakdown for frontend display
        breakdown = {
            "questionnaire": {
                "name": "Questionnaire",
                "score": raw_breakdown.get('questionnaire', 0),
                "max": 50
            },
            "nlp": {
                "name": "NLP Analysis",
                "score": raw_breakdown.get('nlp', 0),
                "max": 30
            },
            "activity": {
                "name": "Activity",
                "score": raw_breakdown.get('activity', 0),
                "max": 20
            }
        }
        
        # NLP analysis on Section G if provided
        nlp_result = None
        if text_responses:
            try:
                logger.info(f"Analyzing {len(text_responses)} open-ended responses with NLP")
                nlp_result = nlp_analyzer.analyze_text(text_responses)
                logger.info(f"NLP Analysis result: {nlp_result.get('prediction', 'Unknown')}")
            except Exception as nlp_error:
                logger.error(f"NLP analysis failed: {str(nlp_error)}")
                nlp_result = {
                    "prediction": "Normal",
                    "confidence": 0.0,
                    "probabilities": {"Normal": 0.25, "Anxiety": 0.25, "Depression": 0.25, "High Stress": 0.25},
                    "message": "NLP analysis unavailable",
                    "error": str(nlp_error)
                }
        else:
            nlp_result = {
                "prediction": "Normal",
                "confidence": 0.0,
                "probabilities": {"Normal": 0.25, "Anxiety": 0.25, "Depression": 0.25, "High Stress": 0.25},
                "message": "No text responses provided"
            }
        
        # Get recommended activities based on risk level
        logger.info(f"Getting recommended activities for risk level: {risk_level}")
        recommended_activities = decision_engine.recommend_activities(risk_level)
        
        # Create comprehensive assessment document
        assessment_doc = {
            "user_id": str(user_obj_id),
            "user_email": user.get('email'),
            "user_name": user.get('name'),
            "timestamp": timestamp,
            "final_score": final_score,
            "final_result": {
                "risk_level": risk_level,
                "recommendation": wellness_result.get('recommendation', '')
            },
            "questionnaire": {
                "responses": questionnaire_responses,
                "score": final_score,
                "breakdown": breakdown
            },
            "reflection_section": {
                "text_responses": text_responses,
                "nlp_analysis": nlp_result
            },
            "recommended_activities": recommended_activities,
            "assessment_metadata": {
                "total_responses": len(all_responses),
                "categories_answered": list(questionnaire_responses.keys()),
                "text_responses_count": len(text_responses),
                "assessment_version": "3.0",
                "wellness_engine_processed": True,
                "huggingface_used": nlp_result.get('model', 'Unknown') if nlp_result else False
            }
        }
        
        # Insert into MongoDB
        logger.info(f"Inserting assessment for user {user_id}")
        result = assessments_col.insert_one(assessment_doc)
        assessment_id = str(result.inserted_id)
        
        # Update user's assessment count
        mongo.db.users.update_one(
            {"_id": user_obj_id},
            {
                "$inc": {"assessments_taken": 1},
                "$set": {
                    "last_assessment": datetime.now(timezone.utc),
                    "last_assessment_result": risk_level
                }
            }
        )
        
        logger.info(f"✅ Assessment saved for user {user_id}: {assessment_id}")
        
        return jsonify({
            "success": True,
            "assessment_id": assessment_id,
            "final_score": final_score,
            "status": "Completed",
            "risk_level": risk_level,
            "recommendation": wellness_result.get('recommendation', ''),
            "recommended_activities": recommended_activities,
            "nlp_prediction": nlp_result.get('prediction', 'Normal') if nlp_result else 'N/A',
            "nlp_confidence": nlp_result.get('confidence', 0.0) if nlp_result else 0.0,
            "breakdown": breakdown,
            "emotions": emotions,
            "message": "Assessment stored successfully"
        }), 201
    
    except ValueError as e:
        logger.error(f"Invalid user ID format: {str(e)}")
        return jsonify({"success": False, "error": "Invalid user ID format"}), 400
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error submitting assessment: {error_msg}", exc_info=True)
        return jsonify({"success": False, "error": f"Assessment submission failed: {error_msg}"}), 500

@app.route('/api/latest-assessment/<user_id>', methods=['GET'])
def get_latest_assessment(user_id):
    """
    Get the latest assessment for a user.
    
    Args:
        user_id: User identifier
    
    Returns:
        JSON: Latest assessment with detailed results
    """
    try:
        # Retrieve latest assessment
        assessment = mongo.db.assessments.find_one(
            {"user_id": user_id},
            sort=[("timestamp", -1)]
        )
        
        if not assessment:
            return jsonify({
                "success": False,
                "message": "No assessment found",
                "assessment": None
            }), 404
        
        # Convert ObjectId to string for JSON serialization
        assessment["_id"] = str(assessment["_id"])
        if isinstance(assessment.get("timestamp"), datetime):
            assessment["timestamp"] = assessment["timestamp"].isoformat()
        
        return jsonify({
            "success": True,
            "assessment": assessment
        }), 200
    
    except Exception as e:
        app.logger.error(f"Error retrieving latest assessment: {str(e)}")
        return jsonify({"error": f"Failed to retrieve assessment: {str(e)}"}), 500


@app.route('/api/user-history/<user_id>', methods=['GET'])
def get_user_history(user_id):
    """
    Retrieve assessment history for a specific user.
    
    Args:
        user_id: Unique identifier for the user
    
    Returns:
        JSON: User's assessment history with scores and dates
    """
    try:
        # Retrieve user's assessments from MongoDB
        assessments = list(mongo.db.assessments.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(50))  # Get last 50 assessments
        
        # Convert ObjectId and datetime for JSON serialization
        for assessment in assessments:
            assessment["_id"] = str(assessment["_id"])
            if isinstance(assessment.get("timestamp"), datetime):
                assessment["timestamp"] = assessment["timestamp"].isoformat()
        
        return jsonify({
            "user_id": user_id,
            "assessment_count": len(assessments),
            "assessments": assessments
        }), 200
    
    except Exception as e:
        app.logger.error(f"Error retrieving user history: {str(e)}")
        return jsonify({"error": "Failed to retrieve user history"}), 500

# ============================================================================
# NEW WELLNESS ENGINE ENDPOINTS (Professional Hybrid Scoring System)
# ============================================================================

@app.route('/api/wellness/submit', methods=['POST'])
def submit_wellness_assessment():
    """
    Submit comprehensive wellness assessment with hybrid scoring.
    
    Includes: questionnaire, NLP emotion analysis, activity tracking
    
    Expected JSON payload:
    {
        "user_id": "user_id_string",
        "questionnaire_responses": {questionnaire answers},
        "text_responses": ["text1", "text2", "text3"],
        "activities_completed": 3
    }
    
    Returns:
        Comprehensive assessment result with scores, emotions, trends
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        # Validate user
        if not user_id:
            return jsonify(ResultFormatter.format_error_response(
                "user_id is required",
                "MISSING_USER_ID"
            )), 400
        
        try:
            user_obj_id = ObjectId(user_id)
        except:
            return jsonify(ResultFormatter.format_error_response(
                "Invalid user ID format",
                "INVALID_USER_ID"
            )), 400
        
        user = mongo.db.users.find_one({"_id": user_obj_id})
        if not user:
            return jsonify(ResultFormatter.format_error_response(
                "User not found",
                "USER_NOT_FOUND"
            )), 404
        
        # Extract data
        questionnaire_responses = data.get('questionnaire_responses', {})
        text_responses = data.get('text_responses', [])
        activities_completed = data.get('activities_completed', 0)
        
        # Process assessment through wellness engine
        logger.info(f"Processing wellness assessment for user {user_id}")
        
        assessment_result = wellness_engine.process_assessment(
            user_id=user_id,
            questionnaire_responses=questionnaire_responses,
            text_responses=[r for r in text_responses if r and r.strip()],
            activities_completed=max(0, int(activities_completed))
        )
        
        # Check for emergency
        if assessment_result.get('emergency_flag'):
            helpline = wellness_engine.get_emergency_helpline_response()
            assessment_result['helpline_info'] = helpline
        
        # Format response
        formatted_response = ResultFormatter.format_assessment_result(assessment_result)
        
        logger.info(f"✅ Wellness assessment completed for {user_id}: Score {assessment_result.get('final_score')}")
        
        return jsonify(formatted_response), 201
        
    except Exception as e:
        logger.error(f"Error in wellness assessment: {str(e)}", exc_info=True)
        return jsonify(ResultFormatter.format_error_response(
            f"Assessment processing failed: {str(e)}",
            "ASSESSMENT_FAILED"
        )), 500


@app.route('/api/wellness/history/<user_id>', methods=['GET'])
def get_wellness_history(user_id):
    """
    Retrieve user's assessment history with wellness data.
    
    Args:
        user_id: User identifier
        days: Optional query parameter for number of days (default: 30)
    
    Returns:
        Assessment history with scores and trends
    """
    try:
        # Validate user
        try:
            user_obj_id = ObjectId(user_id)
        except:
            return jsonify(ResultFormatter.format_error_response(
                "Invalid user ID format",
                "INVALID_USER_ID"
            )), 400
        
        user = mongo.db.users.find_one({"_id": user_obj_id})
        if not user:
            return jsonify(ResultFormatter.format_error_response(
                "User not found",
                "USER_NOT_FOUND"
            )), 404
        
        # Get optional days parameter
        days = request.args.get('days', 30, type=int)
        
        # Retrieve assessments
        assessments = wellness_engine.get_user_assessments(user_id, days)
        
        # Format response
        formatted_response = ResultFormatter.format_history_response(assessments, user_id)
        
        return jsonify(formatted_response), 200
        
    except Exception as e:
        logger.error(f"Error retrieving wellness history: {str(e)}")
        return jsonify(ResultFormatter.format_error_response(
            f"Failed to retrieve history: {str(e)}",
            "HISTORY_FAILED"
        )), 500


@app.route('/api/wellness/rolling-average/<user_id>', methods=['GET'])
def get_rolling_average(user_id):
    """
    Get 7-day rolling average wellness score.
    
    Args:
        user_id: User identifier
    
    Returns:
        Rolling average score and trend data
    """
    try:
        # Validate user
        try:
            user_obj_id = ObjectId(user_id)
        except:
            return jsonify(ResultFormatter.format_error_response(
                "Invalid user ID format",
                "INVALID_USER_ID"
            )), 400
        
        user = mongo.db.users.find_one({"_id": user_obj_id})
        if not user:
            return jsonify(ResultFormatter.format_error_response(
                "User not found",
                "USER_NOT_FOUND"
            )), 404
        
        # Calculate rolling average
        rolling_avg = wellness_engine.calculate_rolling_average(user_id, days=7)
        
        # Calculate trend
        trend_data = wellness_engine.calculate_trend(user_id)
        
        return jsonify({
            "status": "success",
            "user_id": user_id,
            "rolling_average": rolling_avg,
            "trend": trend_data,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error calculating rolling average: {str(e)}")
        return jsonify(ResultFormatter.format_error_response(
            f"Failed to calculate rolling average: {str(e)}",
            "ROLLING_AVG_FAILED"
        )), 500


@app.route('/api/wellness/latest/<user_id>', methods=['GET'])
def get_latest_wellness_assessment(user_id):
    """
    Get latest wellness assessment with all details.
    
    Args:
        user_id: User identifier
    
    Returns:
        Latest assessment with full breakdown
    """
    try:
        # Validate user
        try:
            user_obj_id = ObjectId(user_id)
        except:
            return jsonify(ResultFormatter.format_error_response(
                "Invalid user ID format",
                "INVALID_USER_ID"
            )), 400
        
        user = mongo.db.users.find_one({"_id": user_obj_id})
        if not user:
            return jsonify(ResultFormatter.format_error_response(
                "User not found",
                "USER_NOT_FOUND"
            )), 404
        
        # Get latest assessment
        assessments = wellness_engine.get_user_assessments(user_id, days=30)
        
        if not assessments:
            return jsonify({
                "status": "success",
                "message": "No assessments found",
                "assessment": None
            }), 200
        
        latest = assessments[0]  # Already sorted by date desc
        
        return jsonify({
            "status": "success",
            "user_id": user_id,
            "assessment": {
                "date": latest.get('date', datetime.utcnow()).isoformat(),
                "final_score": latest.get('final_score', 0),
                "questionnaire_score": latest.get('questionnaire_score', 0),
                "nlp_score": latest.get('nlp_score', 0),
                "activity_score": latest.get('activity_score', 0),
                "emotions": latest.get('emotions', {}),
                "emergency_flag": latest.get('emergency_flag', False)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving latest wellness assessment: {str(e)}")
        return jsonify(ResultFormatter.format_error_response(
            f"Failed to retrieve latest assessment: {str(e)}",
            "LATEST_FAILED"
        )), 500


@app.route('/api/wellness/chart-data/<user_id>', methods=['GET'])
def get_chart_data(user_id):
    """
    Get emotion chart data for visualization.
    
    Args:
        user_id: User identifier
    
    Returns:
        Chart.js compatible emotion distribution data
    """
    try:
        # Get latest assessment
        try:
            user_obj_id = ObjectId(user_id)
        except:
            return jsonify(ResultFormatter.format_error_response(
                "Invalid user ID format",
                "INVALID_USER_ID"
            )), 400
        
        user = mongo.db.users.find_one({"_id": user_obj_id})
        if not user:
            return jsonify(ResultFormatter.format_error_response(
                "User not found",
                "USER_NOT_FOUND"
            )), 404
        
        assessments = wellness_engine.get_user_assessments(user_id, days=7)
        
        if not assessments:
            emotions = {}
        else:
            emotions = assessments[0].get('emotions', {})
        
        chart_data = ResultFormatter.format_chart_data(emotions)
        
        return jsonify({
            "status": "success",
            "chart_data": chart_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving chart data: {str(e)}")
        return jsonify(ResultFormatter.format_error_response(
            f"Failed to retrieve chart data: {str(e)}",
            "CHART_DATA_FAILED"
        )), 500

# ============================================================================
# END WELLNESS ENGINE ENDPOINTS
# ============================================================================

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    Retrieve aggregated statistics for admin dashboard.
    
    Returns:
        JSON: System-wide statistics
    """
    try:
        # Aggregate risk level distribution
        pipeline = [
            {"$group": {"_id": "$final_result.risk_level", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        risk_distribution = list(mongo.db.assessments.aggregate(pipeline))
        
        # Total assessments count
        total_assessments = mongo.db.assessments.count_documents({})
        
        # Recent assessments (last 7 days)
        recent_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        recent_assessments = mongo.db.assessments.count_documents({
            "timestamp": {"$gte": recent_date}
        })
        
        return jsonify({
            "total_assessments": total_assessments,
            "recent_assessments": recent_assessments,
            "risk_distribution": risk_distribution
        }), 200
    
    except Exception as e:
        app.logger.error(f"Error retrieving statistics: {str(e)}")
        return jsonify({"error": "Failed to retrieve statistics"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)