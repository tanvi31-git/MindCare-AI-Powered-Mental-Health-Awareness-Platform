"""
MindCare Scoring Engine

This module contains the rule-based logic for calculating questionnaire scores
and determining risk levels based on clinical guidelines.
"""

from typing import Dict, List, Any, Tuple, Union

class ScoringEngine:
    """
    Rule-based scoring engine for questionnaire responses.
    
    This class implements a transparent, explainable scoring system that
    follows clinical guidelines for mental health assessment.
    """
    
    def __init__(self):
        """Initialize the scoring engine with default thresholds."""
        # Updated to match wellness engine (higher = better)
        self.critical_threshold = 20     # 0-19 = Critical
        self.concerning_threshold = 40   # 20-39 = Concerning
        self.moderate_threshold = 60     # 40-59 = Moderate
        self.good_threshold = 80         # 60-79 = Good
        # 80-100 = Excellent
        
        # Risk level categories
        self.risk_levels = ["Critical", "Concerning", "Moderate", "Good", "Excellent"]
        
        # Risk level mapping
        self.risk_level_mapping = {
            "Excellent": "Low Risk",
            "Good": "Low Risk", 
            "Moderate": "Moderate Risk",
            "Concerning": "High Risk",
            "Critical": "Critical"
        }
        
        # Subscale mappings (if questionnaire has sections)
        self.subscale_mappings = {
            "mood": [0, 1, 2, 3, 4, 5],  # Indices of mood-related questions
            "anxiety": [6, 7, 8, 9, 10],  # Indices of anxiety-related questions
            "stress": [11, 12, 13, 14, 15],  # Indices of stress-related questions
            "functioning": [16, 17, 18, 19, 20]  # Indices of functioning-related questions
        }
        
        # Questions where higher value = WORSE wellness (need reverse scoring).
        # Formula: reversed = (MAX_SCALE + 1) - raw_value  →  5→1, 4→2, 3→3, 2→4, 1→5
        # These are all "negatively worded" questions where answering "Almost Always" / "Extreme"
        # indicates poor mental health, not good health.
        self.REVERSE_SCORED_QUESTIONS = {
            # Section A – Mood (negative questions)
            'a4',  # How frequently do you feel emotionally exhausted, numb, or detached?
            'a5',  # How often do you notice sudden or significant changes in your mood?
            # Section B – Anxiety (ALL negative)
            'b1',  # How often do you worry excessively?
            'b2',  # How frequently do you find it difficult to slow down your thoughts?
            'b3',  # How often do you experience feelings of anxiety without an obvious trigger?
            'b4',  # How often do you dwell on past events or anticipate future outcomes?
            'b5',  # How frequently do you feel mentally tense, uneasy, or on edge?
            # Section C – Stress (mixed)
            'c1',  # How much pressure do you feel from expectations? (Extreme pressure = bad)
            'c2',  # How often do you feel overwhelmed by daily responsibilities?
            'c4',  # How often do you feel mentally exhausted by end of day?
            'c5',  # How often do minor setbacks feel more distressing than expected?
            # Section D – Focus/Motivation (negative questions)
            'd2',  # How often do you experience difficulty maintaining focus?
            'd3',  # How frequently do you delay or avoid important tasks?
            'd5',  # How often have you noticed a loss of interest in activities you previously liked?
            # Section E – Sleep (mixed)
            'e2',  # How frequently do you feel tired or low in energy even after adequate sleep?
            'e3',  # How often does stress interfere with your sleep?
            'e4',  # How often do you experience physical symptoms during stress?
            # Section F – Social (mixed)
            'f3',  # How often do you feel lonely or emotionally isolated?
            'f5',  # To what extent do you feel your mental well-being requires attention or improvement?
        }
        
        self.MAX_SCALE = 5  # Options go from 1 to 5
    
    def calculate_score(self, responses: Union[Dict[str, Any], List[int]]) -> Dict[str, Any]:
        """
        Calculate total score and risk level from questionnaire responses.
        
        Args:
            responses: Dictionary of response name-value pairs from the questionnaire
            
        Returns:
            Dictionary containing score results and risk level
        """
        # Handle both dict and list inputs
        if isinstance(responses, dict):
            # Filter out empty/non-numeric responses, apply reverse scoring where needed
            numeric_values = []
            for key, value in responses.items():
                # Skip reflection section questions
                if key in ['g1', 'g2', 'g3']:
                    continue
                try:
                    raw = int(value)
                    # Reverse-score negatively-worded questions so that
                    # "Almost Always" on a bad question scores LOW (good = high score system).
                    if key in self.REVERSE_SCORED_QUESTIONS:
                        raw = (self.MAX_SCALE + 1) - raw  # 5→1, 4→2, 3→3, 2→4, 1→5
                    numeric_values.append(raw)
                except (ValueError, TypeError):
                    pass
        else:
            # If it's a list, convert values to int (no key info → can't reverse score)
            numeric_values = []
            for value in responses:
                try:
                    numeric_values.append(int(value))
                except (ValueError, TypeError):
                    pass
        
        # Validate responses
        if not numeric_values:
            return {
                "score": 0,
                "risk_level": "Low Risk",
                "breakdown": {},
                "message": "No valid responses provided"
            }
        
        # Calculate total score
        total_score = sum(numeric_values)
        
        # Normalize to 0-100 scale
        # Each question: min=1, max=5. With N questions: raw range = [N, N*5]
        # Normalize: (raw - N) / (N*4) * 100
        n = len(numeric_values)
        if n > 0:
            normalized_score = round((total_score - n) / (n * 4) * 100)
            normalized_score = max(0, min(100, normalized_score))
        else:
            normalized_score = 0
        
        # Determine risk level based on normalized score
        risk_level = self._determine_risk_level(normalized_score)
        
        # Generate breakdown by section
        breakdown = self._calculate_section_breakdown(responses)
        
        # Generate message
        message = f"Calculated score of {normalized_score}/100 from {len(numeric_values)} responses (raw: {total_score})"
        
        return {
            "score": normalized_score,
            "raw_score": total_score,
            "risk_level": risk_level,
            "breakdown": breakdown,
            "message": message,
            "response_count": len(numeric_values)
        }
    
    def _determine_risk_level(self, score: int) -> str:
        """
        Determine risk level based on total score.
        Higher scores = BETTER wellness (not higher risk)
        
        Args:
            score: Total questionnaire score (0-100)
            
        Returns:
            Risk level category
        """
        if score >= 80:
            return "Excellent"      # 80-100
        elif score >= 60:
            return "Good"           # 60-79
        elif score >= 40:
            return "Moderate"       # 40-59
        elif score >= 20:
            return "Concerning"     # 20-39
        else:
            return "Critical"       # 0-19
    
    def _calculate_subscale_scores(self, responses: Union[Dict[str, Any], List[int]]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate scores for each subscale.
        
        Args:
            responses: Dictionary of response name-value pairs
            
        Returns:
            Dictionary of subscale scores and risk levels
        """
        subscale_scores = {}
        
        for subscale, indices in self.subscale_mappings.items():
            subscale_responses = []
            # This mapping is based on indices, skip it for now
            
        return subscale_scores
    
    def _calculate_section_breakdown(self, responses: Union[Dict[str, Any], List[int]]) -> Dict[str, Any]:
        """
        Calculate score breakdown by assessment section.
        Args:
            responses: Dictionary of response name-value pairs
            
        Returns:
            Dictionary of section breakdowns
        """
        breakdown = {
            "a": {"name": "Mood & Emotional Health", "score": 0, "count": 0},
            "b": {"name": "Anxiety & Thought Patterns", "score": 0, "count": 0},
            "c": {"name": "Stress & Pressure Handling", "score": 0, "count": 0},
            "d": {"name": "Motivation, Focus & Productivity", "score": 0, "count": 0},
            "e": {"name": "Sleep & Physical Signals", "score": 0, "count": 0},
            "f": {"name": "Social Connection & Self-Worth", "score": 0, "count": 0}
        }
        
        # Parse responses by section
        for key, value in responses.items():
            if key in ['g1', 'g2', 'g3']:
                continue
            
            try:
                numeric_value = int(value)
                # Apply reverse scoring for negatively-worded questions
                if key in self.REVERSE_SCORED_QUESTIONS:
                    numeric_value = (self.MAX_SCALE + 1) - numeric_value
                section = key[0].lower()  # Get first character (a, b, c, etc.)
                
                if section in breakdown:
                    breakdown[section]["score"] += numeric_value
                    breakdown[section]["count"] += 1
            except (ValueError, TypeError, IndexError):
                continue
        
        # Calculate averages
        for section in breakdown:
            if breakdown[section]["count"] > 0:
                breakdown[section]["average"] = breakdown[section]["score"] / breakdown[section]["count"]
            else:
                breakdown[section]["average"] = 0
        
        return breakdown
    
    def get_score_explanation(self, score: int) -> str:
        """
        Get an explanation of what the score means.
        
        Args:
            score: Total questionnaire score (0-100)
            
        Returns:
            Explanation string
        """
        risk_level = self._determine_risk_level(score)
        
        if risk_level == "Excellent":
            return (
                f"Your score of {score} indicates excellent mental wellness. "
                "You're managing very well and maintaining strong mental health habits. "
                "Continue with your current practices."
            )
        elif risk_level == "Good":
            return (
                f"Your score of {score} indicates good mental wellness. "
                "You're coping well with life's challenges. "
                "Keep up your positive mental health practices."
            )
        elif risk_level == "Moderate":
            return (
                f"Your score of {score} indicates moderate mental wellness. "
                "You're experiencing some challenges that could benefit from attention and self-care strategies. "
                "Consider implementing wellness activities."
            )
        elif risk_level == "Concerning":
            return (
                f"Your score of {score} indicates concerning mental wellness. "
                "You may be experiencing significant difficulties that would benefit from support. "
                "Consider reaching out to a counselor or mental health professional."
            )
        else:  # Critical
            return (
                f"Your score of {score} indicates critical mental wellness concerns. "
                "You are experiencing significant challenges that require professional support. "
                "Please reach out to a mental health professional or crisis line immediately."
            )
    
    def calculate_combined_risk_score(
        self,
        questionnaire_score: Union[int, float],
        emotion_nlp_score: Union[int, float],
        questionnaire_weight: float = 0.6,
        emotion_weight: float = 0.4
    ) -> Dict[str, Any]:
        """
        Calculate combined risk score from questionnaire and NLP emotion analysis.
        
        Formula: Final Risk Score = (Questionnaire Score * 0.6) + (NLP Emotion Score * 0.4)
        
        Args:
            questionnaire_score: Score from questionnaire responses (0-100 scale recommended)
            emotion_nlp_score: Score from NLP emotion analysis (0-100 scale)
            questionnaire_weight: Weight for questionnaire component (default: 0.6 = 60%)
            emotion_weight: Weight for emotion component (default: 0.4 = 40%)
            
        Returns:
            Dictionary containing combined score, normalized score, risk level, and breakdown
        """
        try:
            # Normalize inputs to 0-100 scale
            q_score = max(0, min(100, float(questionnaire_score)))
            e_score = max(0, min(100, float(emotion_nlp_score)))
            
            # Validate weights sum to 1.0
            total_weight = questionnaire_weight + emotion_weight
            if total_weight == 0:
                return {
                    "combined_score": 0,
                    "normalized_score": 0,
                    "risk_level": "Low Risk",
                    "message": "Invalid weights provided",
                    "breakdown": {
                        "questionnaire_score": q_score,
                        "emotion_score": e_score,
                        "questionnaire_contribution": 0,
                        "emotion_contribution": 0
                    }
                }
            
            # Calculate weighted contributions
            q_contribution = (q_score * questionnaire_weight)
            e_contribution = (e_score * emotion_weight)
            
            # Calculate combined score
            combined_score = q_contribution + e_contribution
            
            # Normalize to 0-100 if weights don't sum to 1.0
            normalized_score = combined_score / total_weight if total_weight != 0 else combined_score
            
            # Determine risk level based on combined score using wellness scale
            risk_level = self._determine_risk_level(int(normalized_score))
            
            return {
                "combined_score": round(normalized_score, 2),
                "normalized_score": round(normalized_score, 2),
                "risk_level": risk_level,
                "message": f"Combined analysis: {risk_level} (Score: {round(normalized_score, 2)})",
                "breakdown": {
                    "questionnaire_score": round(q_score, 2),
                    "emotion_score": round(e_score, 2),
                    "questionnaire_contribution": round(q_contribution, 2),
                    "emotion_contribution": round(e_contribution, 2),
                    "questionnaire_weight": round(questionnaire_weight, 2),
                    "emotion_weight": round(emotion_weight, 2)
                }
            }
            
        except (ValueError, TypeError) as e:
            return {
                "combined_score": 0,
                "normalized_score": 0,
                "risk_level": "Error",
                "message": f"Error calculating combined score: {str(e)}",
                "breakdown": {}
            }