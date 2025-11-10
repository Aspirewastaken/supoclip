"""
AI-powered title generation system using OpenRouter for multi-LLM access.

This module generates viral, platform-optimized titles for video clips using
multiple AI models through OpenRouter API. Titles are scored by virality potential
and tailored to specific platforms and target audiences.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from enum import Enum
import aiohttp
from pydantic import BaseModel, Field, validator
import re

from ..config import Config

logger = logging.getLogger(__name__)
config = Config()


class Platform(str, Enum):
    """Supported social media platforms."""
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"


class TitleStyle(str, Enum):
    """Title style formats for different content types."""
    QUESTION = "question"  # Starts with a question
    SHOCKING = "shocking"  # Uses shocking/surprising elements
    HOW_TO = "how_to"  # Educational/tutorial format
    LISTICLE = "listicle"  # Number-based (e.g., "5 ways to...")
    STORY = "story"  # Narrative/story format
    DIRECT = "direct"  # Direct, straightforward
    CURIOSITY = "curiosity"  # Curiosity gap technique
    EMOTIONAL = "emotional"  # Emotional hook


class GeneratedTitle(BaseModel):
    """A single generated title with metadata."""
    title: str = Field(description="The generated title text")
    style: TitleStyle = Field(description="The style/format of the title")
    virality_score: float = Field(
        description="Predicted virality score (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(description="Why this title should be effective")
    character_count: int = Field(description="Number of characters in title")
    model_used: str = Field(description="AI model that generated this title")

    @validator('character_count', always=True)
    def set_character_count(cls, v, values):
        """Automatically set character count from title."""
        if 'title' in values:
            return len(values['title'])
        return v


class TitleGenerationRequest(BaseModel):
    """Request parameters for title generation."""
    transcript_text: str = Field(description="The transcript text of the clip")
    platform: Platform = Field(
        default=Platform.TIKTOK,
        description="Target platform for the title"
    )
    target_audience: Optional[str] = Field(
        default=None,
        description="Target audience description (e.g., 'young entrepreneurs', 'fitness enthusiasts')"
    )
    key_topics: Optional[List[str]] = Field(
        default=None,
        description="Key topics from the video"
    )
    duration_seconds: Optional[float] = Field(
        default=None,
        description="Clip duration in seconds"
    )
    num_variations: int = Field(
        default=8,
        description="Number of title variations to generate",
        ge=3,
        le=15
    )
    include_styles: Optional[List[TitleStyle]] = Field(
        default=None,
        description="Specific title styles to include (generates all if None)"
    )


class TitleGenerationResponse(BaseModel):
    """Response containing generated titles."""
    titles: List[GeneratedTitle] = Field(description="List of generated titles")
    best_title: GeneratedTitle = Field(description="Highest scoring title")
    platform: Platform = Field(description="Platform these titles were generated for")
    total_generated: int = Field(description="Total number of titles generated")


class TitleGenerator:
    """
    AI-powered title generator using OpenRouter for multi-LLM access.

    Uses multiple AI models to generate diverse, viral titles optimized
    for different social media platforms and content styles.
    """

    # OpenRouter models to use for title generation
    OPENROUTER_MODELS = [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4-turbo",
        "google/gemini-2.0-flash-001",
        "meta-llama/llama-3.1-70b-instruct",
        "mistralai/mistral-large-2407",
    ]

    # Platform-specific character limits
    PLATFORM_LIMITS = {
        Platform.TIKTOK: 150,
        Platform.INSTAGRAM: 125,
        Platform.YOUTUBE: 100,
        Platform.TWITTER: 280,
        Platform.LINKEDIN: 120,
    }

    # Platform-specific optimization tips
    PLATFORM_STYLES = {
        Platform.TIKTOK: "casual, trendy, uses slang, creates FOMO, hooks in first 3 words",
        Platform.INSTAGRAM: "aesthetic, aspirational, uses emojis strategically, creates desire",
        Platform.YOUTUBE: "search-optimized, clear value proposition, includes keywords",
        Platform.TWITTER: "punchy, conversational, thread-starter potential",
        Platform.LINKEDIN: "professional, thought-leadership, industry insights",
    }

    def __init__(self):
        """Initialize the title generator."""
        self.api_key = config.openrouter_api_key
        self.referer = config.openrouter_referer

        if not self.api_key:
            logger.warning("OpenRouter API key not configured. Title generation will fail.")

    def _build_system_prompt(self, platform: Platform, target_audience: Optional[str] = None) -> str:
        """
        Build the system prompt for title generation.

        Args:
            platform: Target social media platform
            target_audience: Optional target audience description

        Returns:
            System prompt string
        """
        char_limit = self.PLATFORM_LIMITS[platform]
        platform_style = self.PLATFORM_STYLES[platform]

        audience_context = ""
        if target_audience:
            audience_context = f"\nTARGET AUDIENCE: {target_audience}"

        return f"""You are an expert social media content strategist specializing in viral {platform.value} titles.

