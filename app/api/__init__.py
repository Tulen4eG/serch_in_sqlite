from fastapi import APIRouter

from .delete_endpoint import router as delete_router
from .search_endpoint import router as search_router


main_router = APIRouter()
main_router.include_router(
    delete_router,
    prefix="/delete",
    tags=["delete"])
main_router.include_router(
    search_router,
    prefix="/search",
    tags=["search"]
)

__all__ = ["main_router"]
