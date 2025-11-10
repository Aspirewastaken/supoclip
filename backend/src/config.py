from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    def __init__(self):
        self.whisper_model = os.getenv("WHISPER_MODEL", "base")
        self.llm = os.getenv("LLM_MODEL", "google-gla:gemini-2.5-flash-lite")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.assembly_ai_api_key = os.getenv("ASSEMBLY_AI_API_KEY")

        # OpenRouter for multi-LLM council
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_referer = os.getenv("OPENROUTER_REFERER", "http://localhost:3000")

        self.max_video_duration = int(os.getenv("MAX_VIDEO_DURATION", "3600"))
        self.output_dir = os.getenv("OUTPUT_DIR", "outputs")

        self.max_clips = int(os.getenv("MAX_CLIPS", "10"))
        self.clip_duration = int(os.getenv("CLIP_DURATION", "30"))  # seconds

        self.temp_dir = os.getenv("TEMP_DIR", "temp")

        # Redis configuration
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))

        # Google Calendar OAuth configuration
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")

        # CDN configuration
        self.cdn_enabled = os.getenv("CDN_ENABLED", "false").lower() == "true"
        self.cdn_provider = os.getenv("CDN_PROVIDER")  # cloudfront, r2, bunny
        self.cdn_base_url = os.getenv("CDN_BASE_URL", "")

        # AWS CloudFront configuration
        self.aws_s3_bucket = os.getenv("AWS_S3_BUCKET")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.cloudfront_distribution_id = os.getenv("CLOUDFRONT_DISTRIBUTION_ID")
        self.cloudfront_key_id = os.getenv("CLOUDFRONT_KEY_ID")
        self.cloudfront_private_key_path = os.getenv("CLOUDFRONT_PRIVATE_KEY_PATH")

        # Cloudflare R2 configuration
        self.cloudflare_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.r2_access_key_id = os.getenv("R2_ACCESS_KEY_ID")
        self.r2_secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
        self.r2_bucket_name = os.getenv("R2_BUCKET_NAME")
        self.r2_public_url = os.getenv("R2_PUBLIC_URL")
        self.cloudflare_zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
        self.cloudflare_api_token = os.getenv("CLOUDFLARE_API_TOKEN")

        # Bunny CDN configuration
        self.bunny_storage_zone_name = os.getenv("BUNNY_STORAGE_ZONE_NAME")
        self.bunny_storage_api_key = os.getenv("BUNNY_STORAGE_API_KEY")
        self.bunny_cdn_api_key = os.getenv("BUNNY_CDN_API_KEY")
        self.bunny_storage_region = os.getenv("BUNNY_STORAGE_REGION", "de")
        self.bunny_pull_zone_id = os.getenv("BUNNY_PULL_ZONE_ID")
