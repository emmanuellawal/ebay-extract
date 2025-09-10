"""
eBay OAuth Authentication Module

This module handles OAuth token generation for eBay API access.
Supports both sandbox and production environments with token caching.
"""

import requests
import os
import time
import logging
from base64 import b64encode
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

class EbayAuth:
    """Handles eBay OAuth authentication with token caching."""
    
    def __init__(self, use_sandbox: bool = True):
        """
        Initialize eBay authentication.
        
        Args:
            use_sandbox: If True, use sandbox credentials; if False, use production
        """
        self.use_sandbox = use_sandbox
        self.token_cache: Dict[str, Any] = {}
        self.cache_duration = int(os.getenv("EBAY_TOKEN_CACHE_DURATION", "7200"))  # 2 hours default
        
        if use_sandbox:
            self.app_id = os.getenv("EBAY_SANDBOX_APP_ID")
            self.cert_id = os.getenv("EBAY_SANDBOX_CERT_ID")
            self.token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        else:
            self.app_id = os.getenv("EBAY_APP_ID")
            self.cert_id = os.getenv("EBAY_CERT_ID")
            self.token_url = "https://api.ebay.com/identity/v1/oauth2/token"
        
        if not self.app_id or not self.cert_id:
            env_type = "sandbox" if use_sandbox else "production"
            raise ValueError(f"eBay {env_type} credentials not found. Please set EBAY_{env_type.upper()}_APP_ID and EBAY_{env_type.upper()}_CERT_ID in your .env file.")
    
    def _is_token_valid(self) -> bool:
        """Check if cached token is still valid."""
        if not self.token_cache:
            return False
        
        current_time = time.time()
        token_time = self.token_cache.get('timestamp', 0)
        return (current_time - token_time) < self.cache_duration
    
    def _generate_credentials(self) -> str:
        """Generate base64 encoded credentials for OAuth."""
        credentials = f"{self.app_id}:{self.cert_id}"
        return b64encode(credentials.encode()).decode()
    
    def get_token(self) -> str:
        """
        Get a valid OAuth token, using cache if available.
        
        Returns:
            str: OAuth access token
            
        Raises:
            Exception: If token generation fails
        """
        # Check if we have a valid cached token
        if self._is_token_valid():
            logger.debug("Using cached eBay OAuth token")
            return self.token_cache['access_token']
        
        logger.info("Generating new eBay OAuth token")
        
        # Prepare OAuth request
        credentials = self._generate_credentials()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {credentials}"
        }
        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                
                if not access_token:
                    raise Exception("No access token in response")
                
                # Cache the token
                self.token_cache = {
                    'access_token': access_token,
                    'timestamp': time.time(),
                    'expires_in': token_data.get('expires_in', self.cache_duration)
                }
                
                logger.info("Successfully generated eBay OAuth token")
                return access_token
            else:
                error_msg = f"Token generation failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during token generation: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def clear_cache(self):
        """Clear the token cache to force a new token generation."""
        self.token_cache = {}
        logger.info("eBay OAuth token cache cleared")

# Global auth instance for easy access
_ebay_auth_instance: Optional[EbayAuth] = None

def get_ebay_auth(use_sandbox: bool = True) -> EbayAuth:
    """
    Get the global eBay auth instance.
    
    Args:
        use_sandbox: If True, use sandbox credentials; if False, use production
        
    Returns:
        EbayAuth: Configured authentication instance
    """
    global _ebay_auth_instance
    
    if _ebay_auth_instance is None or _ebay_auth_instance.use_sandbox != use_sandbox:
        _ebay_auth_instance = EbayAuth(use_sandbox=use_sandbox)
    
    return _ebay_auth_instance

def get_ebay_token(use_sandbox: bool = True) -> str:
    """
    Convenience function to get an eBay OAuth token.
    
    Args:
        use_sandbox: If True, use sandbox credentials; if False, use production
        
    Returns:
        str: OAuth access token
    """
    auth = get_ebay_auth(use_sandbox=use_sandbox)
    return auth.get_token()

# For backward compatibility
def get_ebay_token_legacy() -> str:
    """
    Legacy function for backward compatibility.
    Uses sandbox by default.
    """
    return get_ebay_token(use_sandbox=True)

