"""
API package - exports all routers
"""
from app.api.applications import router as applications_router
from app.api.lenders import router as lenders_router

__all__ = [
    "applications_router",
    "lenders_router",
]
