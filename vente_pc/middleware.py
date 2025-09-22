from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponseServerError

class ShowErrorsInDevelopmentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if settings.SHOW_CUSTOM_ERRORS:
            if response.status_code == 404:
                from .views import error_404
                return error_404(request, None)
            elif response.status_code == 500:
                from .views import error_500
                return error_500(request)

        return response



class NoCacheSocialMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Empêche la mise en cache pour les robots sociaux
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        social_bots = ['facebook', 'twitter', 'linkedin', 'whatsapp', 'telegram']

        if any(bot in user_agent for bot in social_bots):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response