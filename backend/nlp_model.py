"""
MindCare NLP Model

This module encapsulates all NLP-based inference for the MindCare system.
It processes open-ended text responses to predict mental states using ML techniques.
"""

import os
import pickle
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from typing import Dict, List, Tuple, Any
from transformers import pipeline as hf_pipeline, AutoTokenizer, AutoModelForSequenceClassification
from huggingface_hub import login
import logging
import torch

logger = logging.getLogger(__name__)

class NLPAnalyzer:
    """
    NLP-based mental state analyzer.
    
    This class handles text processing, feature extraction, and mental state prediction
    using both local ML models and Hugging Face transformers for enhanced analysis.
    """
    
    def __init__(self, model_path=None, hf_token=None, hf_model=None, use_huggingface=True):
        """
        Initialize the NLP analyzer.
        
        Args:
            model_path: Path to the trained model directory
            hf_token: Hugging Face API token
            hf_model: Hugging Face model identifier
            use_huggingface: Whether to use Hugging Face models (default: True)
        """
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), 'models')
        self.model = None
        self.confidence_threshold = 0.65  # Minimum confidence to trust predictions
        
        # Mental state categories
        self.categories = ["Normal", "Anxiety", "Depression", "High Stress"]
        
        # Emotion model configuration
        self.emotion_model_name = "j-hartmann/emotion-english-distilroberta-base"
        self.emotion_tokenizer = None
        self.emotion_model = None
        self.emotion_labels = ["sadness", "joy", "love", "anger", "fear", "surprise"]
        
        # Hugging Face configuration
        self.use_huggingface = use_huggingface
        self.hf_token = hf_token
        self.hf_model_name = hf_model or "facebook/bart-large-mnli"
        self.hf_classifier = None
        
        # Initialize Hugging Face if token provided
        if self.use_huggingface and self.hf_token:
            self._initialize_huggingface()
        elif self.use_huggingface and not self.hf_token:
            logger.warning("Hugging Face token not provided. Using local model only. To enable HF, set HUGGINGFACE_TOKEN environment variable.")
            self.use_huggingface = False
        
        # Load emotion analysis model
        self._load_emotion_model()
        
        # Load or create local model
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """
        Load a pre-trained model or create a new one if none exists.
        """
        model_file = os.path.join(self.model_path, 'mental_state_model.pkl')
        
        try:
            # Try to load a pre-trained model
            with open(model_file, 'rb') as f:
                self.model = pickle.load(f)
            logger.info("Loaded pre-trained NLP model")
        except (FileNotFoundError, EOFError):
            # If no model exists, create a mock one for demonstration
            logger.info("No pre-trained model found. Creating demo model...")
            self._create_demo_model()
            
            # Ensure model directory exists
            os.makedirs(self.model_path, exist_ok=True)
            
            # Save the model for future use
            with open(model_file, 'wb') as f:
                pickle.dump(self.model, f)
            logger.info(f"Saved demo model to {model_file}")
    
    def _initialize_huggingface(self):
        """
        Initialize Hugging Face API and models for advanced NLP analysis.
        """
        try:
            # Authenticate with Hugging Face
            login(token=self.hf_token)
            logger.info("Authenticated with Hugging Face")
            
            # Initialize zero-shot classification pipeline
            self.hf_classifier = hf_pipeline(
                "zero-shot-classification",
                model=self.hf_model_name,
                use_auth_token=self.hf_token
            )
            logger.info(f"Loaded Hugging Face model: {self.hf_model_name}")
            self.use_huggingface = True
        except Exception as e:
            logger.error(f"Failed to initialize Hugging Face: {str(e)}")
            logger.info("Falling back to local model only")
            self.use_huggingface = False
    
    def _load_emotion_model(self):
        """
        Load the emotion analysis model from Hugging Face.
        Uses the distilroberta-base model fine-tuned for emotion classification.
        """
        try:
            logger.info(f"Loading emotion model: {self.emotion_model_name}")
            self.emotion_tokenizer = AutoTokenizer.from_pretrained(self.emotion_model_name)
            self.emotion_model = AutoModelForSequenceClassification.from_pretrained(self.emotion_model_name)
            logger.info("Emotion analysis model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load emotion model: {str(e)}")
            logger.warning("Emotion analysis will be unavailable")
            self.emotion_model = None
            self.emotion_tokenizer = None
    
    def _create_demo_model(self):
        """
        Create a demonstration model with mock training data.
        In production, this would be replaced with proper training on real labeled data.
        """
        # Create a pipeline with TF-IDF vectorizer and Logistic Regression
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=1000, 
                stop_words='english',
                ngram_range=(1, 2),  # Include bigrams
                min_df=2,  # Ignore terms that appear in less than 2 documents
                max_df=0.8  # Ignore terms that appear in more than 80% of documents
            )),
            ('classifier', LogisticRegression(
                random_state=42,
                max_iter=1000,
                C=1.0  # Regularization strength
            ))
        ])
        
        # Mock training data (in production, use real labeled data)
        mock_texts = [
            # Normal
            "I'm feeling great and energetic today",
            "Life is good and I'm enjoying my work",
            "I feel positive about the future",
            "I'm happy with my relationships",
            
            # Anxiety
            "I've been worrying about everything lately",
            "Sometimes I feel restless and can't relax",
            "I'm anxious about upcoming exams",
            "My heart races when I think about the future",
            
            # Depression
            "I feel sad most days and can't sleep",
            "Nothing seems enjoyable anymore",
            "I feel hopeless and don't see a way out",
            "I've lost interest in activities I used to love",
            
            # High Stress
            "Work pressure is overwhelming me",
            "I'm stressed about my financial situation",
            "I feel like I'm drowning in responsibilities",
            "I can't handle all these deadlines"
        ]
        
        mock_labels = [
            # Normal
            "Normal", "Normal", "Normal", "Normal",
            # Anxiety
            "Anxiety", "Anxiety", "Anxiety", "Anxiety",
            # Depression
            "Depression", "Depression", "Depression", "Depression",
            # High Stress
            "High Stress", "High Stress", "High Stress", "High Stress"
        ]
        
        # Train the model
        self.model.fit(mock_texts, mock_labels)
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for analysis.
        
        Args:
            text: Raw text input
            
        Returns:
            Preprocessed text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def analyze_text_huggingface(self, text_responses: List[str]) -> Dict[str, Any]:
        """
        Analyze text using Hugging Face zero-shot classification.
        
        Args:
            text_responses: List of text responses to open-ended questions
            
        Returns:
            Dictionary containing HF prediction results
        """
        if not self.hf_classifier:
            logger.warning("Hugging Face classifier not initialized")
            return None
        
        try:
            # Combine all responses
            combined_text = " ".join(text_responses)
            
            if not combined_text.strip():
                return None
            
            # Limit text length for efficiency (HF models have token limits)
            if len(combined_text) > 512:
                combined_text = combined_text[:512]
            
            # Perform zero-shot classification
            result = self.hf_classifier(
                combined_text,
                self.categories,
                multi_class=False
            )
            
            # Build probability dictionary
            category_probabilities = {}
            for label, score in zip(result['labels'], result['scores']):
                category_probabilities[label] = float(score)
            
            # Get top prediction and confidence
            top_prediction = result['labels'][0]
            confidence = result['scores'][0]
            
            return {
                "prediction": top_prediction,
                "confidence": float(confidence),
                "probabilities": category_probabilities,
                "message": f"HF Analysis: {len(text_responses)} response(s)",
                "model": "Hugging Face Zero-Shot Classification"
            }
        except Exception as e:
            logger.error(f"Hugging Face analysis failed: {str(e)}")
            return None
    
    def analyze_text(self, text_responses: List[str]) -> Dict[str, Any]:
        """
        Analyze text responses to predict mental state.
        
        Tries Hugging Face first if available, falls back to local model.
        
        Args:
            text_responses: List of text responses to open-ended questions
            
        Returns:
            Dictionary containing prediction results
        """
        # Handle empty responses
        if not text_responses or all(not response.strip() for response in text_responses):
            return {
                "prediction": "Normal",
                "confidence": 0.0,
                "probabilities": {category: 0.25 for category in self.categories},
                "message": "No text provided for analysis"
            }
        
        # Try Hugging Face analysis first if available
        if self.use_huggingface and self.hf_classifier:
            logger.info("Using Hugging Face model for analysis")
            hf_result = self.analyze_text_huggingface(text_responses)
            if hf_result:
                return hf_result
            else:
                logger.info("Hugging Face analysis failed, falling back to local model")
        
        # Fall back to local model
        logger.info("Using local scikit-learn model for analysis")
        
        # Combine all responses into a single text for analysis
        combined_text = " ".join(text_responses)
        
        # Preprocess text
        preprocessed_text = self._preprocess_text(combined_text)
        
        # Use the model to predict mental state
        prediction = self.model.predict([preprocessed_text])[0]
        
        # Get prediction probabilities
        probabilities = self.model.predict_proba([preprocessed_text])[0]
        
        # Create a dictionary of category probabilities
        category_probabilities = {
            category: prob for category, prob in zip(self.categories, probabilities)
        }
        
        # Get confidence score (probability of the predicted class)
        confidence = max(probabilities)
        
        # If confidence is below threshold, mark as uncertain
        if confidence < self.confidence_threshold:
            prediction = "Uncertain"
        
        return {
            "prediction": prediction,
            "confidence": float(confidence),
            "probabilities": category_probabilities,
            "message": f"Local Model: Analyzed {len(text_responses)} response(s)",
            "model": "Scikit-learn Local Model"
        }
    
    def analyze_emotions(self, text_responses: List[str]) -> Dict[str, Any]:
        """
        Analyze emotions in text responses using the emotion analysis model.
        
        Args:
            text_responses: List of text responses to analyze
            
        Returns:
            Dictionary containing emotion scores and analysis
        """
        if not self.emotion_model or not self.emotion_tokenizer:
            logger.warning("Emotion model not loaded")
            return {
                "emotion_scores": {},
                "dominant_emotion": "neutral",
                "emotion_score": 0.5,
                "message": "Emotion model not available"
            }
        
        try:
            # Handle empty responses
            if not text_responses or all(not response.strip() for response in text_responses):
                return {
                    "emotion_scores": {emotion: 0.0 for emotion in self.emotion_labels},
                    "dominant_emotion": "neutral",
                    "emotion_score": 0.5,
                    "message": "No text provided for emotion analysis"
                }
            
            # Combine all responses
            combined_text = " ".join(text_responses)
            
            # Limit text length for model efficiency
            if len(combined_text) > 512:
                combined_text = combined_text[:512]
            
            # Tokenize and get model predictions
            inputs = self.emotion_tokenizer(
                combined_text,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )
            
            with torch.no_grad():
                outputs = self.emotion_model(**inputs)
            
            # Get probabilities
            probabilities = torch.softmax(outputs.logits, dim=-1)[0].cpu().numpy()
            
            # Create emotion scores dictionary
            emotion_scores = {
                emotion: float(prob) for emotion, prob in zip(self.emotion_labels, probabilities)
            }
            
            # Get dominant emotion
            dominant_idx = np.argmax(probabilities)
            dominant_emotion = self.emotion_labels[dominant_idx]
            dominant_emotion_score = float(probabilities[dominant_idx])
            
            # Convert emotion to risk score (0-100)
            # Negative emotions (sadness, anger, fear) increase risk
            # Positive emotions (joy, love, surprise) decrease risk
            emotion_risk_score = self._emotion_to_risk_score(emotion_scores)
            
            return {
                "emotion_scores": emotion_scores,
                "dominant_emotion": dominant_emotion,
                "dominant_emotion_confidence": dominant_emotion_score,
                "emotion_score": emotion_risk_score,
                "message": f"Emotion analysis: {dominant_emotion} ({dominant_emotion_score:.2%})",
                "model": "DistilRoBERTa Emotion Classifier"
            }
            
        except Exception as e:
            logger.error(f"Emotion analysis failed: {str(e)}")
            return {
                "emotion_scores": {},
                "dominant_emotion": "error",
                "emotion_score": 0.5,
                "message": f"Emotion analysis error: {str(e)}"
            }
    
    def _emotion_to_risk_score(self, emotion_scores: Dict[str, float]) -> float:
        """
        Convert emotion scores to a mental health risk score (0-100).
        
        Risk-increasing emotions: sadness, anger, fear
        Risk-decreasing emotions: joy, love, surprise
        
        Args:
            emotion_scores: Dictionary of emotion labels to confidence scores
            
        Returns:
            Risk score between 0 and 100
        """
        # Weights for different emotions (impact on mental health risk)
        # Negative emotions increase risk, positive emotions decrease risk
        emotion_weights = {
            "sadness": 0.35,    # High risk indicator
            "anger": 0.25,      # Significant risk indicator
            "fear": 0.30,       # High risk indicator
            "joy": -0.30,       # Protective factor
            "love": -0.25,      # Protective factor
            "surprise": -0.10   # Slight protective factor
        }
        
        # Calculate weighted risk score
        risk_score = 50  # Neutral baseline (0-100 scale)
        
        for emotion, score in emotion_scores.items():
            weight = emotion_weights.get(emotion, 0)
            # Scale contribution: emotion_intensity * weight * 50
            # (50 is to scale the contribution to 0-100 range)
            risk_score += (score * weight * 50)
        
        # Clamp to 0-100 range
        risk_score = max(0, min(100, risk_score))
        
        return risk_score