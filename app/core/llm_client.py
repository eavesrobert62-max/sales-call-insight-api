import openai
from typing import Dict, List, Optional
from app.core.config import settings
import json


class LLMClient:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.default_llm_model
    
    def analyze_transcript(self, transcript: str, metadata: Optional[Dict] = None) -> Dict:
        """Main analysis endpoint using GPT-4o-mini"""
        system_prompt = """
        You are a sales call analysis expert. Analyze the following sales call transcript and provide:
        
        1. Deal score (0-100) based on deal health indicators
        2. Buyer intent classification (researching/comparing/ready_to_buy/stalled)
        3. Detected objections with timestamps and recommended responses
        4. Talk ratio analysis (rep vs prospect)
        5. Sentiment timeline (engagement over call duration)
        6. Key topics discussed
        7. Decision makers identified
        8. Budget mentions
        9. Timeline urgency indicators
        10. Competitor mentions
        11. Next best actions ranked by priority
        
        Return as structured JSON.
        """
        
        user_prompt = f"""
        Transcript:
        {transcript}
        
        Metadata: {metadata or {}}
        
        Provide comprehensive analysis in JSON format.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            raise Exception(f"LLM analysis failed: {str(e)}")
    
    def generate_coaching_tips(self, objection: str, context: str) -> List[str]:
        """Generate coaching tips for specific objections"""
        prompt = f"""
        As a sales coach, provide 3 specific, actionable tips for handling this objection:
        
        Objection: {objection}
        Context: {context}
        
        Return as a JSON array of strings.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert sales coach."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            raise Exception(f"Coaching tips generation failed: {str(e)}")


llm_client = LLMClient()
