import os
import sys
import json
import datetime
import subprocess
import urllib.parse
import requests
from dotenv import load_dotenv

# Force UTF-8 encoding for console (fixes Windows UnicodeEncodeError)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load environment variables
load_dotenv()
load_dotenv("d:/AI/Playground/02-auto-poster-agent/.env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Import notifier if available
sys.path.append("d:/AI/Playground/02-auto-poster-agent")
try:
    from notifier import trigger_milestone_alert
except ImportError:
    def trigger_milestone_alert(title, value):
        print(f"[Notifier Mock] Alert: {title} - {value}")

def call_gemini(prompt: str, use_search: bool = False):
    """Calls Gemini API with model fallback and optional search grounding."""
    if not GEMINI_API_KEY:
        print("Error: Gemini API Key is missing.")
        return None
    
    models = ["gemini-2.5-flash", "gemini-2.0-flash"]
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    if use_search:
        payload["tools"] = [{"googleSearch": {}}]
    
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                res_data = response.json()
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"Error calling Gemini ({model}): {e}")
    return None

def get_verified_product_image(title):
    title_lower = title.lower()
    
    # Predefined high-quality verified Unsplash images for products
    images = {
        "audio": [
            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=600&auto=format&fit=crop", # Headphones
            "https://images.unsplash.com/photo-1545454675-3531b543be5d?q=80&w=600&auto=format&fit=crop", # Speaker
            "https://images.unsplash.com/photo-1487215078519-e21cc028cb29?q=80&w=600&auto=format&fit=crop"  # Studio headphones
        ],
        "wearable": [
            "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?q=80&w=600&auto=format&fit=crop", # Smartwatch
            "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?q=80&w=600&auto=format&fit=crop", # Watch on table
            "https://images.unsplash.com/photo-1523275335684-37898b6baf30?q=80&w=600&auto=format&fit=crop"  # Sleek white watch
        ],
        "kitchen": [
            "https://images.unsplash.com/photo-1621972750749-0fbb1abb7736?q=80&w=600&auto=format&fit=crop", # Coffee maker
            "https://images.unsplash.com/photo-1576092768241-dec231879fc3?q=80&w=600&auto=format&fit=crop", # Thermos flask
            "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?q=80&w=600&auto=format&fit=crop"  # Kitchen items
        ],
        "gaming_pc": [
            "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?q=80&w=600&auto=format&fit=crop", # Gaming mouse
            "https://images.unsplash.com/photo-1587829741301-dc798b83add3?q=80&w=600&auto=format&fit=crop", # Keyboard
            "https://images.unsplash.com/photo-1527689368864-3a821dbccc34?q=80&w=600&auto=format&fit=crop"  # Desk setup/laptop
        ],
        "home_appliance": [
            "https://images.unsplash.com/photo-1581578731548-c64695cc6952?q=80&w=600&auto=format&fit=crop", # Cleaning/vacuum
            "https://images.unsplash.com/photo-1528740561666-bd247e665488?q=80&w=600&auto=format&fit=crop", # Humidifier
            "https://images.unsplash.com/photo-1558317374-067fb5f30001?q=80&w=600&auto=format&fit=crop"  # Air purifier/fan
        ],
        "general": [
            "https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=600&auto=format&fit=crop", # Tech/office
            "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?q=80&w=600&auto=format&fit=crop", # General camera
            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=600&auto=format&fit=crop"  # Default headphones
        ]
    }
    
    # Categorization based on keywords
    cat = "general"
    if any(k in title_lower for k in ["kulaklık", "headphone", "ses", "hoparlör", "speaker", "soundbar", "kulaklik"]):
        cat = "audio"
    elif any(k in title_lower for k in ["saat", "watch", "band", "bileklik", "smartwatch"]):
        cat = "wearable"
    elif any(k in title_lower for k in ["mutfak", "airfryer", "kahve", "tencere", "tava", "bardak", "termos", "makine"]):
        cat = "kitchen"
    elif any(k in title_lower for k in ["mouse", "klavye", "keyboard", "oyuncu", "gaming", "mousepad"]):
        cat = "gaming_pc"
    elif any(k in title_lower for k in ["süpürge", "dyson", "robot", "temizlik", "supurge"]):
        cat = "home_appliance"
        
    img_list = images.get(cat, images["general"])
    hash_val = sum(ord(c) for c in title)
    idx = hash_val % len(img_list)
    return img_list[idx]

