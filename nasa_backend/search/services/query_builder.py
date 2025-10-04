from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


class QueryBuilder:
    """Builds Django ORM queries from AI-interpreted parameters"""

    def __init__(self, model_class):
        self.model = model_class

    def build_query(self, search_params: dict):
        """Build and execute Django ORM query"""
        queryset = self.model.objects.all()

        queryset = self._apply_filters(queryset, search_params.get('filters', {}))
        queryset = self._apply_text_search(queryset, search_params.get('search_terms', []))
        queryset = self._apply_sorting(
            queryset,
            search_params.get('sort_by'),
            search_params.get('sort_order', 'asc')
        )

        limit = search_params.get('limit', 50)
        return queryset[:limit]

    def _apply_filters(self, queryset, filters: dict):
        """Apply exact filters to queryset"""
        if not filters:
            return queryset

        valid_filters = {}
        for key, value in filters.items():
            field_name = key.split('__')[0]
            if hasattr(self.model, field_name):
                valid_filters[key] = value
            else:
                logger.warning(f"Invalid filter field: {field_name}")

        return queryset.filter(**valid_filters) if valid_filters else queryset

    def _apply_text_search(self, queryset, search_terms: list):
        """Apply text search across searchable fields"""
        if not search_terms:
            return queryset

        searchable_fields = self._get_searchable_fields()

        q_objects = Q()
        for term in search_terms:
            term_q = Q()
            for field in searchable_fields:
                term_q |= Q(**{f"{field}__icontains": term})
            q_objects &= term_q

        return queryset.filter(q_objects)

    def _apply_sorting(self, queryset, sort_by: str, sort_order: str):
        """Apply sorting to queryset"""
        if not sort_by:
            return queryset

        if not hasattr(self.model, sort_by):
            logger.warning(f"Invalid sort field: {sort_by}")
            return queryset

        prefix = '-' if sort_order == 'desc' else ''
        return queryset.order_by(f'{prefix}{sort_by}')

    def _get_searchable_fields(self):
        """Get list of text fields that can be searched"""
        searchable = []
        for field in self.model._meta.get_fields():
            if field.get_internal_type() in ['CharField', 'TextField']:
                searchable.append(field.name)
        return searchable