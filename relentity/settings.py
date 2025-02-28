from pydantic_settings import BaseSettings, SettingsConfigDict


class OllamaSettings(BaseSettings):
    base_url: str = "http://192.168.1.14:11434"
    default_model: str = "qwen2.5:14b"  # we do what we can
    json_fix_model: str = "qwen2.5:14b"
    model_keep_alive: float = 300.0

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_prefix = "relentity_"
    )

settings = OllamaSettings()
