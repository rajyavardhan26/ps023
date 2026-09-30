import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.libvirt.factory import get_backend
from app.services.agent_service import AgentService
from app.api import health, vms

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(f"node.{settings.NODE_ID}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize virtualization engine (Real KVM or Mock)
    backend = get_backend()
    app.state.backend = backend

    service = AgentService(backend)
    app.state.service = service

    logger.info(f"Starting Node Agent '{settings.NODE_ID}' on port {settings.NODE_PORT}")

    # Register node with central controller
    asyncio.create_task(service.register_with_controller())
    
    # Start periodic heartbeat loop
    hb_task = asyncio.create_task(service.start_heartbeat_loop())

    yield

    logger.info(f"Shutting down Node Agent '{settings.NODE_ID}'")
    service.stop()
    hb_task.cancel()

app = FastAPI(
    title=f"PS-023 Node Agent ({settings.NODE_ID})",
    description="Hypervisor Node Agent for PS-023 Cloud Controller",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(vms.router)
