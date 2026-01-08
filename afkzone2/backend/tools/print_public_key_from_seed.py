import base64
import sys

import nacl.signing


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python print_public_key_from_seed.py <seed_b64>", file=sys.stderr)
        raise SystemExit(2)
    seed_b64 = sys.argv[1]
    seed = base64.b64decode(seed_b64)
    if len(seed) != 32:
        print("Seed must decode to 32 bytes", file=sys.stderr)
        raise SystemExit(2)
    sk = nacl.signing.SigningKey(seed)
    pk = sk.verify_key.encode()
    print(base64.b64encode(pk).decode("ascii"))


if __name__ == "__main__":
    main()

