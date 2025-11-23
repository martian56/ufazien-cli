"""
Ufazien API Client
Handles all API communication with the Ufazien platform.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


class UfazienAPIClient:
    """Client for interacting with the Ufazien API."""

    def __init__(self, base_url: Optional[str] = None, config_dir: Optional[str] = None):
        """
        Initialize the API client.

        Args:
            base_url: Base URL for the API (defaults to https://api.ufazien.com/api)
            config_dir: Directory to store config files (defaults to ~/.ufazien)
        """
        self.base_url = base_url or "https://api.ufazien.com/api"
        if not self.base_url.endswith('/api'):
            if self.base_url.endswith('/'):
                self.base_url = self.base_url.rstrip('/') + '/api'
            else:
                self.base_url = self.base_url + '/api'

        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            home = Path.home()
            self.config_dir = home / '.ufazien'

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / 'config.json'
        self.tokens_file = self.config_dir / 'tokens.json'

        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self._load_tokens()

    def _load_tokens(self) -> None:
        """Load tokens from file."""
        if self.tokens_file.exists():
            try:
                with open(self.tokens_file, 'r') as f:
                    tokens = json.load(f)
                    self.access_token = tokens.get('access_token')
                    self.refresh_token = tokens.get('refresh_token')
            except (json.JSONDecodeError, IOError):
                pass

    def _save_tokens(self, access_token: str, refresh_token: str) -> None:
        """Save tokens to file."""
        self.access_token = access_token
        self.refresh_token = refresh_token
        try:
            with open(self.tokens_file, 'w') as f:
                json.dump({
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }, f)
            os.chmod(self.tokens_file, 0o600)
        except IOError as e:
            print(f"Warning: Could not save tokens: {e}", file=sys.stderr)

    def _clear_tokens(self) -> None:
        """Clear tokens from memory and file."""
        self.access_token = None
        self.refresh_token = None
        if self.tokens_file.exists():
            try:
                self.tokens_file.unlink()
            except IOError:
                pass

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Any:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/auth/login/')
            data: Request data (for JSON requests)
            files: Files to upload (for multipart requests)
            headers: Additional headers

        Returns:
            Response data (parsed JSON or raw bytes)

        Raises:
            Exception: If the request fails
        """
        url = f"{self.base_url}{endpoint}"

        request_headers = {}
        if headers:
            request_headers.update(headers)

        if self.access_token:
            request_headers['Authorization'] = f'Bearer {self.access_token}'

        try:
            if files:
                # Multipart form data request
                file_data = {}
                for key, file_path in files.items():
                    if isinstance(file_path, str):
                        file_data[key] = ('file', open(file_path, 'rb'), 'application/octet-stream')
                    else:
                        file_data[key] = file_path

                response = requests.request(
                    method,
                    url,
                    data=data,
                    files=file_data,
                    headers=request_headers,
                    timeout=300  # 5 minutes for file uploads
                )

                # Close file handles
                for file_tuple in file_data.values():
                    if isinstance(file_tuple, tuple) and len(file_tuple) > 1:
                        file_obj = file_tuple[1]
                        if hasattr(file_obj, 'close'):
                            file_obj.close()
            else:
                # JSON request
                if data:
                    request_headers['Content-Type'] = 'application/json'

                response = requests.request(
                    method,
                    url,
                    json=data if data else None,
                    headers=request_headers,
                    timeout=30
                )

            response.raise_for_status()

            # Parse JSON response
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return response.json()
            else:
                return response.content

        except requests.exceptions.HTTPError as e:
            error_data = {}
            try:
                if e.response.content:
                    error_data = e.response.json()
            except (json.JSONDecodeError, AttributeError):
                pass

            # Handle 401 Unauthorized - try to refresh token
            if e.response.status_code == 401 and self.refresh_token and endpoint != '/auth/token/refresh/':
                if self._refresh_access_token():
                    return self._make_request(method, endpoint, data, files, headers)
                else:
                    self._clear_tokens()
                    raise Exception("Authentication failed. Please login again using 'ufazien login'")

            error_msg = error_data.get('detail', error_data.get('message', f'HTTP {e.response.status_code}: {e.response.reason}'))
            if isinstance(error_msg, dict):
                error_msg = json.dumps(error_msg, indent=2)
            raise Exception(error_msg)

        except requests.exceptions.RequestException as e:
            raise Exception(f"Connection error: {str(e)}")

    def _refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        if not self.refresh_token:
            return False

        try:
            url = f"{self.base_url}/auth/token/refresh/"
            response = requests.post(
                url,
                json={'refresh': self.refresh_token},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            response_data = response.json()
            new_access_token = response_data.get('access')

            if new_access_token:
                self._save_tokens(new_access_token, self.refresh_token)
                return True

            return False

        except Exception:
            return False

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login and store tokens.

        Args:
            email: User email
            password: User password

        Returns:
            User data dict
        """
        response = self._make_request('POST', '/auth/login/', {
            'email': email,
            'password': password
        })

        if 'access' in response and 'refresh' in response:
            self._save_tokens(response['access'], response['refresh'])

        return response.get('user', {})

    def logout(self) -> None:
        """Logout and clear tokens."""
        try:
            if self.access_token:
                self._make_request('POST', '/auth/logout/')
        except Exception:
            pass
        finally:
            self._clear_tokens()

    def get_profile(self) -> Dict[str, Any]:
        """Get current user profile."""
        return self._make_request('GET', '/auth/user/')

    def create_website(
        self,
        name: str,
        subdomain: str,
        website_type: str,
        description: Optional[str] = None,
        environment_variables: Optional[Dict[str, str]] = None,
        domain_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new website.

        Args:
            name: Website name
            subdomain: Subdomain (without .ufazien.com)
            website_type: 'static' or 'php'
            description: Optional description
            environment_variables: Optional dict of environment variables
            domain_id: Optional existing domain ID

        Returns:
            Created website data
        """
        data: Dict[str, Any] = {
            'name': name,
            'website_type': website_type,
        }

        if description:
            data['description'] = description

        if environment_variables:
            data['environment_variables'] = environment_variables

        if domain_id:
            data['domain_id'] = domain_id
        else:
            domain_data = {
                'name': f'{subdomain}.ufazien.com',
                'domain_type': 'subdomain'
            }
            domain = self._make_request('POST', '/hosting/domains/', domain_data)
            data['domain_id'] = domain['id']

        return self._make_request('POST', '/hosting/websites/', data)

    def create_database(
        self,
        name: str,
        db_type: str = 'mysql',
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new database.

        Args:
            name: Database name
            db_type: 'mysql' or 'postgresql'
            description: Optional description

        Returns:
            Created database data with credentials
        """
        data = {
            'name': name,
            'db_type': db_type,
        }

        if description:
            data['description'] = description

        return self._make_request('POST', '/hosting/databases/', data)

    def upload_zip(self, website_id: str, zip_file_path: str) -> Dict[str, Any]:
        """
        Upload and extract a ZIP file to a website.

        Args:
            website_id: Website ID
            zip_file_path: Path to ZIP file

        Returns:
            Upload response
        """
        return self._make_request(
            'POST',
            f'/hosting/websites/{website_id}/upload_zip/',
            files={'zip_file': zip_file_path}
        )

    def get_websites(self) -> List[Dict[str, Any]]:
        """Get list of user's websites."""
        return self._make_request('GET', '/hosting/websites/')

    def get_website(self, website_id: str) -> Dict[str, Any]:
        """Get website details."""
        return self._make_request('GET', f'/hosting/websites/{website_id}/')

    def deploy_website(self, website_id: str) -> Dict[str, Any]:
        """Trigger a website deployment."""
        return self._make_request('POST', f'/hosting/websites/{website_id}/deploy/')

    def get_available_domains(self) -> List[Dict[str, Any]]:
        """Get list of available domains."""
        return self._make_request('GET', '/hosting/domains/available/')

    def get_database(self, database_id: str) -> Dict[str, Any]:
        """Get database details."""
        return self._make_request('GET', f'/hosting/databases/{database_id}/')

