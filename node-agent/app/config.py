import os
from pydantic_settings import BaseSettings

class NodeSettings(BaseSettings):
    NODE_ID: str = "node-a"
    NODE_HOST: str = "127.0.0.1"
    NODE_PORT: int = 8001
    HOSTNAME: str = "fedora-node-1"
    
    CONTROLLER_URL: str = "http://127.0.0.1:8000"
    NODE_AUTH_TOKEN: str = "ps023-hackathon-token-secret-xyz"
    
    HEARTBEAT_INTERVAL: int = 5
    
    # Virtualization backend: true = simulated mock backend, false = real libvirt/KVM
    DEMO_MODE: bool = True
    LIBVIRT_URI: str = "qemu:///system"
    
    VM_STORAGE_DIR: str = "/tmp/ps023/disks"
    BASE_IMAGE_DIR: str = "/tmp/ps023/images"

    class Config:
        env_file = ".env"
        extra = "allow"

settings = NodeSettings()
