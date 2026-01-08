"""
Create QA Pack seed config via Admin API.
"""
import json
import requests

BASE = "http://127.0.0.1:8888"
AUTH = ("admin", "test123")

# QA Pack config with required actions
QA_PACK_PAYLOAD = {
    "schema_version": 1,
    "ttl_seconds": 300,
    "kill_switch": False,
    "tabs": [
        {"id": "device", "label": "Device", "icon": "tab_device", "visible": True, "route_type": "tab_device"},
        {"id": "discover", "label": "Discover", "icon": "tab_discover", "visible": True, "route_type": "tab_discover"},
        {"id": "purchase", "label": "Purchase", "icon": "tab_purchase", "visible": True, "route_type": "tab_purchase"},
        {"id": "me", "label": "Me", "icon": "tab_me", "visible": True, "route_type": "tab_me"}
    ],
    "routes": [
        {"id": "screen_orders", "route_type": "screen_orders"},
        {"id": "screen_net_check", "route_type": "screen_net_check"},
        {"id": "screen_user_guide", "route_type": "screen_user_guide"},
        {"id": "screen_webview", "route_type": "screen_webview"}
    ],
    "actions": [
        # Device quick actions
        {"id": "open_recent", "label": "Recent", "icon": "icon_recent", "action_key": "open_recent"},
        {"id": "open_favorites", "label": "Favorites", "icon": "icon_star", "action_key": "open_favorites"},
        {"id": "open_contacts", "label": "Contacts", "icon": "icon_contacts", "action_key": "open_contacts"},
        {"id": "share_screen_start", "label": "Share Screen", "icon": "icon_share", "action_key": "share_screen_start"},
        {"id": "scan_qr", "label": "Scan QR", "icon": "icon_qr", "action_key": "scan_qr"},
        # Me menu actions
        {"id": "open_orders", "label": "Orders", "icon": "icon_orders", "action_key": "open_orders"},
        {"id": "net_check", "label": "Net Check", "icon": "icon_network", "action_key": "net_check"},
        {"id": "user_guide", "label": "User Guide", "icon": "icon_guide", "action_key": "open_webview", "params": {"url": "https://afkzone.cloud/guide"}},
        {"id": "redeem_code", "label": "Redeem Code", "icon": "icon_gift", "action_key": "redeem_code"},
        # Auth actions
        {"id": "auth_login", "label": "Login", "icon": "icon_login", "action_key": "auth_login"},
        {"id": "auth_logout", "label": "Logout", "icon": "icon_logout", "action_key": "auth_logout"},
        {"id": "oauth_google", "label": "Google Login", "icon": "icon_google", "action_key": "oauth_google_login"},
        # Purchase actions
        {"id": "select_region", "label": "Select Region", "icon": "icon_globe", "action_key": "select_region"},
        {"id": "buy_plan", "label": "Buy Plan", "icon": "icon_cart", "action_key": "buy_plan"},
        # Discover card actions
        {"id": "news_1", "label": "News Link", "icon": "icon_news", "action_key": "open_webview", "params": {"url": "https://afkzone.cloud/news/1"}}
    ],
    "content": {
        "device": {
            "quick_action_ids": ["open_recent", "open_favorites", "share_screen_start", "scan_qr"]
        },
        "discover": {
            "sections": [
                {
                    "id": "news",
                    "title": "News",
                    "cards": [
                        {"id": "card_welcome", "title": "Welcome to AFKZone", "subtitle": "Get started", "image_url": "https://afkzone.cloud/img/welcome.png", "action_id": "news_1"},
                        {"id": "card_guide", "title": "User Guide", "subtitle": "Learn more", "image_url": "https://afkzone.cloud/img/guide.png", "action_id": "user_guide"}
                    ]
                },
                {
                    "id": "tutorials",
                    "title": "Tutorials",
                    "cards": [
                        {"id": "card_setup", "title": "Quick Setup", "subtitle": "5 min", "image_url": "https://afkzone.cloud/img/setup.png", "action_id": "user_guide"}
                    ]
                }
            ]
        },
        "purchase": {
            "tiers": [
                {"id": "uvip", "label": "UVIP"},
                {"id": "gvip", "label": "GVIP"},
                {"id": "kvip", "label": "KVIP"}
            ],
            "regions": [
                {"code": "sg", "label": "Singapore", "probe_host": "ping-sg.afkzone.cloud"},
                {"code": "th", "label": "Thailand", "probe_host": "ping-th.afkzone.cloud"},
                {"code": "vn", "label": "Vietnam", "probe_host": "ping-vn.afkzone.cloud"}
            ]
        },
        "me": {
            "menu_action_ids": ["open_orders", "net_check", "user_guide", "redeem_code"]
        }
    }
}

def main():
    print("=" * 60)
    print("Creating QA Pack Config Revision")
    print("=" * 60)
    
    # Create config
    resp = requests.post(
        f"{BASE}/admin/api/ui-configs",
        json={"payload": QA_PACK_PAYLOAD, "comment": "QA Pack - full actions/discover/purchase"},
        auth=AUTH
    )
    resp.raise_for_status()
    data = resp.json()
    print(f"\n✅ Created revision: {data['revision']}")
    
    # Fetch to verify
    print("\n📄 Verifying /public/mobile-ui-config...")
    config = requests.get(f"{BASE}/public/mobile-ui-config").json()
    print(f"   Revision: {config['payload']['revision']}")
    print(f"   Signature alg: {config['signature']['alg']}")
    print(f"   Key ID: {config['signature']['key_id']}")
    print(f"   Tabs: {len(config['payload']['tabs'])}")
    print(f"   Actions: {len(config['payload']['actions'])}")
    print(f"   Quick actions: {config['payload']['content']['device']['quick_action_ids']}")
    print(f"   Menu actions: {config['payload']['content']['me']['menu_action_ids']}")
    print(f"   Discover sections: {len(config['payload']['content']['discover']['sections'])}")
    
    print("\n" + "=" * 60)
    print("QA Pack created successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
