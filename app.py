import os, httpx, time, threading
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask

app = Flask(__name__)
TOKEN = os.environ.get("TOKEN")
ID_FILE = "subscribers.txt"

def save_id(chat_id):
    chat_id = str(chat_id)
    if not os.path.exists(ID_FILE): open(ID_FILE, "w").close()
    with open(ID_FILE, "r") as f: ids = f.read().splitlines()
    if chat_id not in ids:
        with open(ID_FILE, "a") as f: f.write(chat_id + "\n")

def get_all_ids():
    if not os.path.exists(ID_FILE): return []
    with open(ID_FILE, "r") as f: return f.read().splitlines()

def broadcast(text):
    if not TOKEN: return
    for cid in get_all_ids():
        try:
            httpx.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": cid, "text": text}, timeout=5.0)
            time.sleep(0.1)
        except: continue

def updater():
    offset = 0
    while True:
        try:
            res = httpx.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=30", timeout=35.0).json()
            if res.get("ok"):
                for up in res.get("result", []):
                    offset = up["update_id"] + 1
                    if "message" in up: save_id(up["message"]["chat"]["id"])
        except: time.sleep(5)

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
                    code_tag = BeautifulSoup(res.text, 'html.parser').find('code')
                    if code_tag and url not in scanned:
                        broadcast(f"🌟 MÃ XU MỚI!\n🔑 Code: {code_tag.text}\n🔗 {url}")
                        scanned.add(url)
                    stt += 1
                else:
                    time.sleep(25)
                    continue
            except: time.sleep(10)

@app.route('/health')
def health(): return {"status": "alive"}, 200

@app.route('/')
def home(): return "Hunter Active", 200

if __name__ == "__main__":
    threading.Thread(target=updater, daemon=True).start()
    threading.Thread(target=scanner, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
