import httpx
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


@api_view(['POST'])
def smart_search(request):
    """NEW ENDPOINT: Smart search with RAG + DB integration"""
    from .services import ai_search_service

    try:
        prompt = request.data.get("prompt", "").strip()
        model_name = request.data.get("model")
        app_label = request.data.get("app", "search")

        if not prompt or not model_name:
            return Response({
                'success': False,
                'error': 'Prompt and model are required'
            }, status=400)

        results = ai_search_service.search(
            prompt=prompt,
            model_name=model_name,
            app_label=app_label
        )

        return Response({'success': True, **results})
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Smart search error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
def research_search(request):
    """NEW ENDPOINT: Direct search of Space Biology research papers"""
    try:
        query = request.data.get("query", "").strip()
        topk = request.data.get("topk", 5)

        if not query:
            return Response({
                'success': False,
                'error': 'Query is required'
            }, status=400)

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                'http://localhost:5000/search',
                json={"query": query, "topk": topk}
            )
            response.raise_for_status()
            result = response.json()

        return Response({'success': True, **result})
    except httpx.TimeoutException:
        logger.error("RAG service timeout")
        return Response({
            'success': False,
            'error': 'Search service took too long to respond'
        }, status=504)

    except httpx.HTTPStatusError as e:
        logger.error(f"RAG service HTTP error: {e.response.status_code}")
        return Response({
            'success': False,
            'error': f'Search service error: {e.response.status_code}'
        }, status=502)
    except Exception as e:
        logger.error(f"Research search error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint

    Checks if the RAG service is available and responding.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get('http://localhost:5000/health')
            if response.status_code == 200:
                rag_status = response.json()
                return Response({
                    'success': True,
                    'django': 'ok',
                    'rag_service': rag_status
                })
            else:
                return Response({
                    'success': False,
                    'django': 'ok',
                    'rag_service': 'unavailable'
                }, status=503)
    except Exception as e:
        return Response({
            'success': False,
            'django': 'ok',
            'rag_service': 'unavailable',
            'error': str(e)
        }, status=503)