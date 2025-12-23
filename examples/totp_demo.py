"""
Example demonstrating TOTP (Two-Factor Authentication) utilities.

This script shows how to:
1. Generate a TOTP secret
2. Create an otpauth:// URI
3. Verify TOTP codes
4. Format secrets for display

Note: This is for demonstration purposes only.
In production, secret generation should be done server-side.
"""

import pyotp
from src.include.util.twofa import (
    verify_totp_code,
    generate_totp_uri,
    get_current_totp_code,
    format_secret_for_display,
)


def demo_totp_flow():
    """Demonstrate a complete TOTP setup and verification flow."""
    
    print("=" * 60)
    print("TOTP Two-Factor Authentication Demo")
    print("=" * 60)
    
    # Step 1: Generate a random secret (normally done by server)
    secret = pyotp.random_base32()
    print(f"\n1. Generated secret (base32): {secret}")
    print(f"   Formatted for display: {format_secret_for_display(secret)}")
    
    # Step 2: Generate otpauth:// URI for QR code
    username = "demo_user"
    uri = generate_totp_uri(secret, username, issuer="CFMS")
    print(f"\n2. Generated otpauth:// URI for QR code:")
    print(f"   {uri}")
    print(f"   (User would scan this as a QR code with their authenticator app)")
    
    # Step 3: Generate current TOTP code
    current_code = get_current_totp_code(secret)
    print(f"\n3. Current TOTP code: {current_code}")
    print(f"   (This is what the authenticator app would show)")
    
    # Step 4: Verify the code
    is_valid = verify_totp_code(secret, current_code)
    print(f"\n4. Verification result: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    # Step 5: Test with invalid code
    invalid_code = "000000"
    is_valid_invalid = verify_totp_code(secret, invalid_code)
    print(f"\n5. Testing invalid code '{invalid_code}':")
    print(f"   Verification result: {'✓ Valid' if is_valid_invalid else '✗ Invalid'}")
    
    # Step 6: Show time-based nature
    print(f"\n6. Time-based codes (changes every 30 seconds):")
    totp = pyotp.TOTP(secret)
    for i in range(3):
        code = totp.at(totp.timecode(for_time=None) + i)
        time_offset = i * 30
        print(f"   Code in +{time_offset}s: {code}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo_totp_flow()