def run_agent():
    print("=" * 60)
    print("  Fiyat Dedektifi (Hot Deals) Autonomous Agent: Curation Loop")
    print("=" * 60)

    # 1. Search Google for current trending discounts in Turkey
    print("Searching Google for trending price drops and hot discounts in Turkey...")
    search_prompt = (
        "What are the best trending tech, home, or accessory discounts, hot deals, and price drops "
        "live today in Turkey on Amazon.com.tr, Hepsiburada, and Trendyol? Find real products with notable discounts."
    )
    
    search_results = "No search results available."
    try:
        raw_res = call_gemini(search_prompt, use_search=True)
        if raw_res:
            search_results = raw_res
            print("[OK] Trends searched successfully.")
    except Exception as e:
        print(f"Warning: Search grounding failed: {e}")

    # 2. Call Gemini to format the top 5 deals
    print("Curating top 5 deals via Gemini...")
    generator_prompt = f"""
    You are an expert shopping curator for 'Fiyat Dedektifi', a premium minimalist price comparison dashboard for Turkish youth.
    Analyze the following search trends and select EXACTLY 5 notable, verified discounts/deals currently active in Turkey.
    For each deal, generate:
    1. title: Clean Turkish product name (e.g. 'Anker Soundcore Q30 Kulaklık').
    2. original_price: Approximate standard market price in TL (e.g., '2.499 TL').
    3. discount_price: Actual discount/sale price in TL (e.g., '1.799 TL').
    4. discount_rate: Calculated drop percentage (e.g., '%28 İndirim').
    5. source: The store name (e.g., 'Amazon.com.tr', 'Hepsiburada', 'Trendyol').
    6. affiliate_link: Amazon.com.tr search link containing 'tag=aurafocus-21' for this product, e.g. "https://www.amazon.com.tr/s?k=anker+soundcore+q30&tag=aurafocus-21"
    7. description: A concise 1-sentence Turkish sales pitch/review explaining why this is a good deal (e.g., 'Son 3 ayın en düşük fiyatı, fiyat/performans canavarı.').
    8. image_url: A high-quality Unsplash image URL suitable for this item category.

    SEARCH TRENDS:
    {search_results}

    Respond in STRICT JSON format (no markdown blocks, just raw JSON matching the schema below):
    {{
      "deals": [
        {{
          "title": "Product Title",
          "original_price": "Price TL",
          "discount_price": "Discount TL",
          "discount_rate": "% Indirim",
          "source": "Store Name",
          "affiliate_link": "Amazon search link with tag=aurafocus-21",
          "description": "Short Turkish description.",
          "image_url": "Unsplash image URL"
        }},
        ... (exactly 5 items)
      ]
    }}
    """

    raw_json = call_gemini(generator_prompt, use_search=False)
    if not raw_json:
        print("[FAIL] Gemini returned empty response. Aborting.")
        return

    # 3. Parse and update data.json
    try:
        clean_json = raw_json.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        data["last_updated"] = datetime.datetime.utcnow().isoformat() + "Z"
        
        # Overwrite image URLs with verified ones to prevent 404 broken images
        for deal in data.get("deals", []):
            deal["image_url"] = get_verified_product_image(deal["title"])
            
        # Save to file
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print("[OK] data.json updated successfully.")
        print(f"Top Deal Curated: {data['deals'][0]['title']}")

        # 4. Trigger Notification
        try:
            best_deal = data['deals'][0]['title']
            trigger_milestone_alert("Fiyat Dedektifi Guncellendi", f"En Sicak Firsat: {best_deal}")
            print("[OK] SMS/Email notification sent.")
        except Exception as e:
            print(f"Warning: Failed to trigger notification: {e}")

        # 5. Git Commit and Push (Only in Git repo)
        if os.path.exists(".git") or os.path.exists("../.git"):
            print("Staging and committing data.json to git...")
            try:
                subprocess.run(["git", "config", "user.name", "Deals Agent"], check=True)
                subprocess.run(["git", "config", "user.email", "agent@fiyatdedektifi.com"], check=True)
                subprocess.run(["git", "add", "data.json"], check=True)
                
                # Check if there are changes to commit
                status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
                if status.stdout.strip():
                    subprocess.run(["git", "commit", "-m", "Otonom Guncelleme: Sicak firsatlar yenilendi [skip ci]"], check=True)
                    subprocess.run(["git", "push", "origin", "main"], check=True)
                    print("[OK] Git push completed. Website auto-deployed!")
                else:
                    print("[INFO] No changes in data.json. Skipping commit.")
            except Exception as e:
                print(f"Warning: Git commit/push failed: {e}")
        else:
            print("[INFO] No Git repository detected. Skipping git push.")
        
    except Exception as e:
        print(f"[FAIL] Error parsing Gemini JSON: {e}")
        print("Raw response was:", raw_json[:300])
        return

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_agent()
