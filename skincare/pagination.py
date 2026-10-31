from rest_framework.pagination import PageNumberPagination


class AdminPagination(PageNumberPagination):
    """Dashboard tables pick their own page size; exports ask for everything at once."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000
