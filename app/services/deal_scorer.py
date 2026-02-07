from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ScoringFactor:
    name: str
    weight: float
    description: str


class DealScorer:
    def __init__(self):
        self.scoring_factors = [
            ScoringFactor("positive_sentiment", 0.25, "Positive sentiment and engagement"),
            ScoringFactor("buyer_engagement", 0.20, "Prospect talk ratio and participation"),
            ScoringFactor("objection_resolution", 0.20, "How well objections were handled"),
            ScoringFactor("clear_next_steps", 0.15, "Defined actions and timeline"),
            ScoringFactor("budget_timeline", 0.15, "Budget confirmation and timeline urgency"),
            ScoringFactor("decision_maker", 0.05, "Decision maker involvement")
        ]
    
    def calculate_deal_score(self, analysis_data: Dict) -> Dict:
        """Calculate comprehensive deal health score (0-100)"""
        factor_scores = {}
        
        # Calculate each factor score
        factor_scores["positive_sentiment"] = self._score_sentiment(analysis_data)
        factor_scores["buyer_engagement"] = self._score_engagement(analysis_data)
        factor_scores["objection_resolution"] = self._score_objection_resolution(analysis_data)
        factor_scores["clear_next_steps"] = self._score_next_steps(analysis_data)
        factor_scores["budget_timeline"] = self._score_budget_timeline(analysis_data)
        factor_scores["decision_maker"] = self._score_decision_maker(analysis_data)
        
        # Calculate weighted total score
        total_score = 0.0
        for factor in self.scoring_factors:
            factor_score = factor_scores.get(factor.name, 0)
            weighted_score = factor_score * factor.weight
            total_score += weighted_score
        
        # Ensure score is within 0-100 range
        total_score = max(0, min(100, total_score))
        
        # Determine risk level
        risk_level = self._determine_risk_level(total_score)
        
        # Generate scoring insights
        insights = self._generate_scoring_insights(factor_scores, total_score)
        
        return {
            "deal_score": round(total_score, 1),
            "risk_level": risk_level,
            "factor_scores": factor_scores,
            "insights": insights,
            "recommendations": self._generate_recommendations(factor_scores, total_score)
        }
    
    def _score_sentiment(self, analysis_data: Dict) -> float:
        """Score positive sentiment (0-100)"""
        sentiment_timeline = analysis_data.get("sentiment_timeline", [])
        
        if not sentiment_timeline:
            return 50.0  # Neutral default
        
        # Calculate average sentiment
        total_sentiment = sum(point.get("sentiment_score", 0) for point in sentiment_timeline)
        avg_sentiment = total_sentiment / len(sentiment_timeline)
        
        # Convert from -1 to 1 scale to 0-100 scale
        # -1 = 0, 0 = 50, 1 = 100
        score = (avg_sentiment + 1) * 50
        
        # Bonus for consistent positive sentiment
        positive_points = [p for p in sentiment_timeline if p.get("sentiment_score", 0) > 0.3]
        if len(positive_points) / len(sentiment_timeline) > 0.7:
            score = min(100, score + 10)
        
        return score
    
    def _score_engagement(self, analysis_data: Dict) -> float:
        """Score buyer engagement based on talk ratio (0-100)"""
        talk_ratio = analysis_data.get("talk_ratio", {})
        prospect_percentage = talk_ratio.get("prospect_percentage", 50)
        
        # Ideal prospect talk ratio is 40-60%
        if 40 <= prospect_percentage <= 60:
            base_score = 100
        elif 30 <= prospect_percentage < 40 or 60 < prospect_percentage <= 70:
            base_score = 80
        elif 20 <= prospect_percentage < 30 or 70 < prospect_percentage <= 80:
            base_score = 60
        else:
            base_score = 40
        
        # Consider engagement levels from sentiment timeline
        sentiment_timeline = analysis_data.get("sentiment_timeline", [])
        if sentiment_timeline:
            avg_engagement = sum(p.get("engagement_level", 0) for p in sentiment_timeline) / len(sentiment_timeline)
            engagement_bonus = avg_engagement * 20  # Max 20 point bonus
            base_score = min(100, base_score + engagement_bonus)
        
        return base_score
    
    def _score_objection_resolution(self, analysis_data: Dict) -> float:
        """Score objection handling (0-100)"""
        objections = analysis_data.get("detected_objections", [])
        
        if not objections:
            return 85.0  # No objections is generally good
        
        # Base score decreases with more objections
        base_score = max(40, 100 - (len(objections) * 10))
        
        # Bonus if objections have recommended responses (indicating they were addressed)
        addressed_objections = [obj for obj in objections if obj.get("recommended_response")]
        if addressed_objections:
            resolution_rate = len(addressed_objections) / len(objections)
            resolution_bonus = resolution_rate * 30
            base_score = min(100, base_score + resolution_bonus)
        
        # Penalty for late-stage objections
        timestamps = [obj.get("timestamp", 0) for obj in objections]
        if timestamps and max(timestamps) > 0.8:
            base_score -= 15
        
        return max(0, base_score)
    
    def _score_next_steps(self, analysis_data: Dict) -> float:
        """Score clarity of next steps (0-100)"""
        next_actions = analysis_data.get("next_best_actions", [])
        
        if not next_actions:
            return 20.0  # Poor - no next steps
        
        # Score based on quantity and quality
        base_score = min(100, len(next_actions) * 20)
        
        # Bonus for specific, actionable items
        specific_actions = [action for action in next_actions 
                          if action.get("priority") and action.get("action")]
        if specific_actions:
            specificity_bonus = (len(specific_actions) / len(next_actions)) * 20
            base_score = min(100, base_score + specificity_bonus)
        
        return base_score
    
    def _score_budget_timeline(self, analysis_data: Dict) -> float:
        """Score budget and timeline confirmation (0-100)"""
        budget_mentions = analysis_data.get("budget_mentions", [])
        timeline_urgency = analysis_data.get("timeline_urgency", [])
        
        score = 0
        
        # Budget scoring
        if budget_mentions:
            budget_score = 50
            # Bonus for specific amounts
            if any("$" in mention or "k" in mention.lower() for mention in budget_mentions):
                budget_score = 75
            # Bonus for budget confirmation
            if any(word in " ".join(budget_mentions).lower() for word in ["approved", "confirmed", "available"]):
                budget_score = 100
            score += budget_score * 0.5
        
        # Timeline scoring
        if timeline_urgency:
            timeline_score = 50
            # Bonus for specific dates
            if any(mention.isdigit() for mention in timeline_urgency):
                timeline_score = 75
            # Bonus for urgency indicators
            if any(word in " ".join(timeline_urgency).lower() for word in ["urgent", "asap", "immediately", "this week"]):
                timeline_score = 100
            score += timeline_score * 0.5
        
        return score
    
    def _score_decision_maker(self, analysis_data: Dict) -> float:
        """Score decision maker involvement (0-100)"""
        decision_makers = analysis_data.get("decision_makers_identified", [])
        
        if not decision_makers:
            return 30.0  # Poor - no decision makers identified
        
        # Base score for identifying decision makers
        base_score = min(100, len(decision_makers) * 30)
        
        # Bonus for explicit decision maker confirmation
        entities = analysis_data.get("entities", {})
        if entities and len(decision_makers) > 0:
            base_score = min(100, base_score + 20)
        
        return base_score
    
    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level based on deal score"""
        if score >= 80:
            return "low"
        elif score >= 60:
            return "medium"
        elif score >= 40:
            return "high"
        else:
            return "critical"
    
    def _generate_scoring_insights(self, factor_scores: Dict, total_score: float) -> List[str]:
        """Generate insights based on scoring factors"""
        insights = []
        
        # Find strongest and weakest factors
        strongest_factor = max(factor_scores.items(), key=lambda x: x[1])
        weakest_factor = min(factor_scores.items(), key=lambda x: x[1])
        
        insights.append(f"Strongest area: {strongest_factor[0].replace('_', ' ').title()} ({strongest_factor[1]:.1f}/100)")
        
        if weakest_factor[1] < 60:
            insights.append(f"Needs improvement: {weakest_factor[0].replace('_', ' ').title()} ({weakest_factor[1]:.1f}/100)")
        
        # Overall assessment
        if total_score >= 80:
            insights.append("Excellent deal health - high probability of closing")
        elif total_score >= 60:
            insights.append("Good deal health - positive indicators with some areas to address")
        elif total_score >= 40:
            insights.append("Moderate deal health - requires attention and follow-up")
        else:
            insights.append("Low deal health - significant risks and obstacles identified")
        
        return insights
    
    def _generate_recommendations(self, factor_scores: Dict, total_score: float) -> List[str]:
        """Generate actionable recommendations based on scoring"""
        recommendations = []
        
        # Specific recommendations based on weak areas
        if factor_scores.get("positive_sentiment", 0) < 60:
            recommendations.append("Focus on building rapport and addressing concerns to improve sentiment")
        
        if factor_scores.get("buyer_engagement", 0) < 60:
            recommendations.append("Increase prospect engagement with more questions and active listening")
        
        if factor_scores.get("objection_resolution", 0) < 60:
            recommendations.append("Develop better objection handling strategies and responses")
        
        if factor_scores.get("clear_next_steps", 0) < 60:
            recommendations.append("Always end calls with clear, specific next steps and timelines")
        
        if factor_scores.get("budget_timeline", 0) < 60:
            recommendations.append("Qualify budget and timeline early in the sales process")
        
        if factor_scores.get("decision_maker", 0) < 60:
            recommendations.append("Identify and engage all key decision makers")
        
        # Overall recommendations based on total score
        if total_score < 40:
            recommendations.append("Consider if this deal is worth pursuing - major red flags present")
        
        return recommendations


deal_scorer = DealScorer()
