"""
Custom pagination classes for the Gym Management API.
"""
from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """
    Custom pagination class that allows clients to specify page size.
    
    Usage: ?page=2&page_size=100
    """
    page_size = 20  # Default page size
    page_size_query_param = 'page_size'  # Allow client to set via ?page_size=X
    max_page_size = 1000  # Maximum allowed page size
