from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    IMG_PATH: str


@lru_cache
def get_settings():
    return Settings()