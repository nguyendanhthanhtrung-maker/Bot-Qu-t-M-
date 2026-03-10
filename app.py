import os, httpx, time, threading
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask

app = Flask(__name__)
TOKEN = os.environ.get("TOKEN")

# Lấy ID cố định từ biến môi trường, ví dụ: "12345678,98765432"
def get_fixed_ids():
    ids_str = os.environ.get("ADMIN_IDS", "")
    if not ids_str:
        return []
    return [i.strip() for i in ids_str.split(",") if i.strip()]

def broadcast(text):
    if not TOKEN: return
    ids = get_fixed_ids()
    for cid in ids:
        try:
            httpx.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                       json={"chat_id": cid, "text": text}, timeout=5.0)
            time.sleep(0.1)
        except: continue

def scanner():
    scanned = set()
    while True:
        now = datetime.now()
        m, d = now.strftime("%m"), now.strftime("%d")
        stt = 1
        while True:
            if datetime.now().strftime("%d") != d: break
            url = f"https://telegra.ph/NH%E1%BA%ACN-XU-BOT-DVK-{m}-{d}-{stt:02d}"
            try:
                res = httpx.get(url, timeout=15.0)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    code_tag = soup.find('code')
                    if code_tag and url not in scanned:
                        broadcast(f"🌟 MÃ XU MỚI!\n🔑 Code: {code_tag.text}\n🔗 {url}")
                        scanned.add(url)
                    stt += 1
                else:
                    time.sleep(25)
                    continue
            except:
                time.sleep(10)

@app.route('/health')
def health():
    return {"status": "alive", "fixed_subs": get_fixed_ids()}, 200

@app.route('/')
def home():
    return "Hunter Fixed ID Active", 200

if __name__ == "__main__":
    threading.Thread(target=scanner, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
