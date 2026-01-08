"""
Generate Ed25519 public key from seed for Sonnet/OpusC to verify signatures.
"""
import base64
import nacl.signing

# Dev seed (matches AFK_SIGNING_SEED_B64 in ENV)
# This is a 32-byte zero seed for dev/testing only
DEV_SEED_B64 = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
KEY_ID = "dev-key"

def main():
    seed_bytes = base64.b64decode(DEV_SEED_B64)
    signing_key = nacl.signing.SigningKey(seed_bytes)
    verify_key = signing_key.verify_key
    public_key_b64 = base64.b64encode(bytes(verify_key)).decode()
    
    print("=" * 60)
    print("AFKZone vNext - Dev Signing Key")
    print("=" * 60)
    print()
    print(f"key_id: {KEY_ID}")
    print(f"public_key_base64: {public_key_b64}")
    print()
    print("Copy this to client config for signature verification:")
    print()
    print(f'''{{
  "signing_keys": {{
    "{KEY_ID}": "{public_key_b64}"
  }}
}}''')
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()
