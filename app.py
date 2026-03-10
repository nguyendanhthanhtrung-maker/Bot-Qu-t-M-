import os, httpx, time, threading
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask

app = Flask(__name__)
TOKEN = os.environ.get("TOKEN")
# Danh sách ID lưu trong bộ nhớ tạm (sẽ mất khi restart, nên hãy dùng ADMIN_IDS trong Render)
temp_subs = set()

def get_all_ids():
    fixed_ids = os.environ.get("ADMIN_IDS", "")
    ids = [i.strip() for i in fixed_ids.split(",") if i.strip()]
    ids.extend(list(temp_subs))
    return list(set(ids))

def broadcast(text):
    if not TOKEN: return
    for cid in get_all_ids():
        try:
            httpx.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                       json={"chat_id": cid, "text": text}, timeout=5.0)
            time.sleep(0.1)
        except: continue

def updater():
    offset = 0
    if not TOKEN: return
    logger_url = f"https://api.telegram.org/bot{TOKEN}"
    while True:
        try:
            # Lấy tin nhắn mới
            res = httpx.get(f"{logger_url}/getUpdates?offset={offset}&timeout=20", timeout=25.0).json()
            if res.get("ok"):
                for up in res.get("result", []):
                    offset = up["update_id"] + 1
                    if "message" in up:
                        cid = str(up["message"]["chat"]["id"])
                        if cid not in temp_subs:
                            temp_subs.add(cid)
                            # GỬI PHẢN HỒI NGAY LẬP TỨC ĐỂ KIỂM TRA
                            httpx.post(f"{logger_url}/sendMessage", 
                                       json={"chat_id": cid, "text": f"✅ Bot Hunter đã nhận ID: {cid}\nBạn sẽ nhận được mã khi Telegra.ph cập nhật."})
        except Exception as e:
            print(f"Update Error: {e}")
            time.sleep(5)

def scanner():
    scanned = set()
    while True:
        now = datetime.now()
        # Định dạng tháng/ngày: 03-10
        m, d = now.strftime("%m"), now.strftime("%d")
        stt = 1
        while True:
            # Nếu đã sang ngày mới thì thoát vòng lặp STT để cập nhật m, d
            if datetime.now().strftime("%d") != d: break
            
            url = f"https://telegra.ph/NH%E1%BA%ACN-XU-BOT-DVK-{m}-{d}-{stt:02d}"
            try:
                res = httpx.get(url, timeout=10.0)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    code_tag = soup.find('code')
                    if code_tag and url not in scanned:
                        broadcast(f"🌟 MÃ XU MỚI!\n🔑 Code: {code_tag.text}\n🔗 {url}")
                        scanned.add(url)
                    stt += 1 # Tiếp tục tìm bài 02, 03...
                    time.sleep(2)
                else:
                    # Nếu không tìm thấy bài stt tiếp theo, nghỉ 30s rồi quét lại stt đó
                    time.sleep(30)
                    continue
            except:
                time.sleep(10)

@app.route('/health')
def health():
    return {"status": "alive", "active_ids": get_all_ids()}, 200

@app.route('/')
def home():
    return "Hunter Bot is Running", 200

if __name__ == "__main__":
    # Chạy updater để đọc tin nhắn và scanner để quét mã
    threading.Thread(target=updater, daemon=True).start()
    threading.Thread(target=scanner, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