Your goal is to create highly engaging, click-worthy titles that maximize views and engagement.

PLATFORM: {platform.value.upper()}
CHARACTER LIMIT: {char_limit} characters{audience_context}

PLATFORM STYLE GUIDELINES:
{platform_style}

TITLE CREATION PRINCIPLES:

1. HOOK PSYCHOLOGY:
   - Create curiosity gaps (make them want to know more)
   - Use pattern interrupts (unexpected angles)
   - Trigger emotional responses (surprise, excitement, validation)
   - Promise value (what they'll learn or gain)

2. VIRALITY FACTORS:
   - Strong opening (first 3 words are critical)
   - Relatable pain points or desires
   - Surprising or counterintuitive angles
   - Social proof implications ("everyone is talking about...")
   - Urgency or timeliness

3. FORMATTING BEST PRACTICES:
   - Use powerful action verbs
   - Include specific numbers when relevant
   - Ask compelling questions
   - Create before/after contrasts
   - Use "you" and "your" for direct connection

4. AVOID:
   - Clickbait that doesn't deliver
   - Generic or boring descriptions
   - Overly complex language
   - Misleading information
   - Excessive emojis or special characters

Your titles should be authentic, deliver on their promise, and make viewers genuinely excited to watch."""

    def _build_user_prompt(
        self,
        transcript: str,
        key_topics: Optional[List[str]] = None,
        duration: Optional[float] = None,
        style: Optional[TitleStyle] = None
    ) -> str:
        """
        Build the user prompt with clip context.

        Args:
            transcript: Transcript text of the clip
            key_topics: Optional key topics
            duration: Optional clip duration
            style: Optional specific style to use

        Returns:
            User prompt string
        """
        topics_context = ""
        if key_topics:
            topics_context = f"\nKEY TOPICS: {', '.join(key_topics)}"

        duration_context = ""
        if duration:
            duration_context = f"\nCLIP DURATION: {duration:.1f} seconds"

        style_instruction = ""
        if style:
            style_map = {
                TitleStyle.QUESTION: "Create a compelling question that makes viewers curious",
                TitleStyle.SHOCKING: "Use surprising or shocking elements to grab attention",
                TitleStyle.HOW_TO: "Frame as educational/tutorial (how to, guide to, etc.)",
                TitleStyle.LISTICLE: "Use number-based format (X ways to, X things, etc.)",
                TitleStyle.STORY: "Tell it as a narrative or story hook",
                TitleStyle.DIRECT: "Be direct and straightforward about the value",
                TitleStyle.CURIOSITY: "Create a curiosity gap without revealing everything",
                TitleStyle.EMOTIONAL: "Lead with emotional hook (excitement, inspiration, etc.)",
            }
            style_instruction = f"\n\nSTYLE REQUIREMENT: {style_map[style]}"

        return f"""Generate a viral title for this video clip.

CLIP TRANSCRIPT:
{transcript}{topics_context}{duration_context}{style_instruction}

Generate ONE highly engaging title that:
1. Accurately represents the content
2. Maximizes click-through potential
3. Fits the character limit
4. Follows the platform style guidelines
5. Creates genuine excitement to watch

Respond with ONLY the title text, nothing else."""

    async def _call_openrouter(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.9
    ) -> Optional[str]:
        """
        Make an API call to OpenRouter.

        Args:
            model: Model identifier
            system_prompt: System prompt
            user_prompt: User prompt
            temperature: Sampling temperature

        Returns:
            Generated title text or None if failed
        """
        if not self.api_key:
            logger.error("OpenRouter API key not configured")
            return None

        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.referer,
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 150,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API error ({response.status}): {error_text}")
                        return None

                    data = await response.json()
                    title = data["choices"][0]["message"]["content"].strip()

                    # Clean up the title (remove quotes, extra whitespace)
                    title = title.strip('"\'').strip()

                    return title

        except asyncio.TimeoutError:
            logger.error(f"Timeout calling OpenRouter model: {model}")
            return None
        except Exception as e:
            logger.error(f"Error calling OpenRouter model {model}: {e}")
            return None

    def _calculate_virality_score(
        self,
        title: str,
        platform: Platform,
        style: TitleStyle
    ) -> float:
        """
        Calculate a virality score for a title based on various factors.

        Args:
            title: The title text
            platform: Target platform
            style: Title style

        Returns:
            Virality score between 0.0 and 1.0
        """
        score = 0.5  # Base score

        # Length scoring (platform-specific optimal ranges)
        char_limit = self.PLATFORM_LIMITS[platform]
        length = len(title)

        if platform == Platform.TIKTOK:
            optimal_range = (50, 100)
        elif platform == Platform.YOUTUBE:
            optimal_range = (50, 80)
        else:
            optimal_range = (40, 90)

        if optimal_range[0] <= length <= optimal_range[1]:
            score += 0.15
        elif length > char_limit:
            score -= 0.2  # Penalize over limit

        # Powerful words that increase engagement
        power_words = [
            'secret', 'revealed', 'shocking', 'amazing', 'incredible', 'ultimate',
            'proven', 'guaranteed', 'insider', 'exclusive', 'breakthrough', 'hack',
            'you', 'your', 'why', 'how', 'what', 'finally', 'never', 'always',
            'best', 'worst', 'truth', 'exposed', 'mistake', 'warning'
        ]

        title_lower = title.lower()
        power_word_count = sum(1 for word in power_words if word in title_lower)
        score += min(power_word_count * 0.05, 0.15)  # Up to 0.15 bonus

        # Number presence (specific numbers increase credibility)
        if re.search(r'\d+', title):
            score += 0.1

        # Question format (questions drive engagement)
        if '?' in title:
            score += 0.1

        # First word strength (critical for hook)
        first_word = title.split()[0].lower() if title.split() else ""
        strong_starters = ['why', 'how', 'what', 'this', 'the', 'i', 'you', 'watch', 'stop', 'wait']
        if first_word in strong_starters:
            score += 0.08

        # Emotional words
        emotional_words = [
            'love', 'hate', 'fear', 'hope', 'dream', 'wish', 'feel', 'pain',
            'happy', 'sad', 'angry', 'excited', 'amazing', 'terrible', 'beautiful'
        ]
        if any(word in title_lower for word in emotional_words):
            score += 0.07

        # Style-specific bonuses
        style_bonuses = {
            TitleStyle.QUESTION: 0.05,
            TitleStyle.SHOCKING: 0.08,
            TitleStyle.HOW_TO: 0.06,
            TitleStyle.LISTICLE: 0.07,
            TitleStyle.CURIOSITY: 0.09,
        }
        score += style_bonuses.get(style, 0.0)

        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))

    def _detect_title_style(self, title: str) -> TitleStyle:
        """
        Detect the style of a generated title.

        Args:
            title: The title text

        Returns:
            Detected title style
        """
        title_lower = title.lower()

        if '?' in title:
            return TitleStyle.QUESTION
        elif re.search(r'\d+\s+(ways|things|tips|secrets|hacks|reasons|steps)', title_lower):
            return TitleStyle.LISTICLE
        elif title_lower.startswith(('how to', 'how i', 'guide to', 'learn to')):
            return TitleStyle.HOW_TO
        elif any(word in title_lower for word in ['shocking', 'unbelievable', 'insane', 'crazy', 'mind-blowing']):
            return TitleStyle.SHOCKING
        elif any(word in title_lower for word in ['story', 'when i', 'time i', 'day i']):
            return TitleStyle.STORY
        elif any(word in title_lower for word in ['why', 'what', 'this is', 'the truth', 'nobody tells you']):
            return TitleStyle.CURIOSITY
        elif any(word in title_lower for word in ['love', 'hate', 'fear', 'dream', 'changed my life']):
            return TitleStyle.EMOTIONAL
        else:
            return TitleStyle.DIRECT

    async def generate_titles(
        self,
        request: TitleGenerationRequest
    ) -> TitleGenerationResponse:
        """
        Generate multiple title variations using different AI models.

        Args:
            request: Title generation request parameters

        Returns:
            TitleGenerationResponse with generated titles
        """
        logger.info(f"Generating {request.num_variations} titles for {request.platform.value}")

        # Build prompts
        system_prompt = self._build_system_prompt(request.platform, request.target_audience)

        # Determine styles to generate
        if request.include_styles:
            styles = request.include_styles
        else:
            # Use all styles, cycling through them
            styles = list(TitleStyle)

        # Generate titles using different models and styles
        tasks = []
        models_to_use = []
        styles_to_use = []

        for i in range(request.num_variations):
            model = self.OPENROUTER_MODELS[i % len(self.OPENROUTER_MODELS)]
            style = styles[i % len(styles)]

            user_prompt = self._build_user_prompt(
                request.transcript_text,
                request.key_topics,
                request.duration_seconds,
                style
            )

            tasks.append(self._call_openrouter(model, system_prompt, user_prompt))
            models_to_use.append(model)
            styles_to_use.append(style)

        # Execute all generations in parallel
        generated_texts = await asyncio.gather(*tasks)

        # Process results
        generated_titles: List[GeneratedTitle] = []

        for i, title_text in enumerate(generated_texts):
            if not title_text:
                logger.warning(f"Failed to generate title with {models_to_use[i]}")
                continue

            # Truncate if over platform limit
            char_limit = self.PLATFORM_LIMITS[request.platform]
            if len(title_text) > char_limit:
                title_text = title_text[:char_limit-3] + "..."
                logger.info(f"Truncated title to {char_limit} chars")

            # Detect actual style (may differ from requested)
            detected_style = self._detect_title_style(title_text)

            # Calculate virality score
            virality_score = self._calculate_virality_score(
                title_text,
                request.platform,
                detected_style
            )

            # Generate reasoning
            reasoning = self._generate_reasoning(
                title_text,
                detected_style,
                virality_score,
                request.platform
            )

            generated_titles.append(GeneratedTitle(
                title=title_text,
                style=detected_style,
                virality_score=virality_score,
                reasoning=reasoning,
                character_count=len(title_text),
                model_used=models_to_use[i].split('/')[-1]  # Just model name
            ))

        if not generated_titles:
            raise ValueError("Failed to generate any titles")

        # Sort by virality score
        generated_titles.sort(key=lambda x: x.virality_score, reverse=True)

        logger.info(f"Generated {len(generated_titles)} titles, best score: {generated_titles[0].virality_score:.3f}")

        return TitleGenerationResponse(
            titles=generated_titles,
            best_title=generated_titles[0],
            platform=request.platform,
            total_generated=len(generated_titles)
        )

    def _generate_reasoning(
        self,
        title: str,
        style: TitleStyle,
        score: float,
        platform: Platform
    ) -> str:
        """
        Generate reasoning for why a title should be effective.

        Args:
            title: The title text
            style: Title style
            score: Virality score
            platform: Target platform

        Returns:
            Reasoning text
        """
        reasons = []

        # Style-based reasoning
        style_reasons = {
            TitleStyle.QUESTION: "Creates curiosity by posing a question viewers want answered",
            TitleStyle.SHOCKING: "Uses surprising elements to grab attention immediately",
            TitleStyle.HOW_TO: "Promises educational value that viewers can apply",
            TitleStyle.LISTICLE: "Specific numbers create clear expectations and credibility",
            TitleStyle.STORY: "Narrative format makes content more relatable and engaging",
            TitleStyle.DIRECT: "Clear, straightforward approach builds trust",
            TitleStyle.CURIOSITY: "Creates information gap that drives clicks",
            TitleStyle.EMOTIONAL: "Emotional connection increases engagement and shares",
        }
        reasons.append(style_reasons[style])

        # Check for power words
        title_lower = title.lower()
        if any(word in title_lower for word in ['you', 'your']):
            reasons.append("Uses direct address to create personal connection")

        if re.search(r'\d+', title):
            reasons.append("Includes specific number for credibility")

        # Platform optimization
        char_limit = self.PLATFORM_LIMITS[platform]
        if len(title) <= char_limit:
            reasons.append(f"Optimized length for {platform.value} ({len(title)}/{char_limit} chars)")

        # Score interpretation
        if score >= 0.8:
            reasons.append("High virality potential based on engagement factors")
        elif score >= 0.6:
            reasons.append("Strong engagement potential with proven elements")

        return ". ".join(reasons) + "."


# Convenience function for simple title generation
async def generate_titles_for_clip(
    transcript: str,
    platform: str = "tiktok",
    target_audience: Optional[str] = None,
    key_topics: Optional[List[str]] = None,
    duration_seconds: Optional[float] = None,
    num_variations: int = 8
) -> TitleGenerationResponse:
    """
    Convenience function to generate titles for a clip.

    Args:
        transcript: Transcript text of the clip
        platform: Target platform (tiktok, instagram, youtube, etc.)
        target_audience: Optional target audience description
        key_topics: Optional key topics from the video
        duration_seconds: Optional clip duration
        num_variations: Number of title variations to generate

    Returns:
        TitleGenerationResponse with generated titles
    """
    generator = TitleGenerator()

    request = TitleGenerationRequest(
        transcript_text=transcript,
        platform=Platform(platform.lower()),
        target_audience=target_audience,
        key_topics=key_topics,
        duration_seconds=duration_seconds,
        num_variations=num_variations
    )

    return await generator.generate_titles(request)
