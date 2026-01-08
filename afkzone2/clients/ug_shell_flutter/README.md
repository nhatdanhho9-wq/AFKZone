# AFKZone UG Shell (Flutter) - MVP

This is a clean, standalone Flutter client that renders the UG-phone tabs **from server config**:

- Device / Discover / Purchase / Me

Config endpoint:

- `GET /public/mobile-ui-config`

## Run (dev)

Point backend to `localhost:8081` and run Flutter:

```bash
flutter pub get
flutter run -d android
```

## Notes

- The client caches the last-known-good config in `shared_preferences`.
- Signature verification is implemented (Ed25519). For dev, pass the public key via `--dart-define`:

```bash
# 1) Generate seed (backend)
python afkzone2/backend/tools/generate_dev_signing_seed.py

# 2) Derive public key (backend)
python afkzone2/backend/tools/print_public_key_from_seed.py <seed_b64>

# 3) Run client with public key pinned at build-time
flutter run -d android --dart-define=AFK_UI_KEY_ID=dev-key --dart-define=AFK_UI_PUBKEY_B64=<pubkey_b64>
```

