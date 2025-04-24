import pyotp
import datetime
import time
import re
import base64



class otp_gen:
    def __init__(self, secret, digits=6, name=None, issuer=None):
        # Clean the secret to handle various formats
        self.secret = self.clean_secret(secret)
        self.name = name
        self.issuer = issuer
        self.digits = digits
        self.ins = pyotp.TOTP(self.secret, self.digits, self.name, self.issuer)

    def clean_secret(self, secret):
        """
        Cleans a 2FA secret to handle various formats:
        - Google Authenticator (spaces every 4 chars)
        - Authy (hyphens)
        - Dashlane (with URI scheme)
        - Extracts from otpauth:// URLs
        - Handles secrets with pipe delimiters (UID|PASSWORD|SECRET|EMAIL)
        """
        # If it's empty or None, return as is
        if not secret:
            return secret
            
        # Extract secret from otpauth URI if present
        if secret.startswith('otpauth://'):
            try:
                # Try to extract the secret from the URI
                import urllib.parse
                parsed = urllib.parse.urlparse(secret)
                query_params = urllib.parse.parse_qs(parsed.query)
                if 'secret' in query_params:
                    secret = query_params['secret'][0]
            except Exception:
                # If parsing fails, continue with original secret
                pass
                
        # Handle pipe-delimited format (UID|PASSWORD|SECRET|EMAIL)
        if '|' in secret:
            parts = secret.split('|')
            if len(parts) >= 3:  # Assuming SECRET is the third part
                secret = parts[2]
                
        # Remove all whitespace, hyphens, and equals signs (common in various formats)
        secret = re.sub(r'[\s\-=]+', '', secret)
        
        # Convert to uppercase (Base32 is case insensitive, but convention is uppercase)
        secret = secret.upper()
        
        # Validate it's a proper Base32 string
        try:
            # Check if it contains only valid Base32 characters
            if not re.match(r'^[A-Z2-7]+$', secret):
                raise ValueError("Secret contains invalid Base32 characters")
                
            # Ensure the length is valid for Base32 (multiple of 8 characters or with proper padding)
            # This is a basic check to catch obvious errors
            if len(secret) % 8 != 0:
                # Add padding if needed (Base32 padding is with '=' chars)
                padding = 8 - (len(secret) % 8)
                secret += '=' * padding
                
            # Final validation by trying to decode it
            base64.b32decode(secret, casefold=True)
        except Exception as e:
            # If it's not valid Base32, we'll keep the clean version but log the error
            # We don't want to block the user's attempt completely
            print(f"Warning: Secret doesn't appear to be valid Base32: {e}")
            
        return secret

    def get_totp(self):
        return self.ins.now()

    def time_left(self):
        time_remaining = self.ins.interval - int(datetime.datetime.now().timestamp()) % self.ins.interval
        return time_remaining

