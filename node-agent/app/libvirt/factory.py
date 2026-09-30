import logging
from app.config import settings
from app.libvirt.backend import VirtualizationBackend
from app.libvirt.mock_backend import MockLibvirtBackend

logger = logging.getLogger("node.backend_factory")

def get_backend() -> VirtualizationBackend:
    if settings.DEMO_MODE:
        logger.info("Initializing MOCK virtualization backend (DEMO_MODE=True)")
        return MockLibvirtBackend()

    try:
        from app.libvirt.real_backend import RealLibvirtBackend
        logger.info(f"Initializing REAL KVM/libvirt backend (URI: {settings.LIBVIRT_URI})")
        return RealLibvirtBackend(uri=settings.LIBVIRT_URI)
    except Exception as e:
        logger.warning(f"Could not initialize real libvirt backend ({e}). Falling back to MOCK mode.")
        return MockLibvirtBackend()
