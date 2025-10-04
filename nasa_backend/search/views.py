from rest_framework.decorators import api_view
from rest_framework.response import Response
import logging
from .services import ai_search_service

logger = logging.getLogger(__name__)


@api_view(['POST'])
def search(request):
    """
    AI-powered search endpoint

    Request body:
    {
        "prompt": "find all products under $100",
        "model": "Product",
        "app": "search",  // optional
        "token": "auth_token"  // optional
    }
    """
    try:
        prompt = request.data.get("prompt", "").strip()
        model_name = request.data.get("model")
        app_label = request.data.get("app", "search")
        token = request.data.get("token", "")

        # Validation
        if not prompt:
            return Response({
                'success': False,
                'error': 'Prompt is required'
            }, status=400)

        if not model_name:
            return Response({
                'success': False,
                'error': 'Model name is required'
            }, status=400)

        # TODO: Add token validation if needed
        # if token and not validate_token(token):
        #     return Response({'error': 'Invalid token'}, status=401)

        # Execute AI search
        logger.info(f"Search request: {prompt} on {app_label}.{model_name}")
        results = ai_search_service.search(
            prompt=prompt,
            model_name=model_name,
            app_label=app_label
        )

        return Response({
            'success': True,
            **results
        })

    except ValueError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)

    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Internal server error',
            'details': str(e)
        }, status=500)