"""
MindCare Result Formatter

Formats wellness assessment results for API responses and frontend display.
Ensures consistent JSON structure and includes all required fields.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ResultFormatter:
    """
    Format wellness assessment results for consistent API responses.
    """
    
    @staticmethod
    def format_assessment_result(assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format complete assessment result for API response.
        
        Args:
            assessment_data: Raw assessment data from WellnessEngine
            
        Returns:
            Formatted result dictionary
        """
        try:
            return {
                "status": "success",
                "data": {
                    "assessment_id": assessment_data.get("assessment_id"),
                    "timestamp": assessment_data.get("timestamp"),
                    "score": {
                        "final_score": assessment_data.get("final_score", 0),
                        "risk_level": assessment_data.get("risk_level", "Unknown"),
                        "risk_message": assessment_data.get("risk_message", ""),
                        "percentile": ResultFormatter._calculate_percentile(
                            assessment_data.get("final_score", 0)
                        )
                    },
                    "breakdown": {
                        "questionnaire": {
                            "score": assessment_data.get("breakdown", {}).get("questionnaire", 0),
                            "max": 50,
                            "percentage": round(
                                assessment_data.get("breakdown", {}).get("questionnaire", 0) / 50 * 100, 1
                            )
                        },
                        "nlp_emotion": {
                            "score": assessment_data.get("breakdown", {}).get("nlp", 0),
                            "max": 30,
                            "percentage": round(
                                assessment_data.get("breakdown", {}).get("nlp", 0) / 30 * 100, 1
                            )
                        },
                        "activity": {
                            "score": assessment_data.get("breakdown", {}).get("activity", 0),
                            "max": 20,
                            "percentage": round(
                                assessment_data.get("breakdown", {}).get("activity", 0) / 20 * 100, 1
                            )
                        }
                    },
                    "emotions": ResultFormatter._format_emotions(
                        assessment_data.get("emotions", {})
                    ),
                    "trend": {
                        "current_average": assessment_data.get("rolling_average", 0),
                        "previous_average": assessment_data.get("trend", {}).get("previous_avg", 0),
                        "change_percent": assessment_data.get("trend", {}).get("trend_percent", 0),
                        "direction": assessment_data.get("trend", {}).get("direction", "stable"),
                        "interpretation": ResultFormatter._interpret_trend(
                            assessment_data.get("trend", {}).get("direction", "stable"),
                            assessment_data.get("trend", {}).get("trend_percent", 0)
                        )
                    },
                    "emergency": {
                        "flag": assessment_data.get("emergency_flag", False),
                        "helpline": assessment_data.get("helpline_info") if assessment_data.get("emergency_flag") else None
                    }
                },
                "recommendations": ResultFormatter._get_recommendations(
                    assessment_data.get("risk_level", "Unknown")
                )
            }
        except Exception as e:
            logger.error(f"Error formatting assessment result: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def format_history_response(assessments: List[Dict], user_id: str) -> Dict[str, Any]:
        """
        Format assessment history for display.
        
        Args:
            assessments: List of assessment documents from MongoDB
            user_id: User ID
            
        Returns:
            Formatted history response
        """
        try:
            formatted_assessments = []
            
            for assessment in assessments:
                formatted_assessments.append({
                    "assessment_id": str(assessment.get("_id", "")),
                    "date": assessment.get("date", datetime.utcnow()).isoformat(),
                    "final_score": assessment.get("final_score", 0),
                    "risk_level": ResultFormatter._get_risk_level(
                        assessment.get("final_score", 0)
                    ),
                    "breakdown": {
                        "questionnaire": assessment.get("questionnaire_score", 0),
                        "nlp": assessment.get("nlp_score", 0),
                        "activity": assessment.get("activity_score", 0)
                    }
                })
            
            return {
                "status": "success",
                "user_id": user_id,
                "total_assessments": len(formatted_assessments),
                "assessments": formatted_assessments
            }
        except Exception as e:
            logger.error(f"Error formatting history: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def format_error_response(error_message: str, error_code: str = "UNKNOWN_ERROR") -> Dict[str, Any]:
        """
        Format error response.
        
        Args:
            error_message: Error message
            error_code: Error code
            
        Returns:
            Formatted error response
        """
        return {
            "status": "error",
            "error_code": error_code,
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _calculate_percentile(score: int) -> int:
        """
        Calculate percentile rank (simplified).
        
        Assumes normal distribution for demo purposes.
        """
        if score >= 80:
            return 90
        elif score >= 60:
            return 70
        elif score >= 40:
            return 45
        else:
            return 20
    
    @staticmethod
    def _get_risk_level(score: int) -> str:
        """Determine risk level from score."""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Moderate"
        elif score >= 20:
            return "Concerning"
        else:
            return "Critical"
    
    @staticmethod
    def _format_emotions(emotions: Dict[str, float]) -> Dict[str, Any]:
        """
        Format emotion data for chart display.
        
        Args:
            emotions: Raw emotion scores dictionary
            
        Returns:
            Formatted emotion data
        """
        if not emotions:
            return {
                "distribution": {},
                "dominant": "neutral",
                "summary": "No emotional data available"
            }
        
        # Sort emotions by score
        sorted_emotions = sorted(
            emotions.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        dominant = sorted_emotions[0][0] if sorted_emotions else "neutral"
        
        return {
            "distribution": {emotion: round(score, 3) for emotion, score in emotions.items()},
            "dominant": dominant,
            "dominance_score": round(sorted_emotions[0][1], 3) if sorted_emotions else 0,
            "summary": f"Most prominent emotion: {dominant}"
        }
    
    @staticmethod
    def _interpret_trend(direction: str, percent: float) -> str:
        """
        Get human-readable trend interpretation.
        
        Args:
            direction: "up", "down", or "stable"
            percent: Percentage change
            
        Returns:
            Interpretation string
        """
        if direction == "up":
            if percent > 20:
                return "Significant positive trend! Keep up the good work."
            elif percent > 5:
                return "Positive trend. Continue your wellness practices."
            else:
                return "Slight improvement. Stay consistent."
        elif direction == "down":
            if percent > 20:
                return "Significant decline. Consider reaching out for support."
            elif percent > 5:
                return "Noticeable decline. Review stress management practices."
            else:
                return "Slight decline. Monitor and adjust as needed."
        else:
            return "Wellness level is stable. Maintain current practices."
    
    @staticmethod
    def _get_recommendations(risk_level: str) -> List[Dict[str, str]]:
        """
        Get personalized recommendations based on risk level.
        
        Args:
            risk_level: Risk level category
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations_map = {
            "Excellent": [
                {
                    "category": "Maintain",
                    "action": "Continue your current healthy habits and routines"
                },
                {
                    "category": "Social",
                    "action": "Share your wellness strategies with friends and family"
                },
                {
                    "category": "Growth",
                    "action": "Consider exploring new mindfulness or creative activities"
                }
            ],
            "Good": [
                {
                    "category": "Sleep",
                    "action": "Maintain 7-9 hours of quality sleep nightly"
                },
                {
                    "category": "Exercise",
                    "action": "Continue physical activity: 30+ minutes, 3-5 times weekly"
                },
                {
                    "category": "Mindfulness",
                    "action": "Practice 10-15 minutes of meditation or breathing exercises daily"
                },
                {
                    "category": "Connection",
                    "action": "Maintain regular contact with supportive friends/family"
                }
            ],
            "Moderate": [
                {
                    "category": "Stress Management",
                    "action": "Implement daily relaxation techniques (yoga, breathing, meditation)"
                },
                {
                    "category": "Sleep Hygiene",
                    "action": "Establish consistent sleep schedule; avoid screens 1 hour before bed"
                },
                {
                    "category": "Physical Activity",
                    "action": "Increase to 30-45 minutes of exercise daily"
                },
                {
                    "category": "Social Support",
                    "action": "Strengthen connections; talk to people you trust about your feelings"
                },
                {
                    "category": "Professional Help",
                    "action": "Consider speaking with a counselor or therapist for additional guidance"
                }
            ],
            "Concerning": [
                {
                    "category": "Immediate Action",
                    "action": "Reach out to a mental health professional or counselor"
                },
                {
                    "category": "Crisis Line",
                    "action": "Keep USA 988 Suicide & Crisis Lifeline number handy (988)"
                },
                {
                    "category": "Daily Routine",
                    "action": "Establish simple daily routines for structure and stability"
                },
                {
                    "category": "Support System",
                    "action": "Inform trusted people about your struggles and ask for help"
                },
                {
                    "category": "Medical Check-up",
                    "action": "Schedule appointment with doctor to rule out physical health issues"
                }
            ],
            "Critical": [
                {
                    "category": "URGENT",
                    "action": "Contact emergency services (911) or National Suicide Prevention Lifeline (988)"
                },
                {
                    "category": "Immediate Support",
                    "action": "Reach out to a mental health professional immediately"
                },
                {
                    "category": "Safety",
                    "action": "Go to nearest emergency room or crisis center"
                },
                {
                    "category": "Support Network",
                    "action": "Tell someone you trust how you're feeling right now"
                },
                {
                    "category": "Follow-up",
                    "action": "Seek ongoing professional support and treatment"
                }
            ]
        }
        
        return recommendations_map.get(risk_level, [
            {
                "category": "General",
                "action": "Consider consulting with a mental health professional"
            }
        ])
    
    @staticmethod
    def format_chart_data(emotions: Dict[str, float]) -> Dict[str, Any]:
        """
        Format emotion data for Chart.js visualization.
        
        Args:
            emotions: Emotion distribution dictionary
            
        Returns:
            Data formatted for Chart.js
        """
        if not emotions:
            emotions = {
                "sadness": 0.20,
                "fear": 0.15,
                "anger": 0.15,
                "joy": 0.25,
                "love": 0.15,
                "surprise": 0.10
            }
        
        emotion_names = list(emotions.keys())
        emotion_values = [emotions[e] for e in emotion_names]
        
        # Define colors for emotions
        emotion_colors = {
            "sadness": "#4169E1",      # Royal blue
            "fear": "#DC143C",         # Crimson
            "anger": "#FF4500",        # Orange red
            "joy": "#FFD700",          # Gold
            "love": "#FF1493",         # Deep pink
            "surprise": "#00CED1"      # Dark turquoise
        }
        
        colors = [emotion_colors.get(e, "#808080") for e in emotion_names]
        
        return {
            "labels": [e.capitalize() for e in emotion_names],
            "data": {
                "labels": [e.capitalize() for e in emotion_names],
                "datasets": [
                    {
                        "data": emotion_values,
                        "backgroundColor": colors,
                        "borderColor": colors,
                        "borderWidth": 2
                    }
                ]
            }
        }
