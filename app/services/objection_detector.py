import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class ObjectionPattern:
    category: str
    keywords: List[str]
    recommended_response: str


class ObjectionDetector:
    def __init__(self):
        self.objection_patterns = [
            ObjectionPattern(
                category="price",
                keywords=["expensive", "too much", "cost", "price", "budget", "can't afford", "cheaper"],
                recommended_response="Focus on ROI and value proposition. Offer payment plans or show cost savings."
            ),
            ObjectionPattern(
                category="timing",
                keywords=["too busy", "not now", "later", "wrong time", "wait", "not ready", "next quarter"],
                recommended_response="Create urgency by highlighting current opportunities or risks of delay."
            ),
            ObjectionPattern(
                category="authority",
                keywords=["need to check", "my boss", "manager", "committee", "not my decision", "approval"],
                recommended_response="Identify decision makers and provide materials for internal selling."
            ),
            ObjectionPattern(
                category="need",
                keywords=["don't need", "not interested", "happy with", "working fine", "no problem"],
                recommended_response="Uncover pain points and demonstrate clear value proposition."
            ),
            ObjectionPattern(
                category="competition",
                keywords=["competitor", "alternative", "other option", "x company", "already using"],
                recommended_response="Differentiate on unique value and competitive advantages."
            ),
            ObjectionPattern(
                category="trust",
                keywords=["not sure", "uncertain", "risky", "guarantee", "proof", "evidence"],
                recommended_response="Provide case studies, testimonials, and risk-free trials."
            ),
            ObjectionPattern(
                category="implementation",
                keywords=["complicated", "difficult", "time consuming", "resources", "integration"],
                recommended_response="Simplify onboarding process and highlight support resources."
            )
        ]
    
    def detect_objections(self, transcript: str) -> List[Dict]:
        """Detect objections in transcript with timestamps and recommendations"""
        objections = []
        lines = transcript.split('\n')
        total_lines = len(lines)
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Calculate relative timestamp (0-1 representing call progress)
            timestamp = i / total_lines if total_lines > 0 else 0
            
            # Check each objection pattern
            for pattern in self.objection_patterns:
                if self._contains_objection(line, pattern.keywords):
                    objections.append({
                        "text": line,
                        "timestamp": timestamp,
                        "category": pattern.category,
                        "recommended_response": pattern.recommended_response
                    })
        
        return objections
    
    def _contains_objection(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains objection keywords"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def categorize_objection(self, objection_text: str) -> Tuple[str, str]:
        """Categorize a single objection and return recommendation"""
        objection_text_lower = objection_text.lower()
        
        for pattern in self.objection_patterns:
            if self._contains_objection(objection_text, pattern.keywords):
                return pattern.category, pattern.recommended_response
        
        return "other", "Listen carefully and address the specific concern raised."
    
    def get_objection_statistics(self, objections: List[Dict]) -> Dict:
        """Get statistics about detected objections"""
        if not objections:
            return {
                "total_objections": 0,
                "categories": {},
                "most_common": None,
                "objection_rate": 0.0
            }
        
        category_counts = {}
        for objection in objections:
            category = objection.get("category", "other")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        most_common = max(category_counts.items(), key=lambda x: x[1]) if category_counts else None
        
        return {
            "total_objections": len(objections),
            "categories": category_counts,
            "most_common": most_common[0] if most_common else None,
            "objection_rate": len(objections) / 10  # Assuming 10-minute call average
        }
    
    def generate_coaching_insights(self, objections: List[Dict]) -> List[str]:
        """Generate coaching insights based on objection patterns"""
        insights = []
        
        if not objections:
            return ["No objections detected - consider if you're adequately addressing concerns."]
        
        # Check for repeated objection types
        categories = [obj.get("category") for obj in objections]
        category_counts = {cat: categories.count(cat) for cat in set(categories)}
        
        for category, count in category_counts.items():
            if count >= 2:
                insights.append(f"Multiple {category} objections detected - consider addressing this proactively earlier in the call.")
        
        # Check for timing of objections
        timestamps = [obj.get("timestamp", 0) for obj in objections]
        if timestamps and max(timestamps) > 0.8:
            insights.append("Late-stage objections suggest need for better qualification early in the call.")
        
        # Check for unresolved objections
        unresolved_patterns = ["but", "however", "still", "even though"]
        for objection in objections:
            text = objection.get("text", "").lower()
            if any(pattern in text for pattern in unresolved_patterns):
                insights.append("Potential unresolved objection detected - ensure adequate response and confirmation.")
        
        return insights


objection_detector = ObjectionDetector()
