class NoStoreMiddleware:
    """Session-specific demo responses must not be cached by the hosting proxy."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Cache-Control'] = 'no-store'
        return response
