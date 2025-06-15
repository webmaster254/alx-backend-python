from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination, CursorPagination
from rest_framework.response import Response
from collections import OrderedDict


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for most API endpoints.
    Uses page number and allows custom page size.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """
        Enhanced paginated response with additional metadata.
        """
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('current_page', self.page.number),
            ('results', data)
        ]))


class MessageLimitOffsetPagination(LimitOffsetPagination):
    """
    Limit-offset based pagination for message list views.
    Allows clients to request a specific number of results with an offset.
    """
    default_limit = 20
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100
    
    def get_paginated_response(self, data):
        """
        Enhanced paginated response with additional metadata.
        """
        return Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('limit', self.limit),
            ('offset', self.offset),
            ('results', data)
        ]))


class MessageCursorPagination(CursorPagination):
    """
    Cursor-based pagination for chronological message views.
    More efficient for large datasets with frequent inserts.
    Good for real-time messaging where new messages are constantly being added.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-sent_at'  # Default to most recent messages first
    
    def get_paginated_response(self, data):
        """
        Enhanced paginated response with additional metadata.
        """
        return Response(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_size', self.get_page_size(self.request)),
            ('results', data)
        ]))
