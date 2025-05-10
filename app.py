from flask import Flask, render_template, request
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# 요일별 예약 스케줄
schedule = {
    "Sunday": [
        ("216", "202465133 피아노 최윤정 16:40-20:40"),
        ("208", "202465133 피아노 최윤정 20:40-22:40"),
    ],
    "Monday": [
        ("216", "202465133 피아노 최윤정 16-20"),
        ("208", "202465133 피아노 최윤정 12-15"),
    ],
    "Tuesday": [
        ("216", "202465133 피아노 최윤정 15-19"),
        ("208", "202465133 피아노 최윤정 19-22"),
    ],
    "Wednesday": [
        ("216", "202465133 피아노 최윤정 11:20-15"),
        ("208", "202465133 피아노 최윤정 16-20"),
    ],
    "Thursday": [
        ("216", "202465133 피아노 최윤정 12-16"),
        ("208", "202465133 피아노 최윤정 16-20"),
    ],
    "Friday": [
        ("216", "토 202465133 피아노 최윤정 14-18"),
        ("208", "토 202465133 피아노 최윤정 18-22"),
        ("216", "일 202465133 피아노 최윤정 14-18"),
        ("208", "일 202465133 피아노 최윤정 18-22"),
    ],
}

def run_automation(user_id, user_pw):
    today = datetime.now().strftime("%A")
    entries = schedule.get(today, [])
    content = "."
    t_obj = datetime.strptime("13:00:00", "%H:%M:%S")

    chrome_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(chrome_path), options=options)
    driver.get("https://plato.pusan.ac.kr")
    time.sleep(2)

    driver.find_element(By.ID, "input-username").send_keys(user_id)
    driver.find_element(By.ID, "input-password").send_keys(user_pw)
    driver.find_element(By.NAME, "loginbutton").click()
    time.sleep(3)

    submit_buttons = []
    for i, (ho, subject) in enumerate(entries):
        if i > 0:
            driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[i])
        driver.get("https://plato.pusan.ac.kr/course/view.php?id=93534")
        time.sleep(2)

        try:
            target_text = f"{ho}호 연습실 예약"
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//span[contains(text(), '{target_text}')]"))
            )
            link = driver.find_element(By.XPATH, f"//span[contains(text(), '{target_text}')]/ancestor::a")
            link.click()
            time.sleep(2)

            write_button = driver.find_element(By.CSS_SELECTOR, "a.btn.btn-primary")
            driver.execute_script("arguments[0].click();", write_button)
            time.sleep(2)

            driver.find_element(By.NAME, "subject").send_keys(subject)
            content_area = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#id_contenteditable[contenteditable='true']"))
            )
            content_area.click()
            content_area.send_keys(content)

            submit_btn = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='저장']")
            submit_buttons.append((driver.current_window_handle, submit_btn))

        except Exception as e:
            print(f"[ERROR] {ho}호 문서 준비 실패: {e}")

    res = requests.head("https://plato.pusan.ac.kr")
    server_time = parsedate_to_datetime(res.headers["Date"]) + timedelta(hours=9)
    target_time = server_time.replace(hour=t_obj.hour, minute=t_obj.minute, second=t_obj.second, microsecond=0)
    if target_time <= server_time:
        target_time += timedelta(days=1)

    while True:
        now = parsedate_to_datetime(requests.head("https://plato.pusan.ac.kr").headers["Date"]) + timedelta(hours=9)
        if now >= target_time:
            for handle, btn in submit_buttons:
                try:
                    driver.switch_to.window(handle)
                    driver.execute_script("arguments[0].click();", btn)
                except:
                    print("[WARN] 저장 버튼 클릭 실패")
            break
        time.sleep(0.005)

    driver.quit()

@app.route("/", methods=["GET", "POST", "HEAD"])
def index():
    if request.method == "HEAD":
        return "", 200

    if request.method == "POST":
        user_id = request.form["user_id"]
        user_pw = request.form["user_pw"]
        Thread(target=run_automation, args=(user_id, user_pw)).start()
        return "예약이 시작되었습니다. 서버에서 자동으로 처리됩니다."
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
