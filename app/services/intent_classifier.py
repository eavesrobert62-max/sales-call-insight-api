import re
from typing import Dict, List, Tuple
from enum import Enum
from dataclasses import dataclass


class IntentType(Enum):
    RESEARCHING = "researching"
    COMPARING = "comparing"
    READY_TO_BUY = "ready_to_buy"
    STALLED = "stalled"


@dataclass
class IntentSignal:
    intent: IntentType
    keywords: List[str]
    weight: float
    description: str


class IntentClassifier:
    def __init__(self):
        self.intent_signals = [
            IntentSignal(
                intent=IntentType.READY_TO_BUY,
                keywords=["buy", "purchase", "sign", "contract", "agree", "ready", "let's do it", "when can we start"],
                weight=1.0,
                description="Strong buying signals and commitment language"
            ),
            IntentSignal(
                intent=IntentType.COMPARING,
                keywords=["compare", "versus", "vs", "alternative", "competitor", "other options", "difference between"],
                weight=0.7,
                description="Active comparison with alternatives"
            ),
            IntentSignal(
                intent=IntentType.RESEARCHING,
                keywords=["information", "details", "how does", "what is", "explain", "demo", "show me", "learn more"],
                weight=0.5,
                description="Information gathering and exploration"
            ),
            IntentSignal(
                intent=IntentType.STALLED,
                keywords=["think about it", "maybe later", "not sure", "need time", "let me get back", "hold off"],
                weight=0.3,
                description="Delay tactics and uncertainty"
            )
        ]
        
        # Negative indicators that reduce confidence
        self.negative_indicators = {
            IntentType.READY_TO_BUY: ["not ready", "too early", "just looking", "no budget"],
            IntentType.COMPARING: ["only you", "no other options", "already decided"],
            IntentType.RESEARCHING: ["already know", "familiar with", "understand"],
            IntentType.STALLED: ["definitely interested", "sure", "absolutely"]
        }
    
    def classify_intent(self, transcript: str, talk_ratio: Dict = None) -> Dict:
        """Classify buyer intent from transcript"""
        text_lower = transcript.lower()
        
        # Score each intent type
        intent_scores = {}
        
        for signal in self.intent_signals:
            score = self._calculate_intent_score(text_lower, signal)
            
            # Apply negative indicators
            negative_score = self._calculate_negative_score(text_lower, signal.intent)
            score = max(0, score - negative_score)
            
            # Adjust based on talk ratio if available
            if talk_ratio:
                score = self._adjust_score_by_talk_ratio(score, signal.intent, talk_ratio)
            
            intent_scores[signal.intent.value] = score
        
        # Determine primary intent
        primary_intent = max(intent_scores.items(), key=lambda x: x[1])
        confidence = primary_intent[1] / max(intent_scores.values()) if max(intent_scores.values()) > 0 else 0
        
        return {
            "primary_intent": primary_intent[0],
            "confidence": min(confidence, 1.0),
            "all_scores": intent_scores,
            "reasoning": self._generate_reasoning(primary_intent[0], intent_scores, text_lower)
        }
    
    def _calculate_intent_score(self, text: str, signal: IntentSignal) -> float:
        """Calculate score for a specific intent signal"""
        score = 0.0
        
        for keyword in signal.keywords:
            # Count occurrences
            occurrences = len(re.findall(rf'\b{re.escape(keyword)}\b', text))
            score += occurrences * signal.weight
        
        # Look for variations and context
        if signal.intent == IntentType.READY_TO_BUY:
            # Check for questions about implementation/onboarding
            if any(word in text for word in ["implementation", "onboarding", "start", "go live"]):
                score += 0.5
        
        elif signal.intent == IntentType.COMPARING:
            # Check for specific competitor mentions
            if any(word in text for word in ["salesforce", "hubspot", "zoho", "pipedrive"]):
                score += 0.3
        
        elif signal.intent == IntentType.STALLED:
            # Check for indefinite language
            if any(word in text for word in ["someday", "eventually", "down the road"]):
                score += 0.3
        
        return score
    
    def _calculate_negative_score(self, text: str, intent: IntentType) -> float:
        """Calculate negative score that reduces intent confidence"""
        negative_score = 0.0
        
        if intent in self.negative_indicators:
            for indicator in self.negative_indicators[intent]:
                if indicator in text:
                    negative_score += 0.5
        
        return negative_score
    
    def _adjust_score_by_talk_ratio(self, score: float, intent: IntentType, talk_ratio: Dict) -> float:
        """Adjust intent score based on talk ratio patterns"""
        if not talk_ratio or "prospect_percentage" not in talk_ratio:
            return score
        
        prospect_talk_percentage = talk_ratio["prospect_percentage"]
        
        # High prospect engagement generally indicates higher intent
        if prospect_talk_percentage > 60:
            score *= 1.2
        elif prospect_talk_percentage < 30:
            score *= 0.8
        
        # Specific adjustments by intent
        if intent == IntentType.READY_TO_BUY and prospect_talk_percentage > 50:
            score *= 1.3  # High engagement + buying signals = strong indicator
        elif intent == IntentType.STALLED and prospect_talk_percentage < 40:
            score *= 1.2  # Low engagement + stalling language = likely true stall
        
        return score
    
    def _generate_reasoning(self, primary_intent: str, scores: Dict, text: str) -> str:
        """Generate human-readable reasoning for intent classification"""
        signal = next(s for s in self.intent_signals if s.intent.value == primary_intent)
        
        reasoning_parts = [f"Classified as {primary_intent} based on {signal.description}."]
        
        # Add specific evidence if available
        found_keywords = [kw for kw in signal.keywords if kw in text]
        if found_keywords:
            reasoning_parts.append(f"Detected keywords: {', '.join(found_keywords[:3])}")
        
        # Add confidence context
        max_score = max(scores.values())
        if max_score > 0:
            confidence = scores[primary_intent] / max_score
            if confidence > 0.8:
                reasoning_parts.append("High confidence - clear intent signals detected.")
            elif confidence > 0.5:
                reasoning_parts.append("Moderate confidence - some mixed signals present.")
            else:
                reasoning_parts.append("Low confidence - intent unclear or mixed.")
        
        return " ".join(reasoning_parts)
    
    def get_intent_trend_analysis(self, historical_intents: List[Dict]) -> Dict:
        """Analyze intent trends over multiple calls"""
        if not historical_intents:
            return {"trend": "no_data", "insights": []}
        
        intent_counts = {}
        for intent_data in historical_intents:
            intent = intent_data.get("primary_intent", "unknown")
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        total_calls = len(historical_intents)
        intent_percentages = {k: (v / total_calls) * 100 for k, v in intent_counts.items()}
        
        # Generate insights
        insights = []
        
        if IntentType.READY_TO_BUY.value in intent_percentages:
            buy_rate = intent_percentages[IntentType.READY_TO_BUY.value]
            if buy_rate > 30:
                insights.append(f"Strong buying intent detected in {buy_rate:.1f}% of calls - good pipeline health.")
            elif buy_rate < 10:
                insights.append(f"Low buying intent ({buy_rate:.1f}%) - consider qualification improvements.")
        
        if IntentType.STALLED.value in intent_percentages:
            stall_rate = intent_percentages[IntentType.STALLED.value]
            if stall_rate > 40:
                insights.append(f"High stall rate ({stall_rate:.1f}%) - review objection handling and urgency creation.")
        
        return {
            "trend": "analyzed",
            "intent_distribution": intent_percentages,
            "insights": insights,
            "sample_size": total_calls
        }


intent_classifier = IntentClassifier()
