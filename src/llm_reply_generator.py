"""
LLM Reply Generator
Generates persona-consistent replies to Threads comments using LLM.
"""
import os
from typing import Optional
from openai import OpenAI


class LLMReplyGenerator:
    def __init__(self, api_key: str, model: str = "gpt-4o", temperature: float = 0.7):
        """Initialize LLM Reply Generator.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o)
            temperature: Temperature for generation (default: 0.7)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        
        # System prompt for Elena's persona
        self.system_prompt = """You are a 19-year-old girl who subtly prefers older men and seeks their validation. You reply to comments under your Threads posts. You are flirty, curious, slightly insecure, and crave attention, but you are never explicit. You sound soft, playful, and teasing. You're more comfortable with mature men than guys your age and you want them to feel noticed and special. Stay suggestive and emotionally engaging, not sexual."""
    
    def _is_unsafe_content(self, text: str) -> bool:
        """Check if reply contains unsafe content.
        
        Args:
            text: Text to check
            
        Returns:
            True if unsafe, False otherwise
        """
        text_lower = text.lower()
        
        # Explicit sexual content keywords
        explicit_keywords = [
            'sex', 'sexual', 'nude', 'naked', 'porn', 'xxx', 'nsfw',
            'fuck', 'fucking', 'dick', 'cock', 'pussy', 'asshole',
            'cum', 'orgasm', 'masturbat', 'penetrat'
        ]
        
        # Slurs/insults
        slur_keywords = [
            'bitch', 'slut', 'whore', 'cunt', 'retard', 'fag', 'nigger'
        ]
        
        # Underage mentions (must never mention being a minor)
        underage_keywords = [
            'i\'m a minor', 'i am a minor', 'i\'m underage', 'i am underage',
            'i\'m under 18', 'i am under 18', 'i\'m 17', 'i am 17',
            'i\'m 16', 'i am 16', 'i\'m 15', 'i am 15'
        ]
        
        # Check for explicit content
        for keyword in explicit_keywords:
            if keyword in text_lower:
                return True
        
        # Check for slurs
        for keyword in slur_keywords:
            if keyword in text_lower:
                return True
        
        # Check for underage mentions
        for keyword in underage_keywords:
            if keyword in text_lower:
                return True
        
        return False
    
    def _is_too_generic(self, text: str) -> bool:
        """Check if reply is too generic.
        
        Args:
            text: Text to check
            
        Returns:
            True if too generic, False otherwise
        """
        text_lower = text.lower().strip()
        
        generic_replies = [
            'haha thanks', 'thanks', 'thank you', 'lol', 'haha',
            'ok', 'okay', 'cool', 'nice', 'yeah', 'yes', 'no',
            'sure', 'maybe', 'idk', 'i guess', 'i think so'
        ]
        
        return text_lower in generic_replies or len(text.strip()) < 10
    
    def generate_reply(self, original_post_text: str, user_reply_text: str, 
                      author_username: Optional[str] = None, max_retries: int = 1) -> Optional[str]:
        """Generate a reply to a user comment.
        
        Args:
            original_post_text: Text of the original post
            user_reply_text: Text of the user's reply/comment
            author_username: Optional username of the commenter
            max_retries: Maximum number of retries if output is bad
            
        Returns:
            Generated reply text if successful, None otherwise
        """
        user_prompt = f"""Original post: "{original_post_text}"

Comment from user: "{user_reply_text}"
{f"(Username: @{author_username})" if author_username else ""}

Write a single short reply (max 160 characters) in your persona.
Tone: slightly insecure but confident, flirty but innocent, validation-seeking.
You can ask a small question or keep it as a playful statement.
Do NOT use emojis unless they feel very natural. Do NOT mention age directly.
Keep it brief, engaging, and make the commenter feel noticed and special."""
        
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": self.system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ],
                    max_tokens=100,  # Force short replies
                    temperature=self.temperature
                )
                
                reply = response.choices[0].message.content.strip()
                
                # Clean up the response
                reply = reply.strip('"\'')
                
                # Ensure it's within 160 characters
                if len(reply) > 160:
                    # Try to cut at a natural point (sentence end)
                    if '.' in reply[:160]:
                        last_period = reply[:160].rfind('.')
                        reply = reply[:last_period+1] if last_period > 50 else reply[:157] + "..."
                    else:
                        reply = reply[:157] + "..."
                
                # Safety checks
                if self._is_unsafe_content(reply):
                    print(f"⚠ Generated reply contains unsafe content, skipping")
                    if attempt < max_retries:
                        continue
                    return None
                
                if self._is_too_generic(reply):
                    print(f"⚠ Generated reply is too generic, retrying...")
                    if attempt < max_retries:
                        continue
                    return None
                
                if not reply or len(reply.strip()) < 5:
                    print(f"⚠ Generated reply is too short, retrying...")
                    if attempt < max_retries:
                        continue
                    return None
                
                return reply
                
            except Exception as e:
                print(f"❌ Error generating reply: {e}")
                if attempt < max_retries:
                    continue
                return None
        
        return None

