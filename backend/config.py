from functools import lru_cache
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'postgresql+psycopg://lenny:lenny_local_only@127.0.0.1:54329/lenny'
    agent_url: str = 'http://127.0.0.1:8788'
    agent_token: str = 'local-development-only'
    llm_provider: str = 'ollama'
    ollama_base_url: str = 'http://127.0.0.1:11434'
    ollama_model: str = 'qwen2.5:3b'
    anthropic_api_key: str = ''
    anthropic_model: str = 'claude-sonnet-4-5'
    model_timeout_seconds: int = 1500
    transcript_dir: str = 'data/transcripts/episodes'
    retrieval_limit: int = 5
    allow_sqlite: bool = False
    environment: str = 'development'
    access_username: str = 'reviewer'
    access_password: str = ''
    generation_requests_per_hour: int = Field(default=30, ge=1, le=1000)

    @model_validator(mode='after')
    def deployment_config(self):
        if self.database_url.startswith(('postgres://', 'postgresql://')):
            self.database_url = 'postgresql+psycopg://' + self.database_url.split('://', 1)[1]
        if not self.agent_url.startswith(('http://', 'https://')):
            self.agent_url = 'http://' + self.agent_url
        if self.environment == 'production':
            if len(self.access_password) < 16 or len(self.agent_token) < 32:
                raise ValueError('Production requires ACCESS_PASSWORD (at least 16 characters) and a private AGENT_TOKEN.')
        return self


@lru_cache
def settings():
    return Settings()
