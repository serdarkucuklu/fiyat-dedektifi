import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def verify_files():
    print("--- Verifying Project Files ---")
    required = ["index.html", "style.css", "app.js", "data.json", "agent.py"]
    all_ok = True
    for f in required:
        if os.path.exists(f):
            print(f"[OK] File exists: {f}")
        else:
            print(f"[FAIL] Missing file: {f}")
            all_ok = False
    return all_ok

def run_agent_test():
    print("\n--- Running agent.py Local Dry Run ---")
    import agent
    
    # 1. Verify data.json structure
    print("Reading data.json content...")
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[OK] data.json read successfully. Last updated: {data.get('last_updated')}")
        
        # Verify structure
        if "deals" in data and len(data["deals"]) > 0:
            print(f"[OK] data.json structure is valid. Deals count: {len(data['deals'])}")
        else:
            print("[FAIL] data.json missing 'deals' key or deals list is empty.")
            return False
    except Exception as e:
        print(f"[FAIL] Could not read data.json: {e}")
        return False

    # 2. Test Curation Loop (Dry Run with real API call)
    print("\nRunning top deals curation via Gemini (Dry Run)...")
    try:
        # We use a simple prompt to check formatting speed and parsing
        prompt = (
            "Select exactly 1 hot deal on a tech accessory in Turkey. "
            "Format the response in strict JSON matching this schema: "
            '{"deals": [{"title": "Product Title", "original_price": "Price TL", "discount_price": "Discount TL", "discount_rate": "% Indirim", "source": "Store Name", "affiliate_link": "Link", "description": "Short desc", "image_url": "URL"}]}'
        )
        raw_json = agent.call_gemini(prompt)
        if raw_json:
            clean_json = raw_json.replace("```json", "").replace("```", "").strip()
            res = json.loads(clean_json)
            if "deals" in res and len(res["deals"]) > 0:
                print("[OK] Gemini successfully returned valid structured deals JSON.")
                print(f"  Deal Title: {res['deals'][0].get('title')}")
                print(f"  Discount Price: {res['deals'][0].get('discount_price')}")
                return True
            else:
                print(f"[FAIL] Curation format is incorrect: {res}")
                return False
        else:
            print("[FAIL] Gemini returned empty response.")
            return False
    except Exception as e:
        print(f"[FAIL] Exception during Gemini test: {e}")
        return False

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    files_ok = verify_files()
    if not files_ok:
        sys.exit(1)
        
    test_ok = run_agent_test()
    if test_ok:
        print("\nALL TESTS PASSED! Fiyat Dedektifi Agent is fully verified and functional.")
        sys.exit(0)
    else:
        print("\nTESTS FAILED. Please check API credentials and log errors.")
        sys.exit(1)
