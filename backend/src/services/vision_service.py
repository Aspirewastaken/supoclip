"""
Vision AI service for screenshot analysis and content generation.
Supports both Anthropic Claude Vision and OpenAI GPT-4 Vision.
"""
import logging
from typing import Dict, List, Any, Optional
import json

from ..config import Config

logger = logging.getLogger(__name__)
config = Config()


class VisionService:
    """Service for analyzing screenshots and generating posting content."""

    def __init__(self):
        self.config = config

        # Determine which vision API to use based on available keys
        if self.config.anthropic_api_key:
            self.provider = "anthropic"
            logger.info("🤖 Using Anthropic Claude Vision")
        elif self.config.openai_api_key:
            self.provider = "openai"
            logger.info("🤖 Using OpenAI GPT-4 Vision")
        else:
            raise ValueError("No vision API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")

    async def analyze_screenshot(
        self,
        base64_image: str,
        image_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """
        Analyze a screenshot to detect platform, account type, and generate content suggestions.

        Args:
            base64_image: Base64-encoded image data
            image_type: MIME type of the image

        Returns:
            Dictionary containing analysis results and platform-specific suggestions
        """
        logger.info(f"📸 Analyzing screenshot with {self.provider}")

        if self.provider == "anthropic":
            return await self._analyze_with_claude(base64_image, image_type)
        else:
            return await self._analyze_with_openai(base64_image, image_type)

    async def _analyze_with_claude(
        self,
        base64_image: str,
        image_type: str
    ) -> Dict[str, Any]:
        """Analyze screenshot using Claude Vision API."""
        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic(api_key=self.config.anthropic_api_key)

            # Determine media type for Claude
            media_type = image_type if image_type.startswith("image/") else "image/jpeg"

            prompt = """Analyze this screenshot and provide the following information:

1. **Platform Detection**: Identify which social media platform this is from (TikTok, Instagram, YouTube, Twitter/X, etc.)
2. **Account Type**: What type of account is this? (personal, business, creator, brand, etc.)
3. **Content Type**: What type of content is shown? (video stats, post analytics, profile view, etc.)
4. **Key Metrics**: Extract any visible metrics (views, likes, shares, comments, etc.)

Then, generate platform-specific content suggestions for posting a video clip:

For each major platform (TikTok, Instagram Reels, YouTube Shorts), provide:
- **Title/Caption**: Engaging, hook-based title (optimized for platform)
- **Hashtags**: 5-10 relevant, trending hashtags
- **Description**: Brief description (if applicable)
- **Best Practices**: Platform-specific tips

Return your response as a JSON object with this structure:
{
  "platform": "detected platform",
  "account_type": "account type",
  "content_type": "content type",
  "metrics": {
    "views": "number or null",
    "likes": "number or null",
    "shares": "number or null",
    "comments": "number or null"
  },
  "suggestions": {
    "tiktok": {
      "title": "engaging title here",
      "hashtags": ["hashtag1", "hashtag2", ...],
      "description": "description",
      "tips": ["tip1", "tip2", ...]
    },
    "instagram": { ... },
    "youtube_shorts": { ... }
  }
}"""

            # Call Claude Vision API
            message = await client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Claude 3.5 Sonnet with vision
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64_image,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )

            # Extract and parse response
            response_text = message.content[0].text
            logger.info(f"📝 Claude response: {response_text[:200]}...")

            # Try to parse JSON from response
            result = self._parse_json_response(response_text)

            return result

        except Exception as e:
            logger.error(f"❌ Error with Claude Vision: {e}")
            # Return a default response
            return self._get_default_response(str(e))

    async def _analyze_with_openai(
        self,
        base64_image: str,
        image_type: str
    ) -> Dict[str, Any]:
        """Analyze screenshot using OpenAI GPT-4 Vision API."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.config.openai_api_key)

            prompt = """Analyze this screenshot and provide the following information:

1. **Platform Detection**: Identify which social media platform this is from (TikTok, Instagram, YouTube, Twitter/X, etc.)
2. **Account Type**: What type of account is this? (personal, business, creator, brand, etc.)
3. **Content Type**: What type of content is shown? (video stats, post analytics, profile view, etc.)
4. **Key Metrics**: Extract any visible metrics (views, likes, shares, comments, etc.)

Then, generate platform-specific content suggestions for posting a video clip:

For each major platform (TikTok, Instagram Reels, YouTube Shorts), provide:
- **Title/Caption**: Engaging, hook-based title (optimized for platform)
- **Hashtags**: 5-10 relevant, trending hashtags
- **Description**: Brief description (if applicable)
- **Best Practices**: Platform-specific tips

