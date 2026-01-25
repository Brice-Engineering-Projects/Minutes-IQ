"""
jea_meeting_web_scraper/db/client_service.py
--------------------------------------------

Service layer for client management.
Provides business logic, validation, and orchestration between repositories.
"""

from typing import Any

from jea_meeting_web_scraper.db.client_repository import ClientRepository
from jea_meeting_web_scraper.db.keyword_repository import KeywordRepository


class ClientService:
    """Service for managing clients with business logic and validation."""

    def __init__(self, client_repo: ClientRepository, keyword_repo: KeywordRepository):
        """
        Initialize the service with required repositories.

        Args:
            client_repo: Client repository
            keyword_repo: Keyword repository
        """
        self.client_repo = client_repo
        self.keyword_repo = keyword_repo

    def create_client(
        self,
        name: str,
        created_by: int,
        description: str | None = None,
        website_url: str | None = None,
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """
        Create a new client with validation.

        Args:
            name: Client organization name
            created_by: User ID of admin creating the client
            description: Optional description
            website_url: Optional official website

        Returns:
            Tuple of (success, error_message, client_data)
        """
        # Validate name
        name = name.strip()
        if not name:
            return False, "Client name cannot be empty", None
        if len(name) < 3:
            return False, "Client name must be at least 3 characters", None
        if len(name) > 200:
            return False, "Client name cannot exceed 200 characters", None

        # Validate description if provided
        if description is not None:
            description = description.strip()
            if len(description) > 1000:
                return False, "Description cannot exceed 1000 characters", None

        # Validate website URL if provided
        if website_url is not None:
            website_url = website_url.strip()
            if website_url and not (
                website_url.startswith("http://") or website_url.startswith("https://")
            ):
                return False, "Website URL must start with http:// or https://", None
            if len(website_url) > 500:
                return False, "Website URL cannot exceed 500 characters", None

        # Check if client already exists
        existing = self.client_repo.get_client_by_name(name)
        if existing:
            return False, f"Client '{name}' already exists", None

        # Create client
        try:
            client = self.client_repo.create_client(
                name=name,
                created_by=created_by,
                description=description if description else None,
                website_url=website_url if website_url else None,
            )
            return True, None, client
        except ValueError as e:
            return False, str(e), None
        except Exception as e:
            return False, f"Failed to create client: {str(e)}", None

    def get_client(self, client_id: int) -> dict[str, Any] | None:
        """
        Get a client by ID with its keywords.

        Args:
            client_id: Client ID

        Returns:
            Dictionary containing client data with keywords, or None if not found
        """
        client = self.client_repo.get_client_by_id(client_id)
        if not client:
            return None

        # Enrich with keywords
        keywords = self.keyword_repo.get_client_keywords(client_id)
        client["keywords"] = keywords

        return client

    def list_clients(
        self,
        is_active: bool | None = None,
        include_keywords: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        List clients with optional filtering.

        Args:
            is_active: Filter by active status (None = all clients)
            include_keywords: Include associated keywords for each client
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (clients_list, total_count)
        """
        clients = self.client_repo.list_clients(
            is_active=is_active, limit=limit, offset=offset
        )
        total_count = self.client_repo.get_client_count(is_active=is_active)

        # Optionally enrich with keywords
        if include_keywords:
            for client in clients:
                keywords = self.keyword_repo.get_client_keywords(client["client_id"])
                client["keywords"] = keywords

        return clients, total_count

    def update_client(
        self,
        client_id: int,
        name: str | None = None,
        description: str | None = None,
        website_url: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """
        Update a client's information with validation.

        Args:
            client_id: Client ID
            name: New name (optional)
            description: New description (optional)
            website_url: New website URL (optional)
            is_active: New active status (optional)

        Returns:
            Tuple of (success, error_message, client_data)
        """
        # Validate name if provided
        if name is not None:
            name = name.strip()
            if not name:
                return False, "Client name cannot be empty", None
            if len(name) < 3:
                return False, "Client name must be at least 3 characters", None
            if len(name) > 200:
                return False, "Client name cannot exceed 200 characters", None

            # Check if new name conflicts with another client
            existing = self.client_repo.get_client_by_name(name)
            if existing and existing["client_id"] != client_id:
                return False, f"Client '{name}' already exists", None

        # Validate description if provided
        if description is not None:
            description = description.strip()
            if len(description) > 1000:
                return False, "Description cannot exceed 1000 characters", None

        # Validate website URL if provided
        if website_url is not None:
            website_url = website_url.strip()
            if website_url and not (
                website_url.startswith("http://") or website_url.startswith("https://")
            ):
                return False, "Website URL must start with http:// or https://", None
            if len(website_url) > 500:
                return False, "Website URL cannot exceed 500 characters", None

        # Update client
        try:
            client = self.client_repo.update_client(
                client_id=client_id,
                name=name if name else None,
                description=description if description else None,
                website_url=website_url if website_url else None,
                is_active=is_active,
            )
            if not client:
                return False, "Client not found", None
            return True, None, client
        except ValueError as e:
            return False, str(e), None
        except Exception as e:
            return False, f"Failed to update client: {str(e)}", None

    def delete_client(self, client_id: int) -> tuple[bool, str | None]:
        """
        Delete a client (soft delete).

        Args:
            client_id: Client ID

        Returns:
            Tuple of (success, error_message)
        """
        success = self.client_repo.delete_client(client_id)
        if not success:
            return False, "Client not found"
        return True, None

    def add_keyword_to_client(
        self, client_id: int, keyword_id: int, added_by: int
    ) -> tuple[bool, str | None]:
        """
        Associate a keyword with a client.

        Args:
            client_id: Client ID
            keyword_id: Keyword ID
            added_by: User ID of admin adding the association

        Returns:
            Tuple of (success, error_message)
        """
        # Verify client exists and is active
        client = self.client_repo.get_client_by_id(client_id)
        if not client:
            return False, "Client not found"
        if not client["is_active"]:
            return False, "Cannot add keywords to inactive client"

        # Verify keyword exists and is active
        keyword = self.keyword_repo.get_keyword_by_id(keyword_id)
        if not keyword:
            return False, "Keyword not found"
        if not keyword["is_active"]:
            return False, "Cannot add inactive keyword to client"

        # Add association
        try:
            success = self.keyword_repo.add_keyword_to_client(
                client_id, keyword_id, added_by
            )
            if not success:
                return False, "Keyword is already associated with this client"
            return True, None
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Failed to add keyword to client: {str(e)}"

    def remove_keyword_from_client(
        self, client_id: int, keyword_id: int
    ) -> tuple[bool, str | None]:
        """
        Remove keyword association from a client.

        Args:
            client_id: Client ID
            keyword_id: Keyword ID

        Returns:
            Tuple of (success, error_message)
        """
        success = self.keyword_repo.remove_keyword_from_client(client_id, keyword_id)
        if not success:
            return False, "Keyword is not associated with this client"
        return True, None

    def get_client_keywords(
        self, client_id: int
    ) -> tuple[bool, str | None, list[dict[str, Any]] | None]:
        """
        Get all keywords associated with a client.

        Args:
            client_id: Client ID

        Returns:
            Tuple of (success, error_message, keywords_list)
        """
        # Verify client exists
        client = self.client_repo.get_client_by_id(client_id)
        if not client:
            return False, "Client not found", None

        keywords = self.keyword_repo.get_client_keywords(client_id)
        return True, None, keywords
