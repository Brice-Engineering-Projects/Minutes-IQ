"""
minutes_iq/db/keyword_service.py
---------------------------------------------

Service layer for keyword management.
Provides business logic, validation, and search functionality.
"""

from typing import Any

from minutes_iq.db.keyword_repository import KeywordRepository


class KeywordService:
    """Service for managing keywords with business logic and validation."""

    def __init__(self, keyword_repo: KeywordRepository):
        """
        Initialize the service with required repositories.

        Args:
            keyword_repo: Keyword repository
        """
        self.keyword_repo = keyword_repo

    def create_keyword(
        self,
        keyword: str,
        created_by: int,
        category: str | None = None,
        description: str | None = None,
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """
        Create a new keyword with validation.

        Args:
            keyword: The keyword/phrase
            created_by: User ID of admin creating the keyword
            category: Optional category (e.g., "Infrastructure", "Budget")
            description: Optional description

        Returns:
            Tuple of (success, error_message, keyword_data)
        """
        # Validate keyword
        keyword = keyword.strip()
        if not keyword:
            return False, "Keyword cannot be empty", None
        if len(keyword) < 2:
            return False, "Keyword must be at least 2 characters", None
        if len(keyword) > 100:
            return False, "Keyword cannot exceed 100 characters", None

        # Validate category if provided
        if category is not None:
            category = category.strip()
            if len(category) > 50:
                return False, "Category cannot exceed 50 characters", None

        # Validate description if provided
        if description is not None:
            description = description.strip()
            if len(description) > 500:
                return False, "Description cannot exceed 500 characters", None

        # Check if keyword already exists
        existing = self.keyword_repo.get_keyword_by_text(keyword)
        if existing:
            return False, f"Keyword '{keyword}' already exists", None

        # Create keyword
        try:
            keyword_data = self.keyword_repo.create_keyword(
                keyword=keyword,
                created_by=created_by,
                category=category if category else None,
                description=description if description else None,
            )
            return True, None, keyword_data
        except ValueError as e:
            return False, str(e), None
        except Exception as e:
            return False, f"Failed to create keyword: {str(e)}", None

    def get_keyword(self, keyword_id: int) -> dict[str, Any] | None:
        """
        Get a keyword by ID.

        Args:
            keyword_id: Keyword ID

        Returns:
            Dictionary containing keyword data, or None if not found
        """
        return self.keyword_repo.get_keyword_by_id(keyword_id)

    def list_keywords(
        self,
        is_active: bool | None = None,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        List keywords with optional filtering.

        Args:
            is_active: Filter by active status (None = all keywords)
            category: Filter by category (None = all categories)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (keywords_list, total_count)
        """
        keywords = self.keyword_repo.list_keywords(
            is_active=is_active, category=category, limit=limit, offset=offset
        )
        total_count = self.keyword_repo.get_keyword_count(
            is_active=is_active, category=category
        )
        return keywords, total_count

    def search_keywords(
        self, search_text: str, is_active: bool = True, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Search for keywords by partial text match.

        Args:
            search_text: Text to search for in keyword field
            is_active: Only return active keywords
            limit: Maximum number of results

        Returns:
            List of matching keywords
        """
        search_text = search_text.strip().lower()
        if not search_text:
            return []

        # Get all keywords and filter in memory (simple implementation)
        # For larger datasets, this should be done in the database
        keywords = self.keyword_repo.list_keywords(is_active=is_active, limit=1000)

        # Filter by partial match
        matches = [kw for kw in keywords if search_text in kw["keyword"].lower()]

        return matches[:limit]

    def update_keyword(
        self,
        keyword_id: int,
        keyword: str | None = None,
        category: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """
        Update a keyword's information with validation.

        Args:
            keyword_id: Keyword ID
            keyword: New keyword text (optional)
            category: New category (optional)
            description: New description (optional)
            is_active: New active status (optional)

        Returns:
            Tuple of (success, error_message, keyword_data)
        """
        # Validate keyword if provided
        if keyword is not None:
            keyword = keyword.strip()
            if not keyword:
                return False, "Keyword cannot be empty", None
            if len(keyword) < 2:
                return False, "Keyword must be at least 2 characters", None
            if len(keyword) > 100:
                return False, "Keyword cannot exceed 100 characters", None

            # Check if new keyword conflicts with another entry
            existing = self.keyword_repo.get_keyword_by_text(keyword)
            if existing and existing["keyword_id"] != keyword_id:
                return False, f"Keyword '{keyword}' already exists", None

        # Validate category if provided
        if category is not None:
            category = category.strip()
            if len(category) > 50:
                return False, "Category cannot exceed 50 characters", None

        # Validate description if provided
        if description is not None:
            description = description.strip()
            if len(description) > 500:
                return False, "Description cannot exceed 500 characters", None

        # Update keyword
        try:
            keyword_data = self.keyword_repo.update_keyword(
                keyword_id=keyword_id,
                keyword=keyword if keyword else None,
                category=category if category else None,
                description=description if description else None,
                is_active=is_active,
            )
            if not keyword_data:
                return False, "Keyword not found", None
            return True, None, keyword_data
        except ValueError as e:
            return False, str(e), None
        except Exception as e:
            return False, f"Failed to update keyword: {str(e)}", None

    def delete_keyword(self, keyword_id: int) -> tuple[bool, str | None]:
        """
        Delete a keyword (soft delete).

        Args:
            keyword_id: Keyword ID

        Returns:
            Tuple of (success, error_message)
        """
        success = self.keyword_repo.delete_keyword(keyword_id)
        if not success:
            return False, "Keyword not found"
        return True, None

    def get_keyword_usage(
        self, keyword_id: int
    ) -> tuple[bool, str | None, list[dict[str, Any]] | None]:
        """
        Get all clients using a specific keyword.

        Args:
            keyword_id: Keyword ID

        Returns:
            Tuple of (success, error_message, clients_list)
        """
        # Verify keyword exists
        keyword = self.keyword_repo.get_keyword_by_id(keyword_id)
        if not keyword:
            return False, "Keyword not found", None

        clients = self.keyword_repo.get_keyword_clients(keyword_id)
        return True, None, clients

    def get_categories(self) -> list[str]:
        """
        Get all unique keyword categories.

        Returns:
            List of category names
        """
        # Get all keywords and extract unique categories
        keywords = self.keyword_repo.list_keywords(limit=1000)
        categories = {kw["category"] for kw in keywords if kw["category"] is not None}
        return sorted(categories)

    def suggest_keywords(self, text: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Suggest keywords based on input text (autocomplete).

        Args:
            text: User input text
            limit: Maximum number of suggestions

        Returns:
            List of keyword suggestions
        """
        text = text.strip().lower()
        if not text:
            return []

        # Get active keywords that start with the input text
        keywords = self.keyword_repo.list_keywords(is_active=True, limit=1000)

        # Prioritize keywords that start with the text
        starts_with = [kw for kw in keywords if kw["keyword"].lower().startswith(text)]
        contains = [
            kw
            for kw in keywords
            if text in kw["keyword"].lower() and kw not in starts_with
        ]

        # Combine and limit results
        suggestions = starts_with + contains
        return suggestions[:limit]