Return your response as a JSON object with this structure:
{
  "platform": "detected platform",
  "account_type": "account type",
  "content_type": "content type",
  "metrics": {
    "views": "number or null",
    "likes": "number or null",
    "shares": "number or null",
    "comments": "number or null"
  },
  "suggestions": {
    "tiktok": {
      "title": "engaging title here",
      "hashtags": ["hashtag1", "hashtag2", ...],
      "description": "description",
      "tips": ["tip1", "tip2", ...]
    },
    "instagram": { ... },
    "youtube_shorts": { ... }
  }
}"""

            # Call GPT-4 Vision API
            response = await client.chat.completions.create(
                model="gpt-4o",  # GPT-4 Vision model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_type};base64,{base64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
                max_tokens=2048,
            )

            # Extract and parse response
            response_text = response.choices[0].message.content
            logger.info(f"📝 OpenAI response: {response_text[:200]}...")

            # Try to parse JSON from response
            result = self._parse_json_response(response_text)

            return result

        except Exception as e:
            logger.error(f"❌ Error with OpenAI Vision: {e}")
            # Return a default response
            return self._get_default_response(str(e))

    async def generate_platform_content(
        self,
        platform: str,
        video_title: Optional[str] = None,
        video_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate platform-specific content without screenshot analysis.

        Args:
            platform: Target platform (tiktok, instagram, youtube_shorts)
            video_title: Optional video title
            video_description: Optional video description

        Returns:
            Dictionary with title, hashtags, description, and tips
        """
        logger.info(f"📝 Generating content for {platform}")

        prompt = f"""Generate optimized content for {platform} based on this video:

Video Title: {video_title or "Not provided"}
Video Description: {video_description or "Not provided"}

Provide:
1. **Title/Caption**: Engaging, hook-based title optimized for {platform}
2. **Hashtags**: 5-10 relevant, trending hashtags
3. **Description**: Brief, compelling description
4. **Best Practices**: Platform-specific posting tips

Return as JSON:
{{
  "title": "engaging title",
  "hashtags": ["hashtag1", "hashtag2", ...],
  "description": "description",
  "tips": ["tip1", "tip2", ...]
}}"""

        try:
            if self.provider == "anthropic":
                from anthropic import AsyncAnthropic
                client = AsyncAnthropic(api_key=self.config.anthropic_api_key)

                message = await client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )

                response_text = message.content[0].text

            else:  # openai
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=self.config.openai_api_key)

                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1024,
                )

                response_text = response.choices[0].message.content

            # Parse JSON response
            result = self._parse_json_response(response_text)
            return result

        except Exception as e:
            logger.error(f"❌ Error generating content: {e}")
            # Return default content
            return {
                "title": f"Amazing moment from the video!",
                "hashtags": [f"#{platform}", "#viral", "#fyp", "#trending", "#contentcreator"],
                "description": "Check out this amazing clip!",
                "tips": [
                    "Post during peak hours for maximum engagement",
                    "Engage with comments in the first hour",
                    "Use trending audio if possible"
                ]
            }

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from AI response, handling markdown code blocks."""
        try:
            # Try direct JSON parse first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            else:
                # Try to find JSON object in text
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())

            raise ValueError("Could not parse JSON from response")

    def _get_default_response(self, error_msg: str) -> Dict[str, Any]:
        """Return a default response structure when analysis fails."""
        return {
            "platform": "unknown",
            "account_type": "unknown",
            "content_type": "unknown",
            "metrics": {
                "views": None,
                "likes": None,
                "shares": None,
                "comments": None
            },
            "suggestions": {
                "tiktok": {
                    "title": "🔥 Check out this amazing moment!",
                    "hashtags": ["#tiktok", "#viral", "#fyp", "#trending", "#foryou"],
                    "description": "You won't believe what happens next! 👀",
                    "tips": [
                        "Post between 6-10 PM for maximum reach",
                        "Reply to comments quickly to boost engagement",
                        "Use trending sounds when possible"
                    ]
                },
                "instagram": {
                    "title": "This moment is everything 🤯",
                    "hashtags": ["#reels", "#instagram", "#viral", "#trending", "#explore"],
                    "description": "Save this for later! Drop a 🔥 if you agree",
                    "tips": [
                        "Use 3-5 relevant hashtags (Instagram limits reach with too many)",
                        "Post Reels at 9 AM, 12 PM, or 7 PM",
                        "Add a call-to-action in your caption"
                    ]
                },
                "youtube_shorts": {
                    "title": "The BEST part of this video 🎬",
                    "hashtags": ["#shorts", "#youtube", "#viral", "#trending"],
                    "description": "Subscribe for more amazing content like this!",
                    "tips": [
                        "Keep titles under 40 characters for mobile",
                        "Use #shorts in title and description",
                        "Post consistently (daily if possible)"
                    ]
                }
            },
            "error": error_msg
        }
