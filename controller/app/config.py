import os
from pydantic_settings import BaseSettings

class ControllerSettings(BaseSettings):
    CONTROLLER_HOST: str = "0.0.0.0"
    CONTROLLER_PORT: int = 8000
    DATABASE_URL: str = "sqlite:///./cloud_controller.db"
    
    # Node Heartbeat & Liveness tracking (in seconds)
    HEARTBEAT_INTERVAL: int = 5
    HEARTBEAT_TIMEOUT: int = 15
    RECONCILIATION_INTERVAL: int = 10
    
    # Pre-shared security token for node communication
    NODE_AUTH_TOKEN: str = "ps023-hackathon-token-secret-xyz"
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = ControllerSettings()
