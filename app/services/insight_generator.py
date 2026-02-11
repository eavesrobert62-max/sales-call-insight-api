from typing import Dict, List, Optional
import time
from app.core.llm_client import llm_client
from app.services.transcript_processor import transcript_processor
from app.services.objection_detector import objection_detector
from app.services.intent_classifier import intent_classifier
from app.services.deal_scorer import deal_scorer


class InsightGenerator:
    def __init__(self):
        self.start_time = None
    
    def generate_comprehensive_analysis(self, transcript: str, metadata: Optional[Dict] = None) -> Dict:
        """Generate complete sales call analysis"""
        self.start_time = time.time()
        
        try:
            # Extract entities and basic transcript features
            entities = transcript_processor.extract_entities(transcript)
            talk_ratio = transcript_processor.calculate_talk_ratio(transcript)
            key_topics = transcript_processor.extract_key_topics(transcript)
            sentiment_timeline = transcript_processor.detect_sentiment_timeline(transcript)
            
            # Detect objections
            objections = objection_detector.detect_objections(transcript)
            
            # Classify intent
            intent_result = intent_classifier.classify_intent(transcript, talk_ratio)
            
            # Calculate deal score
            analysis_data = {
                "sentiment_timeline": sentiment_timeline,
                "talk_ratio": talk_ratio,
                "detected_objections": objections,
                "next_best_actions": [],  # Will be filled by LLM
                "budget_mentions": entities.get("money", []),
                "timeline_urgency": entities.get("dates", []),
                "decision_makers_identified": entities.get("people", []),
                "competitor_mentions": entities.get("competitors", []),
                "key_topics": key_topics,
                "entities": entities
            }
            
            deal_score_result = deal_scorer.calculate_deal_score(analysis_data)
            
            # Generate LLM-powered insights and next actions
            llm_analysis = llm_client.analyze_transcript(transcript, metadata)
            
            # Merge and structure all insights
            comprehensive_analysis = self._merge_analysis_results(
                analysis_data, intent_result, deal_score_result, llm_analysis, entities
            )
            
            # Add processing time
            processing_time = int((time.time() - self.start_time) * 1000)
            comprehensive_analysis["processing_time_ms"] = processing_time
            
            return comprehensive_analysis
            
        except Exception as e:
            processing_time = int((time.time() - self.start_time) * 1000) if self.start_time else 0
            return {
                "error": str(e),
                "processing_time_ms": processing_time,
                "deal_score": 0,
                "confidence_score": 0
            }
    
    def _merge_analysis_results(self, analysis_data: Dict, intent_result: Dict, 
                              deal_score_result: Dict, llm_analysis: Dict, entities: Dict) -> Dict:
        """Merge results from all analysis components"""
        
        # Extract and structure objections with coaching tips
        detected_objections = []
        for objection in analysis_data.get("detected_objections", []):
            objection_data = {
                "text": objection.get("text", ""),
                "timestamp": objection.get("timestamp"),
                "category": objection.get("category"),
                "recommended_response": objection.get("recommended_response")
            }
            detected_objections.append(objection_data)
        
        # Structure next actions
        next_actions = []
        if "next_best_actions" in llm_analysis:
            for i, action in enumerate(llm_analysis["next_best_actions"][:5]):  # Top 5 actions
                next_actions.append({
                    "action": action.get("action", str(action)),
                    "priority": i + 1,
                    "due_date": action.get("due_date"),
                    "owner": action.get("owner")
                })
        
        # Merge sentiment timeline
        sentiment_timeline = []
        for point in analysis_data.get("sentiment_timeline", []):
            sentiment_timeline.append({
                "timestamp": point.get("timestamp", 0),
                "sentiment_score": point.get("sentiment_score", 0),
                "engagement_level": point.get("engagement_level", 0)
            })
        
        # Structure talk ratio
        talk_ratio_data = analysis_data.get("talk_ratio", {})
        talk_ratio = {
            "rep_percentage": talk_ratio_data.get("rep_percentage", 50),
            "prospect_percentage": talk_ratio_data.get("prospect_percentage", 50),
            "total_words": talk_ratio_data.get("total_words", 0)
        }
        
        # Compile comprehensive analysis
        comprehensive_analysis = {
            "deal_score": deal_score_result.get("deal_score", 0),
            "risk_level": deal_score_result.get("risk_level", "unknown"),
            "intent_classification": intent_result.get("primary_intent", "unknown"),
            "intent_confidence": intent_result.get("confidence", 0),
            "detected_objections": detected_objections,
            "objection_count": len(detected_objections),
            "talk_ratio": talk_ratio,
            "sentiment_timeline": sentiment_timeline,
            "key_topics": analysis_data.get("key_topics", []),
            "decision_makers_identified": entities.get("people", []),
            "budget_mentions": entities.get("money", []),
            "timeline_urgency": entities.get("dates", []),
            "competitor_mentions": entities.get("competitors", []),
            "next_best_actions": next_actions,
            "confidence_score": min(intent_result.get("confidence", 0), 1.0),
            
            # Additional insights
            "scoring_factors": deal_score_result.get("factor_scores", {}),
            "scoring_insights": deal_score_result.get("insights", []),
            "recommendations": deal_score_result.get("recommendations", []),
            "intent_reasoning": intent_result.get("reasoning", ""),
            
            # Coaching moments
            "coachable_moments": self._identify_coachable_moments(
                detected_objections, sentiment_timeline, talk_ratio
            )
        }
        
        return comprehensive_analysis
    
    def _identify_coachable_moments(self, objections: List[Dict], 
                                   sentiment_timeline: List[Dict], 
                                   talk_ratio: Dict) -> List[Dict]:
        """Identify specific coaching moments from the call"""
        coaching_moments = []
        
        # Missed buying signals
        for i, point in enumerate(sentiment_timeline):
            if point.get("sentiment_score", 0) > 0.5 and point.get("engagement_level", 0) > 0.7:
                # High engagement and positive sentiment - potential buying signal
                coaching_moments.append({
                    "type": "missed_buying_signal",
                    "timestamp": point.get("timestamp", 0),
                    "description": "High engagement detected - consider asking for commitment",
                    "severity": "medium"
                })
        
        # Poor objection handling
        for objection in objections:
            if objection.get("timestamp", 0) > 0.7:  # Late-stage objection
                coaching_moments.append({
                    "type": "late_objection",
                    "timestamp": objection.get("timestamp", 0),
                    "description": f"Late-stage {objection.get('category', 'objection')} detected",
                    "severity": "high",
                    "suggestion": objection.get("recommended_response", "")
                })
        
        # Talk ratio issues
        prospect_talk = talk_ratio.get("prospect_percentage", 50)
        if prospect_talk < 30:
            coaching_moments.append({
                "type": "low_prospect_engagement",
                "timestamp": 0.5,
                "description": f"Prospect only spoke {prospect_talk}% of the time",
                "severity": "high",
                "suggestion": "Ask more open-ended questions to increase prospect participation"
            })
        elif prospect_talk > 70:
            coaching_moments.append({
                "type": "low_rep_control",
                "timestamp": 0.5,
                "description": f"Rep only spoke {talk_ratio.get('rep_percentage', 50)}% of the time",
                "severity": "medium",
                "suggestion": "Take more control to guide the conversation toward outcomes"
            })
        
        # Sentiment drops
        for i in range(1, len(sentiment_timeline)):
            prev_sentiment = sentiment_timeline[i-1].get("sentiment_score", 0)
            curr_sentiment = sentiment_timeline[i].get("sentiment_score", 0)
            
            if prev_sentiment > 0.3 and curr_sentiment < -0.3:
                coaching_moments.append({
                    "type": "sentiment_drop",
                    "timestamp": sentiment_timeline[i].get("timestamp", 0),
                    "description": "Significant sentiment drop detected",
                    "severity": "high",
                    "suggestion": "Review what caused the negative shift and address concerns"
                })
        
        return coaching_moments
    
    def generate_executive_summary(self, analysis: Dict) -> str:
        """Generate executive summary for managers"""
        deal_score = analysis.get("deal_score", 0)
        intent = analysis.get("intent_classification", "unknown")
        objection_count = analysis.get("objection_count", 0)
        risk_level = analysis.get("risk_level", "unknown")
        
        summary_parts = []
        
        # Overall assessment
        if deal_score >= 80:
            summary_parts.append(f"Strong deal health (score: {deal_score})")
        elif deal_score >= 60:
            summary_parts.append(f"Moderate deal health (score: {deal_score})")
        else:
            summary_parts.append(f"Weak deal health (score: {deal_score})")
        
        # Intent and engagement
        summary_parts.append(f"Buyer intent: {intent}")
        
        # Objections
        if objection_count > 0:
            summary_parts.append(f"{objection_count} objections detected")
        
        # Risk level
        if risk_level in ["high", "critical"]:
            summary_parts.append(f"High risk deal - requires attention")
        
        # Key recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            summary_parts.append(f"Key focus: {recommendations[0]}")
        
        return ". ".join(summary_parts) + "."


insight_generator = InsightGenerator()
