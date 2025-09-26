"""
Custom middleware for the core app
"""

from django.conf import settings


class PermissionsPolicyMiddleware:
    """
    Middleware to set Permissions-Policy header to fix browser console warnings
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Set Permissions-Policy header if configured
        if hasattr(settings, 'PERMISSIONS_POLICY'):
            policy_parts = []
            for feature, allowlist in settings.PERMISSIONS_POLICY.items():
                if allowlist == "*":
                    policy_parts.append(f"{feature}=*")
                elif allowlist:
                    policy_parts.append(f"{feature}=({' '.join(allowlist)})")
                else:
                    policy_parts.append(f"{feature}=()")
            
            if policy_parts:
                response['Permissions-Policy'] = ', '.join(policy_parts)
        
        return response
