"""
MindCare Decision Engine

This is the AI decision layer of the MindCare system.
It combines rule-based scoring with ML predictions to determine final risk levels
and generate appropriate interventions.
"""

from typing import Dict, List, Any
from config import Config

HELPLINE_NUMBERS = Config.HELPLINE_NUMBERS
EMERGENCY_DISCLAIMER = Config.EMERGENCY_DISCLAIMER

class DecisionEngine:
    """
    Hybrid decision engine that combines questionnaire scores with NLP analysis.
    
    This class implements the core AI logic of the MindCare system by:
    1. Weighing evidence from different sources
    2. Applying clinical decision rules
    3. Generating personalized recommendations
    4. Ensuring safety protocols are followed
    """
    
    def __init__(self):
        """Initialize the decision engine with default parameters."""
        # Risk level weights for hybrid decision
        self.risk_weights = {
            "Low Risk": 1,
            "Moderate Risk": 2,
            "High Risk": 3
        }
        
        # NLP risk mapping
        self.nlp_risk_mapping = {
            "Normal": "Low Risk",
            "Anxiety": "Moderate Risk",
            "High Stress": "Moderate Risk",
            "Depression": "High Risk",
            "Uncertain": "Low Risk"  # Default to low risk when uncertain
        }
        
        # Confidence thresholds for decision making
        self.high_confidence_threshold = 0.8
        self.medium_confidence_threshold = 0.6
        
        # Intervention recommendations by risk level
        self.interventions = self._initialize_interventions()
    
    def make_decision(self, questionnaire_result: Dict[str, Any], nlp_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a final decision based on questionnaire and NLP results.
        
        Args:
            questionnaire_result: Result from the scoring engine
            nlp_result: Result from the NLP analyzer
            
        Returns:
            Dictionary containing final decision and recommendations
        """
        # Extract risk levels
        questionnaire_risk = questionnaire_result.get("risk_level", "Low Risk")
        nlp_prediction = nlp_result.get("prediction", "Normal")
        nlp_confidence = nlp_result.get("confidence", 0.0)
        
        # Map NLP prediction to risk level
        nlp_risk = self.nlp_risk_mapping.get(nlp_prediction, "Low Risk")
        
        # Apply hybrid decision logic
        final_risk = self._apply_hybrid_logic(
            questionnaire_risk, 
            nlp_risk, 
            nlp_prediction, 
            nlp_confidence
        )
        
        # Generate personalized recommendations
        recommendations = self._generate_recommendations(
            final_risk, 
            questionnaire_result, 
            nlp_result
        )
        
        # Create explanation
        explanation = self._generate_explanation(
            questionnaire_risk, 
            nlp_prediction, 
            nlp_confidence, 
            final_risk
        )
        
        return {
            "risk_level": final_risk,
            "questionnaire_risk": questionnaire_risk,
            "nlp_prediction": nlp_prediction,
            "nlp_confidence": nlp_confidence,
            "recommendations": recommendations,
            "explanation": explanation,
            "disclaimer": EMERGENCY_DISCLAIMER,
            "message": self._get_primary_message(final_risk)
        }
    
    def _apply_hybrid_logic(self, questionnaire_risk: str, nlp_risk: str, 
                           nlp_prediction: str, nlp_confidence: float) -> str:
        """
        Apply hybrid decision logic to determine final risk level.
        
        Args:
            questionnaire_risk: Risk level from questionnaire
            nlp_risk: Risk level from NLP analysis
            nlp_prediction: Raw NLP prediction
            nlp_confidence: Confidence of NLP prediction
            
        Returns:
            Final risk level
        """
        # Get numeric values for comparison
        questionnaire_score = self.risk_weights[questionnaire_risk]
        nlp_score = self.risk_weights[nlp_risk]
        
        # Special case: High confidence depression or anxiety detection
        if (nlp_prediction in ["Depression", "Anxiety"] and 
            nlp_confidence >= self.high_confidence_threshold and
            questionnaire_risk != "Low Risk"):
            return "High Risk"
        
        # Special case: High confidence depression detection even with low questionnaire risk
        if (nlp_prediction == "Depression" and 
            nlp_confidence >= self.high_confidence_threshold):
            return "High Risk"
        
        # General rule: Take the higher risk level
        if questionnaire_score >= nlp_score:
            return questionnaire_risk
        else:
            # Only upgrade risk if NLP confidence is sufficient
            if nlp_confidence >= self.medium_confidence_threshold:
                return nlp_risk
            else:
                return questionnaire_risk
    
    def _generate_recommendations(self, final_risk: str, questionnaire_result: Dict[str, Any], 
                                 nlp_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendations based on risk level.
        
        Args:
            final_risk: Final determined risk level
            questionnaire_result: Result from questionnaire
            nlp_result: Result from NLP analysis
            
        Returns:
            List of recommendation objects
        """
        recommendations = []
        
        if final_risk == "High Risk":
            # Safety first - provide helpline information
            recommendations.append({
                "type": "emergency",
                "title": "Immediate Support",
                "description": "Please reach out to one of these helplines for immediate support:",
                "actions": HELPLINE_NUMBERS,
                "priority": "high"
            })
            
            recommendations.append({
                "type": "professional",
                "title": "Professional Help",
                "description": "We strongly recommend speaking with a mental health professional as soon as possible.",
                "actions": [
                    "Schedule an appointment with a counselor or therapist",
                    "Speak with your primary care physician about your mental health",
                    "Consider a comprehensive mental health evaluation"
                ],
                "priority": "high"
            })
        
        elif final_risk == "Moderate Risk":
            # Coping strategies
            recommendations.append({
                "type": "self_care",
                "title": "Coping Strategies",
                "description": "Try these evidence-based coping strategies:",
                "actions": [
                    "Practice deep breathing exercises for 5 minutes daily",
                    "Try journaling your thoughts and feelings",
                    "Engage in 30 minutes of physical activity each day",
                    "Reduce screen time, especially before bed",
                    "Practice mindfulness or meditation"
                ],
                "priority": "medium"
            })
            
            # Targeted recommendations based on NLP
            nlp_prediction = nlp_result.get("prediction", "Normal")
            if nlp_prediction == "Anxiety":
                recommendations.append({
                    "type": "targeted",
                    "title": "For Anxiety",
                    "description": "Specific strategies for managing anxiety:",
                    "actions": [
                        "Try the 5-4-3-2-1 grounding technique",
                        "Challenge anxious thoughts with evidence",
                        "Limit caffeine and alcohol intake",
                        "Establish a regular sleep routine"
                    ],
                    "priority": "medium"
                })
            elif nlp_prediction == "Depression":
                recommendations.append({
                    "type": "targeted",
                    "title": "For Low Mood",
                    "description": "Strategies that may help with low mood:",
                    "actions": [
                        "Set small, achievable goals for each day",
                        "Spend time in nature or sunlight when possible",
                        "Stay connected with supportive friends or family",
                        "Engage in activities you used to enjoy, even if motivation is low"
                    ],
                    "priority": "medium"
                })
            
            # Follow-up recommendation
            recommendations.append({
                "type": "monitoring",
                "title": "Monitor Your Progress",
                "description": "Keep track of your symptoms and retake this assessment in 2 weeks.",
                "actions": [
                    "Monitor your symptoms daily",
                    "Retake this assessment in 2 weeks",
                    "Consider speaking with a mental health professional if symptoms persist"
                ],
                "priority": "medium"
            })
        
        else:  # Low Risk
            # Wellness maintenance
            recommendations.append({
                "type": "wellness",
                "title": "Wellness Maintenance",
                "description": "Continue maintaining your mental health with these tips:",
                "actions": [
                    "Continue regular social connections",
                    "Maintain a balanced sleep schedule",
                    "Practice mindfulness or meditation",
                    "Engage in hobbies you enjoy",
                    "Consider periodic mental health check-ins"
                ],
                "priority": "low"
            })
        
        return recommendations
    
    def _generate_explanation(self, questionnaire_risk: str, nlp_prediction: str, 
                             nlp_confidence: float, final_risk: str) -> str:
        """
        Generate an explanation of how the decision was made.
        
        Args:
            questionnaire_risk: Risk level from questionnaire
            nlp_prediction: Raw NLP prediction
            nlp_confidence: Confidence of NLP prediction
            final_risk: Final determined risk level
            
        Returns:
            Explanation string
        """
        if final_risk == "High Risk":
            if nlp_prediction in ["Depression", "Anxiety"] and nlp_confidence >= 0.8:
                return (
                    f"Your assessment indicates high risk. Your questionnaire responses showed {questionnaire_risk.lower()}, "
                    f"and our text analysis detected {nlp_prediction.lower()} with high confidence ({nlp_confidence:.0%}). "
                    "This combination suggests you may benefit from professional support."
                )
            else:
                return (
                    f"Your assessment indicates high risk based on your questionnaire responses ({questionnaire_risk}) "
                    f"and text analysis results. We recommend seeking professional support."
                )
        elif final_risk == "Moderate Risk":
            return (
                f"Your assessment indicates moderate risk. Your questionnaire responses showed {questionnaire_risk.lower()}, "
                f"and our text analysis detected {nlp_prediction.lower()} with {nlp_confidence:.0%} confidence. "
                "Consider implementing the recommended coping strategies and monitoring your symptoms."
            )
        else:  # Low Risk
            return (
                f"Your assessment indicates low risk. Your questionnaire responses showed {questionnaire_risk.lower()}, "
                f"and our text analysis detected {nlp_prediction.lower()}. "
                "Continue practicing good mental health habits."
            )
    
    def _get_primary_message(self, final_risk: str) -> str:
        """
        Get the primary message based on risk level.
        
        Args:
            final_risk: Final determined risk level
            
        Returns:
            Primary message string
        """
        if final_risk == "High Risk":
            return "Based on your assessment, we recommend speaking with a mental health professional as soon as possible."
        elif final_risk == "Moderate Risk":
            return "Your responses suggest some areas of concern. Consider these coping strategies:"
        else:  # Low Risk
            return "Your mental health appears to be in a good state. Maintain your well-being with these tips:"
    
    def _initialize_interventions(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize intervention templates for different risk levels.
        
        Returns:
            Dictionary of intervention templates
        """
        return {
            "High Risk": {
                "message": "Based on your assessment, we recommend speaking with a mental health professional as soon as possible.",
                "requires_professional_help": True,
                "includes_helpline": True
            },
            "Moderate Risk": {
                "message": "Your responses suggest some areas of concern. Consider these coping strategies:",
                "requires_professional_help": False,
                "includes_helpline": False
            },
            "Low Risk": {
                "message": "Your mental health appears to be in a good state. Maintain your well-being with these tips:",
                "requires_professional_help": False,
                "includes_helpline": False
            }
        }
    
    def recommend_activities(self, stress_level: str) -> List[Dict[str, Any]]:
        """
        Recommend activities based on stress level.
        
        This method provides personalized activity recommendations with emoji icons
        and descriptions based on the user's stress category.
        
        Args:
            stress_level: The stress level category ("High", "Medium", "Low")
            
        Returns:
            List of activity recommendations with icons and descriptions
        """
        # Normalize stress level input
        stress_level = stress_level.lower().strip()
        
        if "high" in stress_level:
            return [
                {
                    "name": "Call trusted person",
                    "icon": "📞",
                    "description": "Reach out to someone you trust and talk about your feelings. Social support is crucial during high stress."
                },
                {
                    "name": "Guided breathing",
                    "icon": "🫁",
                    "description": "Practice deep breathing exercises (e.g., 4-7-8 breathing) to calm your nervous system."
                },
                {
                    "name": "Grounding exercise",
                    "icon": "🌍",
                    "description": "Use the 5-4-3-2-1 technique to bring yourself back to the present moment when feeling overwhelmed."
                },
                {
                    "name": "Professional counseling",
                    "icon": "🗣️",
                    "description": "Schedule an appointment with a mental health professional for immediate support."
                },
                {
                    "name": "Rest and relax",
                    "icon": "😌",
                    "description": "Take time to rest - find a quiet place and focus on your breathing and relaxation."
                }
            ]
        elif "medium" in stress_level or "moderate" in stress_level:
            return [
                {
                    "name": "Walk 20 mins",
                    "icon": "🚶",
                    "description": "Take a peaceful walk in nature or around your neighborhood to clear your mind."
                },
                {
                    "name": "Meditation",
                    "icon": "🧘",
                    "description": "Practice mindfulness meditation for 10-15 minutes to reduce stress and anxiety."
                },
                {
                    "name": "Limit screen time",
                    "icon": "📵",
                    "description": "Take a digital break - put away your phone and computer for at least 1-2 hours."
                },
                {
                    "name": "Creative activity",
                    "icon": "🎨",
                    "description": "Engage in creative pursuits like drawing, music, or crafting to channel emotions positively."
                },
                {
                    "name": "Yoga or stretching",
                    "icon": "🧘‍♀️",
                    "description": "Perform gentle yoga or stretching exercises to release physical tension and stress."
                }
            ]
        else:  # Low stress
            return [
                {
                    "name": "Gratitude journaling",
                    "icon": "📔",
                    "description": "Write down 3-5 things you're grateful for to boost your mood and perspective."
                },
                {
                    "name": "Workout",
                    "icon": "💪",
                    "description": "Engage in your favorite physical activity - exercise boosts mood and energy levels."
                },
                {
                    "name": "Reading",
                    "icon": "📚",
                    "description": "Read a book or engaging article for pleasure and mental stimulation."
                },
                {
                    "name": "Social connection",
                    "icon": "👥",
                    "description": "Spend quality time with friends or family to strengthen relationships."
                },
                {
                    "name": "Hobby time",
                    "icon": "🎸",
                    "description": "Dedicate time to hobbies and interests that bring you joy and fulfillment."
                }
            ]