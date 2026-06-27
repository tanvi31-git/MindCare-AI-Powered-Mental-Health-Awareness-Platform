"""
MindCare Wellness Engine

Professional hybrid scoring system combining:
- Questionnaire responses (0-50 points)
- NLP emotion analysis (0-30 points)  
- Activity completion (0-20 points)

Final wellness score: 0-100 (higher = better)
Includes emergency detection, rolling averages, and trend analysis.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from pymongo import MongoClient
from nlp_model import NLPAnalyzer

logger = logging.getLogger(__name__)


class WellnessEngine:
    """
    Core wellness scoring and analysis engine.
    
    Combines questionnaire, emotional analysis, and activity tracking
    into a comprehensive wellness index with trend analysis.
    """
    
    # Scoring constants
    QUESTIONNAIRE_MAX = 50
    NLP_MAX = 30
    ACTIVITY_MAX = 20
    FINAL_SCORE_MAX = 100
    
    # Answer value mappings
    ANSWER_VALUES = {
        "never": 10,
        "rarely": 8,
        "sometimes": 5,
        "often": 2,
        "almost always": 0,
        "very often": 0,
        # For reverse-scored items (e.g., "Very satisfied" should be high)
        "very satisfied": 10,
        "satisfied": 8,
        "neutral": 5,
        "dissatisfied": 2,
        "very dissatisfied": 0,
        # Confidence/connection scales
        "extremely confident": 10,
        "mostly confident": 8,
        "moderately confident": 5,
        "slightly confident": 2,
        "not confident at all": 0,
        "very connected": 10,
        "mostly connected": 8,
        "moderately connected": 5,
        "slightly connected": 2,
        "not connected at all": 0,
        # Hopeful scales
        "extremely hopeful": 10,
        "mostly hopeful": 8,
        "moderately hopeful": 5,
        "slightly hopeful": 2,
        "not at all hopeful": 0,
        # Stable scales
        "very stable": 10,
        "mostly stable": 8,
        "moderately stable": 5,
        "slightly unstable": 2,
        "very unstable": 0,
        # Pressure scales (reverse)
        "no pressure": 10,
        "mild pressure": 8,
        "moderate pressure": 5,
        "high pressure": 2,
        "extreme pressure": 0,
        # Hopeful/satisfaction (reverse numeric)
        5: 10,
        4: 8,
        3: 5,
        2: 2,
        1: 0,
    }
    
    # Negatively-worded questions: value 5 = BAD, must be reversed before scoring
    # Formula: reversed = (5 + 1) - raw  →  5→1, 4→2, 3→3, 2→4, 1→5
    REVERSE_SCORED_QUESTIONS = {
        'a4', 'a5',                          # Mood: exhausted, mood swings
        'b1', 'b2', 'b3', 'b4', 'b5',       # Anxiety: ALL negative
        'c1', 'c2', 'c4', 'c5',              # Stress: pressure, overwhelmed, exhausted, setbacks
        'd2', 'd3', 'd5',                    # Focus: difficulty focusing, procrastinating, loss of interest
        'e2', 'e3', 'e4',                    # Sleep: tired despite sleep, stress disrupts sleep, physical symptoms
        'f3', 'f5',                          # Social: loneliness, needs mental health attention
    }

    # Emergency keywords
    EMERGENCY_KEYWORDS = [
        "suicide",
        "kill myself",
        "self harm",
        "hopeless",
        "want to die",
        "end it all",
        "no point",
        "better off dead",
    ]
    
    # Risk level thresholds
    RISK_THRESHOLDS = {
        "excellent": (80, 100),      # 80-100
        "good": (60, 79),            # 60-79
        "moderate": (40, 59),        # 40-59
        "concerning": (20, 39),      # 20-39
        "critical": (0, 19),         # 0-19
    }
    
    def __init__(self, db_client: MongoClient = None):
        """
        Initialize the wellness engine.
        
        Args:
            db_client: MongoDB client connection
        """
        self.db_client = db_client
        self.nlp_analyzer = NLPAnalyzer()
        self.db = None
        self.assessments_collection = None
        self.users_collection = None
        
        if db_client:
            self.db = db_client['mindcare']
            self.assessments_collection = self.db['assessments']
            self.users_collection = self.db['users']
    
    def calculate_questionnaire_score(self, responses: Dict[str, Any]) -> int:
        """
        Calculate questionnaire score from MCQ responses.
        
        Converts numeric 1-5 Likert scale responses to wellness score on 0-50 scale:
        - Higher numeric values (5) = Better wellness
        - Lower numeric values (1) = Lower wellness
        
        Args:
            responses: Dictionary of question answers (numeric or string)
            
        Returns:
            Questionnaire score (0-50)
        """
        try:
            numeric_values = []
            
            for key, value in responses.items():
                # Skip reflection section (g1, g2, g3)
                if key.startswith('g'):
                    continue
                
                try:
                    # Convert to integer
                    if isinstance(value, str):
                        numeric_val = int(value.strip())
                    else:
                        numeric_val = int(value)
                    
                    # Validate range (1-5 Likert scale)
                    if 1 <= numeric_val <= 5:
                        # Reverse-score negatively-worded questions
                        # so "Almost Always exhausted" = 1 (bad), not 5 (good)
                        if key in self.REVERSE_SCORED_QUESTIONS:
                            numeric_val = 6 - numeric_val  # 5→1, 4→2, 3→3, 2→4, 1→5
                        numeric_values.append(numeric_val)
                except (ValueError, TypeError):
                    # Skip unmapped answers
                    continue
            
            # Calculate score
            if not numeric_values:
                return 0
            
            # Sum all values and normalize to 0-50 scale
            # Max possible with all 5s: 5 * num_questions
            # We normalize: (total / (5 * num_questions)) * 50
            total_score = sum(numeric_values)
            max_possible = 5 * len(numeric_values)
            
            # Calculate percentage (0-100), then scale to 0-50
            percentage = (total_score / max_possible) * 100
            questionnaire_score = int((percentage / 100) * self.QUESTIONNAIRE_MAX)
            
            return questionnaire_score
            
        except Exception as e:
            logger.error(f"Error calculating questionnaire score: {str(e)}")
            return 0
    
    def calculate_nlp_emotion_score(self, text_responses: List[str]) -> Tuple[int, Dict[str, float]]:
        """
        Calculate NLP emotion score from text responses.
        
        Uses emotion analysis model to detect emotional states:
        - High stress emotions (sadness, fear, anger) → lower score
        - Positive emotions (joy, love, surprise) → higher score
        
        Formula: nlp_score = (1 - stress_emotion_intensity) * 30
        
        Args:
            text_responses: List of text responses
            
        Returns:
            Tuple of (score 0-30, emotion_distribution dict)
        """
        try:
            if not text_responses or all(not r.strip() for r in text_responses):
                return 0, {}
            
            # Analyze emotions
            emotion_result = self.nlp_analyzer.analyze_emotions(text_responses)
            
            if not emotion_result or not emotion_result.get('emotion_scores'):
                return 0, {}
            
            emotion_scores = emotion_result['emotion_scores']
            
            # Extract negative (stress) emotions
            sadness = emotion_scores.get('sadness', 0)
            fear = emotion_scores.get('fear', 0)
            anger = emotion_scores.get('anger', 0)
            disgust = emotion_scores.get('disgust', 0)
            
            # Extract positive emotions
            joy = emotion_scores.get('joy', 0)
            love = emotion_scores.get('love', 0)
            surprise = emotion_scores.get('surprise', 0)  # can be positive
            
            # Calculate stress intensity (0-1): weighted sum of negative emotions
            stress_intensity = min(1.0, (sadness * 0.4 + fear * 0.35 + anger * 0.15 + disgust * 0.1))
            
            # Calculate positivity (0-1)
            positivity = min(1.0, (joy * 0.5 + love * 0.35 + surprise * 0.15))
            
            # Final NLP wellness = positivity pulls UP, stress pulls DOWN
            # Range 0-30: high stress → low score, high positivity → high score
            wellness_ratio = max(0.0, positivity - stress_intensity + 0.5)  # center at 0.5
            wellness_ratio = min(1.0, wellness_ratio)
            nlp_score = int(wellness_ratio * self.NLP_MAX)
            nlp_score = max(0, min(nlp_score, self.NLP_MAX))
            
            return nlp_score, emotion_scores
            
        except Exception as e:
            logger.error(f"Error calculating NLP emotion score: {str(e)}")
            return 0, {}
    
    def calculate_activity_score(self, activities_completed: int) -> int:
        """
        Calculate activity completion score.
        
        Formula: activity_score = min(activities_completed * 5, 20)
        
        Args:
            activities_completed: Number of completed activities
            
        Returns:
            Activity score (0-20)
        """
        try:
            if activities_completed < 0:
                activities_completed = 0
            
            score = min(activities_completed * 5, self.ACTIVITY_MAX)
            return int(score)
            
        except Exception as e:
            logger.error(f"Error calculating activity score: {str(e)}")
            return 0
    
    def check_emergency_keywords(self, text: str) -> bool:
        """
        Check if text contains emergency keywords indicating crisis.
        
        Emergency keywords:
        - "suicide", "kill myself", "self harm", "hopeless", "want to die"
        
        Args:
            text: Text to scan
            
        Returns:
            True if emergency keyword found, False otherwise
        """
        try:
            if not text:
                return False
            
            text_lower = text.lower()
            
            for keyword in self.EMERGENCY_KEYWORDS:
                if keyword in text_lower:
                    logger.warning(f"Emergency keyword detected: {keyword}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking emergency keywords: {str(e)}")
            return False
    
    def calculate_final_score(
        self,
        questionnaire_score: int,
        nlp_score: int,
        activity_score: int
    ) -> int:
        """
        Calculate final wellness score (0-100).
        
        Formula: final_score = questionnaire_score + nlp_score + activity_score
        
        Args:
            questionnaire_score: Score from questionnaire (0-50)
            nlp_score: Score from emotion analysis (0-30)
            activity_score: Score from activities (0-20)
            
        Returns:
            Final wellness score (0-100)
        """
        try:
            total = questionnaire_score + nlp_score + activity_score
            # Ensure within range
            final_score = max(0, min(total, self.FINAL_SCORE_MAX))
            return int(final_score)
            
        except Exception as e:
            logger.error(f"Error calculating final score: {str(e)}")
            return 0
    
    def get_risk_level(self, score: int) -> str:
        """
        Determine risk level from wellness score.
        
        Risk levels:
        - 80-100: Excellent
        - 60-79: Good
        - 40-59: Moderate
        - 20-39: Concerning
        - 0-19: Critical
        
        Args:
            score: Wellness score (0-100)
            
        Returns:
            Risk level category string
        """
        try:
            for level, (min_score, max_score) in self.RISK_THRESHOLDS.items():
                if min_score <= score <= max_score:
                    return level.capitalize()
            
            return "Unknown"
            
        except Exception as e:
            logger.error(f"Error determining risk level: {str(e)}")
            return "Unknown"
    
    def save_assessment(
        self,
        user_id: str,
        questionnaire_score: int,
        nlp_score: int,
        activity_score: int,
        final_score: int,
        emotions: Dict[str, float],
        emergency_flag: bool = False
    ) -> Optional[str]:
        """
        Save assessment results to MongoDB.
        
        Args:
            user_id: User ID
            questionnaire_score: Questionnaire component score
            nlp_score: NLP emotion component score
            activity_score: Activity component score
            final_score: Final wellness score
            emotions: Emotion distribution dictionary
            emergency_flag: Whether emergency keywords were detected
            
        Returns:
            Assessment ID if successful, None otherwise
        """
        try:
            if self.assessments_collection is None:
                logger.warning("MongoDB not initialized")
                return None
            
            assessment = {
                "user_id": user_id,
                "date": datetime.utcnow(),
                "questionnaire_score": questionnaire_score,
                "nlp_score": nlp_score,
                "activity_score": activity_score,
                "final_score": final_score,
                "emotions": emotions,
                "emergency_flag": emergency_flag,
                "created_at": datetime.utcnow()
            }
            
            result = self.assessments_collection.insert_one(assessment)
            logger.info(f"Assessment saved for user {user_id}: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error saving assessment: {str(e)}")
            return None
    
    def get_user_assessments(self, user_id: str, days: int = 7) -> List[Dict]:
        """
        Retrieve user's assessments from last N days.
        
        Args:
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            List of assessment documents
        """
        try:
            if self.assessments_collection is None:
                return []
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            assessments = list(self.assessments_collection.find({
                "user_id": user_id,
                "date": {"$gte": cutoff_date}
            }).sort("date", -1))
            
            return assessments
            
        except Exception as e:
            logger.error(f"Error retrieving assessments: {str(e)}")
            return []
    
    def calculate_rolling_average(self, user_id: str, days: int = 7) -> float:
        """
        Calculate 7-day rolling average of wellness scores.
        
        Args:
            user_id: User ID
            days: Number of days for rolling average
            
        Returns:
            Rolling average score (0-100)
        """
        try:
            assessments = self.get_user_assessments(user_id, days)
            
            if not assessments:
                return 0.0
            
            scores = [a.get('final_score', 0) for a in assessments]
            rolling_avg = sum(scores) / len(scores)
            
            return round(rolling_avg, 2)
            
        except Exception as e:
            logger.error(f"Error calculating rolling average: {str(e)}")
            return 0.0
    
    def calculate_trend(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate wellness trend by comparing recent vs previous week.
        
        Compares:
        - Last 7 days average
        - Previous 7 days average
        
        Returns:
        {
            "current_avg": float,
            "previous_avg": float,
            "trend_percent": float,
            "direction": "up" or "down"
        }
        
        Args:
            user_id: User ID
            
        Returns:
            Trend analysis dictionary
        """
        try:
            # Get current 7-day average
            current_assessments = self.get_user_assessments(user_id, days=7)
            current_scores = [a.get('final_score', 0) for a in current_assessments]
            current_avg = sum(current_scores) / len(current_scores) if current_scores else 0
            
            # Get previous 7-day average (days 8-14)
            all_assessments = self.get_user_assessments(user_id, days=14)
            previous_scores = []
            
            cutoff_current = datetime.utcnow() - timedelta(days=7)
            for assessment in all_assessments:
                if assessment.get('date', datetime.utcnow()) < cutoff_current:
                    previous_scores.append(assessment.get('final_score', 0))
            
            previous_avg = sum(previous_scores) / len(previous_scores) if previous_scores else current_avg
            
            # Calculate trend percentage
            if previous_avg == 0:
                trend_percent = 0
                direction = "stable"
            else:
                trend_percent = ((current_avg - previous_avg) / previous_avg) * 100
                direction = "up" if trend_percent > 0 else "down"
            
            return {
                "current_avg": round(current_avg, 2),
                "previous_avg": round(previous_avg, 2),
                "trend_percent": round(abs(trend_percent), 2),
                "direction": direction
            }
            
        except Exception as e:
            logger.error(f"Error calculating trend: {str(e)}")
            return {
                "current_avg": 0.0,
                "previous_avg": 0.0,
                "trend_percent": 0.0,
                "direction": "stable"
            }
    
    def get_risk_message(self, risk_level: str) -> str:
        """
        Get human-readable risk message based on risk level.
        
        Args:
            risk_level: Risk level string
            
        Returns:
            Message string
        """
        messages = {
            "Excellent": "Your mental wellness is excellent. Keep maintaining these healthy habits!",
            "Good": "Your mental wellness is good. Continue your positive practices.",
            "Moderate": "Your wellness shows some areas for improvement. Consider self-care activities.",
            "Concerning": "Your wellness indicates significant stress. Professional support is recommended.",
            "Critical": "Your wellness is critically low. Please reach out to a mental health professional immediately.",
        }
        
        return messages.get(risk_level, "Assessment complete. Consider consulting a mental health professional.")
    
    def process_assessment(
        self,
        user_id: str,
        questionnaire_responses: Dict[str, Any],
        text_responses: List[str],
        activities_completed: int = 0
    ) -> Dict[str, Any]:
        """
        Process complete assessment and return comprehensive results.
        
        Args:
            user_id: User ID
            questionnaire_responses: Dictionary of MCQ answers
            text_responses: List of open-ended text responses
            activities_completed: Number of completed activities
            
        Returns:
            Complete assessment result dictionary
        """
        try:
            # Check for emergency keywords
            combined_text = " ".join(text_responses)
            emergency_flag = self.check_emergency_keywords(combined_text)
            
            # Calculate component scores
            q_score = self.calculate_questionnaire_score(questionnaire_responses)
            nlp_score, emotions = self.calculate_nlp_emotion_score(text_responses)
            activity_score = self.calculate_activity_score(activities_completed)
            
            # Calculate final score
            final_score = self.calculate_final_score(q_score, nlp_score, activity_score)
            
            # EMERGENCY OVERRIDE: If crisis keywords detected, cap score at Critical/Concerning
            # regardless of questionnaire score — safety takes priority
            if emergency_flag:
                final_score = min(final_score, 25)  # Cap at "Concerning" max
                logger.warning(f"Emergency flag: score capped to {final_score} for user {user_id}")
            
            # Determine risk level
            risk_level = self.get_risk_level(final_score)
            
            # Get risk message
            risk_message = self.get_risk_message(risk_level)
            
            # Save to database
            assessment_id = self.save_assessment(
                user_id=user_id,
                questionnaire_score=q_score,
                nlp_score=nlp_score,
                activity_score=activity_score,
                final_score=final_score,
                emotions=emotions,
                emergency_flag=emergency_flag
            )
            
            # Calculate rolling averages and trends
            rolling_avg = self.calculate_rolling_average(user_id)
            trend_data = self.calculate_trend(user_id)
            
            # Build result
            result = {
                "assessment_id": assessment_id,
                "final_score": final_score,
                "risk_level": risk_level,
                "risk_message": risk_message,
                "emergency_flag": emergency_flag,
                "breakdown": {
                    "questionnaire": q_score,
                    "nlp": nlp_score,
                    "activity": activity_score
                },
                "rolling_average": rolling_avg,
                "trend": {
                    "current_avg": trend_data['current_avg'],
                    "previous_avg": trend_data['previous_avg'],
                    "trend_percent": trend_data['trend_percent'],
                    "direction": trend_data['direction']
                },
                "emotions": emotions,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Assessment processed for user {user_id}: Score {final_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing assessment: {str(e)}")
            return {
                "error": str(e),
                "final_score": 0,
                "risk_level": "Unknown"
            }
    
    def get_emergency_helpline_response(self) -> Dict[str, Any]:
        """
        Return emergency helpline information.
        
        Returns:
            Emergency response dictionary
        """
        return {
            "emergency_flag": True,
            "emergency_message": "We've detected concerning keywords in your responses. Please reach out for support immediately.",
            "helplines": {
                "national_suicide_prevention_lifeline": {
                    "number": "988",
                    "service": "National Suicide Prevention Lifeline (US)",
                    "available": "24/7"
                },
                "crisis_text_line": {
                    "code": "Text HOME to 741741",
                    "service": "Crisis Text Line",
                    "available": "24/7"
                },
                "international": {
                    "service": "International Association for Suicide Prevention",
                    "url": "https://www.iasp.info/resources/Crisis_Centres/"
                }
            },
            "actions": [
                "Call emergency services immediately if in acute crisis",
                "Reach out to a trusted friend or family member",
                "Contact a mental health professional",
                "Visit your nearest emergency room if needed"
            ]
        }