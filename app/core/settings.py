from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AirSight+ (Python)"
    API_V1_PREFIX: str = "/api/v1"
    CACHE_TTL_SECONDS: int = 600
    CACHE_MAX_ENTRIES: int = 1000

    # Vendor settings
    USE_MOCK_VENDOR: bool = False   # set False for real API mode
    AQICN_TOKEN: str = "put your api here"  #  token here

settings = Settings()

