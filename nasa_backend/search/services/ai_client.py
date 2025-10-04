import httpx
import json
import logging

logger = logging.getLogger(__name__)


class AIClient:
    """Handles communication with local AI service"""

    def __init__(self):
        self.ai_service_url = 'http://localhost:5000/run_ai'
        self.timeout = 60.0  # 60 seconds for AI processing

    def interpret_search_prompt(self, prompt: str, schema: dict) -> dict:
        """
        Send prompt to local AI and get structured search parameters

        Args:
            prompt: User's natural language search query as Python string
            schema: Database schema information for context

        Returns:
            Structured search parameters as dict
        """
        # Build the instruction for the AI
        ai_instruction = self._build_ai_instruction(prompt, schema)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                # Send as plain text/string to your AI service
                response = client.post(
                    self.ai_service_url,
                    content=ai_instruction.encode('utf-8'),
                    headers={'Content-Type': 'text/plain'}
                )
                response.raise_for_status()

                # Get AI response
                ai_response_text = response.text
                logger.info(f"AI Response: {ai_response_text}")

                # Parse JSON from AI response
                search_params = self._parse_ai_response(ai_response_text, prompt)

                return search_params

        except httpx.TimeoutException:
            logger.error(f"AI service timeout after {self.timeout}s")
            # Fallback to basic search
            return self._create_fallback_params(prompt)

        except httpx.HTTPStatusError as e:
            logger.error(f"AI service HTTP error: {e.response.status_code}")
            return self._create_fallback_params(prompt)

        except Exception as e:
            logger.error(f"AI communication error: {str(e)}", exc_info=True)
            return self._create_fallback_params(prompt)

    def _build_ai_instruction(self, prompt: str, schema: dict) -> str:
        """Build instruction string for the AI"""

        # Extract field information
        fields_list = []
        for field in schema.get('fields', []):
            field_type = field['type']
            field_name = field['name']
            field_desc = field.get('description', '')
            fields_list.append(f"{field_name} ({field_type}): {field_desc}")

        fields_text = "\n".join(fields_list)

        instruction = f"""You are a database search query interpreter.

DATABASE SCHEMA:
Model: {schema.get('model', 'Unknown')}
Fields:
{fields_text}

USER SEARCH QUERY:
{prompt}

YOUR TASK:
Convert the user's query into a JSON object with these fields:
- filters: dict of field filters using Django ORM lookups (e.g., {{"price__lte": 100, "name__icontains": "test"}})
- search_terms: list of keywords to search across text fields
- sort_by: field name to sort by (or null)
- sort_order: "asc" or "desc"
- limit: maximum number of results (default 50)

AVAILABLE DJANGO ORM LOOKUPS:
- exact: exact match
- iexact: case-insensitive exact match
- contains/icontains: contains substring
- gt/gte/lt/lte: greater than, greater or equal, less than, less or equal
- startswith/endswith: string starts/ends with
- in: value in list
- isnull: is null (true/false)

RESPONSE FORMAT:
Return ONLY valid JSON, no other text. Example:
{{"filters": {{"category__iexact": "electronics", "price__lt": 500}}, "search_terms": ["laptop"], "sort_by": "price", "sort_order": "asc", "limit": 50}}

Now convert the user query above into the JSON format.
"""

        return instruction

    def _parse_ai_response(self, ai_response: str, original_prompt: str) -> dict:
        """Parse the AI's response into search parameters"""
        try:
            # Try to extract JSON from response
            # Sometimes AI might include extra text, so we try to find JSON
            response_text = ai_response.strip()

            # Try direct parsing first
            try:
                search_params = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    search_params = json.loads(json_match.group())
                else:
                    raise ValueError("No JSON found in AI response")

            # Validate and set defaults
            search_params.setdefault('filters', {})
            search_params.setdefault('search_terms', [])
            search_params.setdefault('sort_by', None)
            search_params.setdefault('sort_order', 'asc')
            search_params.setdefault('limit', 50)

            logger.info(f"Successfully parsed AI response: {search_params}")
            return search_params

        except Exception as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
            logger.error(f"AI Response was: {ai_response}")
            return self._create_fallback_params(original_prompt)

    def _create_fallback_params(self, prompt: str) -> dict:
        """Create basic search parameters when AI fails"""
        logger.warning(f"Using fallback search for: {prompt}")

        # Extract potential keywords
        words = prompt.lower().split()
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'find', 'show', 'get', 'all'}
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return {
            'filters': {},
            'search_terms': keywords[:5],  # Limit to 5 keywords
            'sort_by': None,
            'sort_order': 'asc',
            'limit': 50
        }