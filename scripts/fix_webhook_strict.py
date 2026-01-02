import os

def fix_webhook():
    file_path = 'd:/rustdesk-dev/server_app.py'
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    inserted = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        # Look for the start of the try block in casso_webhook_handler
        # We know it comes shortly after "=== CASSO WEBHOOK RECEIVED ==="
        if "logging.info(\"=== CASSO WEBHOOK RECEIVED ===\")" in line:
            # We are inside the function.
            pass
        
        if "if request.method == \"GET\":" in line and not inserted:
            # Check context: are we in casso_webhook_handler?
            # simpler: just insert it before "body = await request.json()"
            pass

    # Let's try a different approach: find the exact line "body = await request.json()"
    # inside casso_webhook_handler and insert BEFORE it.
    
    new_lines = []
    for line in lines:
        if "body = await request.json()" in line and "casso_webhook_handler" in "".join(lines[lines.index(line)-15:lines.index(line)]):
            indent = line[:line.find(line.lstrip())]
            verification_code = [
                f'{indent}# Verify Signature\n',
                f'{indent}signature = request.headers.get("secure-token")\n',
                f'{indent}if not signature:\n',
                f'{indent}    logging.warning("Webhook missing secure-token header")\n',
                f'{indent}    raise HTTPException(status_code=401, detail="Missing signature")\n',
                f'{indent}\n',
                f'{indent}if signature != CASSO_WEBHOOK_TOKEN:\n',
                f'{indent}    logging.warning(f"Invalid webhook signature: {{signature}}")\n',
                f'{indent}    raise HTTPException(status_code=401, detail="Invalid signature")\n',
                f'{indent}\n'
            ]
            new_lines.extend(verification_code)
            inserted = True
        
        new_lines.append(line)

    if inserted:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("✅ Patch applied successfully")
    else:
        print("❌ Could not search target line to patch")

if __name__ == "__main__":
    fix_webhook()
