from django.contrib.sites.models import Site
from django.conf import settings

class DynamicSiteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            current_host = request.get_host()
            site = Site.objects.filter(id=settings.SITE_ID).first()
            if site and site.domain != current_host:
                site.domain = current_host
                site.save()
        except Exception:
            pass
        return self.get_response(request)
