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

def get_verified_product_image(title, category=None):
    title_lower = title.lower()
    cat = (category or "").lower()
    
    # Predefined high-quality verified Unsplash images for products
    images = {
        "smartphone": [
            "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?q=80&w=600&auto=format&fit=crop", # Rose gold phone
            "https://images.unsplash.com/photo-1598327105666-5b89351aff97?q=80&w=600&auto=format&fit=crop", # Android phone
            "https://images.unsplash.com/photo-1580910051074-3eb694886505?q=80&w=600&auto=format&fit=crop"  # Phone on table
        ],
        "tablet": [
            "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?q=80&w=600&auto=format&fit=crop", # iPad / tablet on dark background
            "https://images.unsplash.com/photo-1589739900243-4b52cd9b104e?q=80&w=600&auto=format&fit=crop"  # Tablet on desk
        ],
        "laptop": [
            "https://images.unsplash.com/photo-1496181130204-7552cc14acfc?q=80&w=600&auto=format&fit=crop", # Laptop
            "https://images.unsplash.com/photo-1531297484001-80022131f5a1?q=80&w=600&auto=format&fit=crop"  # MacBook
        ],
        "headphones": [
            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=600&auto=format&fit=crop", # Headphones
            "https://images.unsplash.com/photo-1487215078519-e21cc028cb29?q=80&w=600&auto=format&fit=crop", # Studio headphones
            "https://images.unsplash.com/photo-1546435770-a3e426bf472b?q=80&w=600&auto=format&fit=crop"  # Wireless headphones
        ],
        "speaker": [
            "https://images.unsplash.com/photo-1545454675-3531b543be5d?q=80&w=600&auto=format&fit=crop", # Speaker
            "https://images.unsplash.com/photo-1608248597279-f99d160bfcbc?q=80&w=600&auto=format&fit=crop", # Smart speaker
            "https://images.unsplash.com/photo-1612198188258-d2427a195e34?q=80&w=600&auto=format&fit=crop"  # Soundbar
        ],
        "smartwatch": [
            "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?q=80&w=600&auto=format&fit=crop", # Smartwatch
            "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?q=80&w=600&auto=format&fit=crop", # Watch
            "https://images.unsplash.com/photo-1523275335684-37898b6baf30?q=80&w=600&auto=format&fit=crop"  # Apple watch style
        ],
        "gaming": [
            "https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?q=80&w=600&auto=format&fit=crop", # DualSense controller
            "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?q=80&w=600&auto=format&fit=crop"  # Gaming setup / controller
        ],
        "tv_monitor": [
            "https://images.unsplash.com/photo-1593305841991-05c297ba4575?q=80&w=600&auto=format&fit=crop", # Smart TV
            "https://images.unsplash.com/photo-1552533237-c8c884b2540b?q=80&w=600&auto=format&fit=crop"  # TV on wall
        ],
        "vacuum": [
            "https://images.unsplash.com/photo-1581578731548-c64695cc6952?q=80&w=600&auto=format&fit=crop", # Cleaning vacuum
            "https://images.unsplash.com/photo-1558317374-067fb5f30001?q=80&w=600&auto=format&fit=crop"  # Robot vacuum
        ],
        "airfryer": [
            "https://images.unsplash.com/photo-1621972750749-0fbb1abb7736?q=80&w=600&auto=format&fit=crop", # Airfryer/oven style
            "https://images.unsplash.com/photo-1578643463396-0997cb5328c1?q=80&w=600&auto=format&fit=crop"  # Blender/mixer
        ],
        "cosmetic_beauty": [
            "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?q=80&w=600&auto=format&fit=crop", # Cosmetics
            "https://images.unsplash.com/photo-1596462502278-27bfdc403348?q=80&w=600&auto=format&fit=crop"  # Facial roller/beauty product
        ],
        "personal_care": [
            "https://images.unsplash.com/photo-1519823551278-64ac92734fb1?q=80&w=600&auto=format&fit=crop", # Massage therapy / stones
            "https://images.unsplash.com/photo-1600334089648-b0d9d3028eb2?q=80&w=600&auto=format&fit=crop"  # Wellness oil/massage
        ],
        "clothing_accessory": [
            "https://images.unsplash.com/photo-1584917865442-de89df76afd3?q=80&w=600&auto=format&fit=crop", # Handbag
            "https://images.unsplash.com/photo-1509319117193-57bab727e09d?q=80&w=600&auto=format&fit=crop"  # Straw hat / clothing
        ],
        "home_appliance": [
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=600&auto=format&fit=crop"  # Modern wall AC
        ],
        "cooling_fan": [
            "https://images.unsplash.com/photo-1618945902034-7389441a1a5b?q=80&w=600&auto=format&fit=crop", # Minimalist white desk fan
            "https://images.unsplash.com/photo-1591181520189-abfe073ff477?q=80&w=600&auto=format&fit=crop"  # Retro desk fan
        ],
        "thermos": [
            "https://images.unsplash.com/photo-1576092768241-dec231879fc3?q=80&w=600&auto=format&fit=crop", # Thermos flask
            "https://images.unsplash.com/photo-1602143407151-7111542de6e8?q=80&w=600&auto=format&fit=crop"  # Steel bottle
        ],
        "general_tech": [
            "https://images.unsplash.com/photo-1527689368864-3a821dbccc34?q=80&w=600&auto=format&fit=crop", # Gadgets on desk
            "https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=600&auto=format&fit=crop"  # Keyboard/tablet
        ],
        "general_home": [
            "https://images.unsplash.com/photo-1513694203232-719a280e022f?q=80&w=600&auto=format&fit=crop", # Living room
            "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?q=80&w=600&auto=format&fit=crop"  # Chair/pillow
        ]
    }
    
    # Priority keyword-based routing first to ensure accurate mappings
    selected_cat = None
    if any(k in title_lower for k in ["tablet", "ipad"]):
        selected_cat = "tablet"
    elif any(k in title_lower for k in ["playstation", "xbox", "nintendo", "ps5", "oyun", "konsol", "gamepad", "bundle"]):
        selected_cat = "gaming"
    elif any(k in title_lower for k in ["tv", "televizyon", "monitör", "monitor", "ekran"]):
        selected_cat = "tv_monitor"
    elif any(k in title_lower for k in ["vantilatör", "fan", "vantilator"]):
        selected_cat = "cooling_fan"
    elif any(k in title_lower for k in ["masaj", "gevşetme", "massage", "epilasyon", "lumea", "tıraş", "traş"]):
        selected_cat = "personal_care"
    elif any(k in title_lower for k in ["kulaklık", "headphone", "airpods", "kulaklik"]):
        selected_cat = "headphones"
    elif any(k in title_lower for k in ["saat", "watch", "band", "bileklik", "smartwatch"]):
        selected_cat = "smartwatch"
    elif any(k in title_lower for k in ["hoparlör", "speaker", "soundbar", "ses"]):
        selected_cat = "speaker"
    elif any(k in title_lower for k in ["telefon", "phone", "iphone", "redmi", "samsung", "xiaomi"]):
        selected_cat = "smartphone"
    elif any(k in title_lower for k in ["laptop", "bilgisayar", "computer", "macbook", "notebook"]):
        selected_cat = "laptop"
    elif any(k in title_lower for k in ["süpürge", "dyson", "robot", "temizlik", "supurge"]):
        selected_cat = "vacuum"
    elif any(k in title_lower for k in ["airfryer", "fritöz", "fırın", "mutfak"]):
        selected_cat = "airfryer"
    elif any(k in title_lower for k in ["parfüm", "krem", "cilt", "bakım"]):
        selected_cat = "cosmetic_beauty"
    elif any(k in title_lower for k in ["çanta", "bag", "gözlük", "fular", "kemer", "aksesuar", "valiz"]):
        selected_cat = "clothing_accessory"
    elif any(k in title_lower for k in ["klima", "hava", "vantilatör", "ısıtıcı"]):
        selected_cat = "home_appliance"
    elif any(k in title_lower for k in ["termos", "matara", "mug"]):
        selected_cat = "thermos"
    elif any(k in title_lower for k in ["ev", "yastık", "perde", "koltuk", "sehpa"]):
        selected_cat = "general_home"
        
    # If no priority keyword matches, try the category returned by Gemini
    if not selected_cat:
        if cat in images:
            selected_cat = cat
        else:
            selected_cat = "general_tech"

    img_list = images.get(selected_cat, images["general_tech"])
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

    # 2. Call Gemini to format the top 15 deals (5 from each store)
    print("Curating top 15 deals via Gemini...")
    generator_prompt = f"""
    You are an expert shopping curator for 'Fiyat Dedektifi', a premium minimalist price comparison dashboard for Turkish youth.
    Analyze the following search trends and select EXACTLY 15 notable, verified discounts/deals currently active in Turkey.
    You MUST select exactly 5 deals from Amazon.com.tr, exactly 5 deals from Hepsiburada, and exactly 5 deals from Trendyol.
    
    For each deal, generate:
    1. title: Clean Turkish product name (e.g. 'Anker Soundcore Q30 Kulaklık').
    2. original_price: Approximate standard market price in TL (e.g., '2.499 TL').
    3. discount_price: Actual discount/sale price in TL (e.g., '1.799 TL').
    4. discount_rate: Calculated drop percentage (e.g., '%28 İndirim').
    5. source: The store name (MUST be exactly one of: 'Amazon.com.tr', 'Hepsiburada', 'Trendyol').
    6. affiliate_link: Amazon.com.tr search link containing 'tag=aurafocus-21' for this product, e.g. "https://www.amazon.com.tr/s?k=anker+soundcore+q30&tag=aurafocus-21"
    7. description: A concise 1-sentence Turkish sales pitch/review explaining why this is a good deal.
    8. category: The product category, which MUST be exactly one of: 'smartphone', 'tablet', 'laptop', 'headphones', 'speaker', 'smartwatch', 'gaming', 'tv_monitor', 'vacuum', 'airfryer', 'cooling_fan', 'home_appliance', 'personal_care', 'cosmetic_beauty', 'clothing_accessory', 'thermos', 'general_tech', 'general_home'.

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
          "source": "Amazon.com.tr",
          "affiliate_link": "Amazon search link with tag=aurafocus-21",
          "description": "Short Turkish description.",
          "category": "headphones"
        }},
        ... (exactly 15 items in total, 5 for each source)
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
        
        # Overwrite image URLs with verified ones and fix affiliate/search links
        for deal in data.get("deals", []):
            deal["image_url"] = get_verified_product_image(deal["title"], deal.get("category"))
            
            # Clean and construct search links if missing or invalid
            link = deal.get("affiliate_link", "")
            if not isinstance(link, str):
                link = ""
            link = link.strip()
            
            source = deal.get("source", "").lower()
            title_query = urllib.parse.quote_plus(deal["title"])
            
            if not link or link.upper() in ["N/A", "NONE", "NULL", ""]:
                if "trendyol" in source:
                    deal["affiliate_link"] = f"https://www.trendyol.com/sr?q={title_query}"
                elif "hepsiburada" in source:
                    deal["affiliate_link"] = f"https://www.hepsiburada.com/ara?q={title_query}"
                else:
                    deal["affiliate_link"] = f"https://www.amazon.com.tr/s?k={title_query}&tag=aurafocus-21"
            
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
