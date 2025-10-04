from .ai_client import AIClient
from .query_builder import QueryBuilder
from django.apps import apps
import logging

logger = logging.getLogger(__name__)


class AISearchService:
    """Main service for AI-powered database search"""

    def __init__(self):
        self.ai_client = AIClient()

    def search(self, prompt: str, model_name: str, app_label: str = 'search'):
        """
        Perform AI-powered search

        Args:
            prompt: User's natural language search query
            model_name: Django model name to search
            app_label: Django app label

        Returns:
            Dict with results, count, search_params, and query
        """
        try:
            model_class = apps.get_model(app_label, model_name)
        except LookupError:
            raise ValueError(f"Model {app_label}.{model_name} not found")

        schema = self._get_model_schema(model_class)
        search_params = self.ai_client.interpret_search_prompt(prompt, schema)

        query_builder = QueryBuilder(model_class)
        queryset = query_builder.build_query(search_params)

        results = list(queryset.values())

        return {
            'results': results,
            'count': len(results),
            'search_params': search_params,
            'query': prompt
        }

    def _get_model_schema(self, model_class) -> dict:
        """Extract schema information from Django model"""
        fields = []
        for field in model_class._meta.get_fields():
            if field.concrete:
                fields.append({
                    'name': field.name,
                    'type': field.get_internal_type(),
                    'description': getattr(field, 'help_text', '')
                })

        return {
            'model': model_class.__name__,
            'fields': fields
        }