import spacy
import re
from typing import Dict, List, Tuple, Optional
from app.core.config import settings


class TranscriptProcessor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy model not found. Using basic processing.")
            self.nlp = None
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from transcript"""
        entities = {
            "people": [],
            "organizations": [],
            "money": [],
            "dates": [],
            "competitors": []
        }
        
        if not self.nlp:
            return self._basic_entity_extraction(text)
        
        doc = self.nlp(text)
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                entities["people"].append(ent.text)
            elif ent.label_ == "ORG":
                entities["organizations"].append(ent.text)
            elif ent.label_ == "MONEY":
                entities["money"].append(ent.text)
            elif ent.label_ == "DATE":
                entities["dates"].append(ent.text)
        
        # Extract competitors (common competitor names)
        competitor_keywords = ["salesforce", "hubspot", "zoho", "pipedrive", "freshworks"]
        text_lower = text.lower()
        for competitor in competitor_keywords:
            if competitor in text_lower:
                entities["competitors"].append(competitor.title())
        
        return entities
    
    def _basic_entity_extraction(self, text: str) -> Dict[str, List[str]]:
        """Fallback basic entity extraction without spaCy"""
        entities = {
            "people": [],
            "organizations": [],
            "money": [],
            "dates": [],
            "competitors": []
        }
        
        # Money patterns
        money_pattern = r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|k|k\s*USD)'
        entities["money"] = re.findall(money_pattern, text, re.IGNORECASE)
        
        # Date patterns
        date_pattern = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,\s*\d{4})?|\d{1,2}/\d{1,2}/\d{2,4}|\b(?:next|this)\s+(?:week|month|quarter)\b'
        entities["dates"] = re.findall(date_pattern, text, re.IGNORECASE)
        
        # Competitors
        competitor_keywords = ["salesforce", "hubspot", "zoho", "pipedrive", "freshworks"]
        text_lower = text.lower()
        for competitor in competitor_keywords:
            if competitor in text_lower:
                entities["competitors"].append(competitor.title())
        
        return entities
    
    def calculate_talk_ratio(self, transcript: str) -> Dict[str, float]:
        """Calculate talk ratio between rep and prospect"""
        # Simple heuristic: look for speaker labels or patterns
        lines = transcript.split('\n')
        rep_words = 0
        prospect_words = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for speaker indicators
            speaker_match = re.match(r'^(Rep|Sales|Agent|Prospect|Customer|Client):?\s*(.+)$', line, re.IGNORECASE)
            if speaker_match:
                speaker = speaker_match.group(1).lower()
                content = speaker_match.group(2)
                word_count = len(content.split())
                
                if any(s in speaker for s in ['rep', 'sales', 'agent']):
                    rep_words += word_count
                else:
                    prospect_words += word_count
            else:
                # If no speaker labels, try to infer from context
                # This is a simplified approach - in production, you'd want proper speaker diarization
                prospect_words += len(line.split()) // 2  # Rough estimate
        
        total_words = rep_words + prospect_words
        if total_words == 0:
            return {"rep_percentage": 50.0, "prospect_percentage": 50.0, "total_words": 0}
        
        return {
            "rep_percentage": round((rep_words / total_words) * 100, 1),
            "prospect_percentage": round((prospect_words / total_words) * 100, 1),
            "total_words": total_words
        }
    
    def extract_key_topics(self, transcript: str) -> List[str]:
        """Extract key topics discussed in the call"""
        # Common sales call topics
        topic_keywords = {
            "pricing": ["price", "cost", "pricing", "budget", "investment", "fee"],
            "features": ["feature", "functionality", "capability", "what can it do"],
            "implementation": ["implementation", "setup", "onboarding", "integration"],
            "timeline": ["timeline", "when", "start", "launch", "deadline"],
            "support": ["support", "help", "training", "customer service"],
            "competition": ["competitor", "alternative", "comparison", "other options"],
            "decision": ["decision", "approve", "buy", "purchase", "sign"],
            "technical": ["technical", "api", "integration", "security", "data"]
        }
        
        text_lower = transcript.lower()
        identified_topics = []
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                identified_topics.append(topic)
        
        return identified_topics
    
    def detect_sentiment_timeline(self, transcript: str) -> List[Dict]:
        """Generate a basic sentiment timeline"""
        # Simplified sentiment analysis based on keyword sentiment
        positive_words = ["great", "excellent", "perfect", "love", "interested", "yes", "definitely", "absolutely"]
        negative_words = ["concern", "issue", "problem", "expensive", "difficult", "no", "don't", "won't"]
        
        lines = transcript.split('\n')
        timeline = []
        total_lines = len(lines)
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            
            # Calculate position in call (0-1)
            position = i / total_lines if total_lines > 0 else 0
            
            line_lower = line.lower()
            positive_count = sum(1 for word in positive_words if word in line_lower)
            negative_count = sum(1 for word in negative_words if word in line_lower)
            
            # Simple sentiment score
            if positive_count > negative_count:
                sentiment = 0.5
            elif negative_count > positive_count:
                sentiment = -0.5
            else:
                sentiment = 0.0
            
            # Engagement based on line length
            engagement = min(len(line.split()) / 20, 1.0)  # Normalize to 0-1
            
            timeline.append({
                "timestamp": position,
                "sentiment_score": sentiment,
                "engagement_level": engagement
            })
        
        return timeline


transcript_processor = TranscriptProcessor()
