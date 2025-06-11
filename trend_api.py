from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

app = Flask(__name__)

@app.route("/trends")
def get_trends():
    region = request.args.get("geo", "US")
    url = f"https://trends.google.com/trends/trendingsearches/daily?geo={region}"

    chrome_path = r"C:\chromedriver-win64\chromedriver.exe"
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # options.add_argument("--headless=new")  # Use only if you don't want the window

    driver = webdriver.Chrome(service=Service(chrome_path), options=options)

    try:
        driver.get(url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "daily-trends"))
        )

        time.sleep(5)

        # DEBUG: Save what Selenium sees
        with open("selenium_dump.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        # Check if Shadow DOM is available
        shadow_root_present = driver.execute_script("""
            const el = document.querySelector('daily-trends');
            return el && !!el.shadowRoot;
        """)

        if not shadow_root_present:
            return jsonify({
                "status": "error",
                "message": "Shadow root not present on <daily-trends>"
            })

        # Extract trends safely
        try:
            trends = driver.execute_script("""
                const items = [];
                const dailyTrendsEl = document.querySelector('daily-trends');
                const feedItems = dailyTrendsEl.shadowRoot.querySelectorAll('feed-item');
                feedItems.forEach(feed => {
                    const root = feed.shadowRoot;
                    if (!root) return;
                    const titleEl = root.querySelector('.details .title');
                    const linkEl = root.querySelector('a');
                    if (titleEl && linkEl) {
                        items.push({
                            title: titleEl.innerText.trim(),
                            link: linkEl.href
                        });
                    }
                });
                return items;
            """)
        except Exception as js_error:
            return jsonify({
                "status": "error",
                "message": f"JavaScript error: {str(js_error)}"
            })

        return jsonify({
            "shadow_root_present": shadow_root_present,
            "trends": trends
        })



    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        driver.quit()

if __name__ == "__main__":
    app.run(debug=True)
