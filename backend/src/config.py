"""Application configuration and environment settings for ChangePilot."""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ChangePilot runtime configuration."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Application Settings
    app_name: str = Field(default="ChangePilot", description="Name of the service")
    app_env: str = Field(default="development", description="Environment: development, test, production")
    log_level: str = Field(default="INFO", description="Logging level")
    host: str = Field(default="0.0.0.0", description="API listen host")
    port: int = Field(default=8000, description="API listen port")

    # Authentication & JWT Configuration
    jwt_secret_key: str = Field(
        default="changepilot-dev-secret-key-super-secure-for-local-hackathon-2026",
        alias="JWT_SECRET_KEY",
        description="HMAC secret key for signing JWT sessions"
    )
    jwt_algorithm: str = Field(default="HS256", description="Algorithm for JWT signing")
    jwt_access_token_expire_minutes: int = Field(default=1440, description="Token expiration duration (24h)")
    
    # Identity Platform / OAuth Providers
    google_client_id: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_SECRET")
    github_client_id: Optional[str] = Field(default=None, alias="GITHUB_CLIENT_ID")
    github_client_secret: Optional[str] = Field(default=None, alias="GITHUB_CLIENT_SECRET")

    # GitHub App Integration
    github_app_id: Optional[str] = Field(default=None, alias="GITHUB_APP_ID")
    github_app_private_key: Optional[str] = Field(default=None, alias="GITHUB_APP_PRIVATE_KEY")
    github_app_installation_id: Optional[str] = Field(default=None, alias="GITHUB_APP_INSTALLATION_ID")

    # Database Configuration (SQLite default for zero-config local/test, PostgreSQL in production)
    database_url: str = Field(
        default="sqlite:///./changepilot.db",
        alias="DATABASE_URL",
        description="Database connection URL"
    )

    # Vertex AI / Google GenAI Configuration
    # Uses ADC (Application Default Credentials) by default
    google_genai_use_vertexai: bool = Field(default=True, alias="GOOGLE_GENAI_USE_VERTEXAI")
    google_cloud_project: Optional[str] = Field(default=None, alias="GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = Field(default="global", alias="GOOGLE_CLOUD_LOCATION")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")

    # Safety & Execution Boundaries
    max_repository_size_mb: int = Field(default=100, description="Maximum permitted repository size in MB")
    max_repository_files: int = Field(default=5000, description="Maximum number of files allowed in repository")
    max_file_size_bytes: int = Field(default=500_000, description="Max individual file size for reading/patching (500KB)")
    command_timeout_seconds: int = Field(default=60, description="Hard timeout for test/build execution")
    clone_timeout_seconds: int = Field(default=45, description="Hard timeout for Git clone")
    workspace_base_dir: str = Field(default="temp_workspaces", description="Directory for isolated workspaces")

    # Sensitive patterns to reject in file paths and commands
    disallowed_path_patterns: list[str] = Field(
        default_factory=lambda: [
            ".git", ".env", ".aws", ".gcp", "id_rsa", "id_ed25519", "credentials", "secrets"
        ]
    )

    def is_vertex_configured(self) -> bool:
        """Returns True if Vertex AI settings are configured."""
        return bool(self.google_genai_use_vertexai and self.google_cloud_project)


# Global singleton settings instance
settings = Settings()
