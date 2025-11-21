"""Pagination utilities for list endpoints."""

from typing import Generic, List, TypeVar, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Query


T = TypeVar('T')


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=50, ge=1, le=100, description="Items per page (max 100)")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size


class PageInfo(BaseModel):
    """Pagination metadata."""
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: List[T] = Field(..., description="List of items for current page")
    page_info: PageInfo = Field(..., description="Pagination metadata")


def paginate(
    query: Query,
    page: int = 1,
    page_size: int = 50,
    max_page_size: int = 100
) -> tuple[List, PageInfo]:
    """
    Apply pagination to SQLAlchemy query and return results with metadata.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        page_size: Number of items per page
        max_page_size: Maximum allowed page size
        
    Returns:
        Tuple of (items, page_info)
        
    Example:
        >>> from app.db.models import Project
        >>> query = db.query(Project).filter(Project.is_active == True)
        >>> items, page_info = paginate(query, page=2, page_size=20)
        >>> print(f"Page {page_info.page}/{page_info.total_pages}")
    """
    # Validate and constrain inputs
    page = max(1, page)
    page_size = min(max(1, page_size), max_page_size)
    
    # Get total count (before applying offset/limit)
    total_items = query.count()
    
    # Calculate pagination
    total_pages = (total_items + page_size - 1) // page_size  # Ceiling division
    has_next = page < total_pages
    has_prev = page > 1
    
    # Apply offset and limit
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    # Create page info
    page_info = PageInfo(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )
    
    return items, page_info


def create_paginated_response(
    items: List[T],
    page_info: PageInfo
) -> PaginatedResponse[T]:
    """
    Create a paginated response from items and page info.
    
    Args:
        items: List of items
        page_info: Pagination metadata
        
    Returns:
        PaginatedResponse object
    """
    return PaginatedResponse(items=items, page_info=page_info)
