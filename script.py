import time
import re
import json
import os
import subprocess
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service

def scrape_beauty_studios(term):
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/chromium-browser"
    options.add_argument("--lang=en-US")
    options.add_experimental_option("detach", True)

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    # 1. Open Google Maps
    driver.get("https://www.google.com/maps")
    driver.maximize_window()
    time.sleep(3)

    # 2. Search for "beauty studio"
    search_box = driver.find_element(By.NAME, "q")
    search_box.clear()
    search_box.send_keys(term + Keys.ENTER)
    time.sleep(5)


    try:
        feed = driver.find_element(By.XPATH, "//div[@role='feed']")
        for _ in range(2):  # Adjust range for more scrolling
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
            time.sleep(2)
    except Exception:
        print("Could not scroll feed.")

    # 4. Get all result cards
    cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'Nv2PK')]")
    print(f"\nFound {len(cards)} Beauty Studios\n")
    print("=" * 50)

    main_data = []
    # 5. Click each card and parse HTML with BeautifulSoup
    for idx, card in enumerate(cards, start=1):
        try:
            # Click card to load details in sidebar
            card.click()
            time.sleep(2)

            # Pass raw HTML page source to BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Extract map url
            map_url = driver.current_url
            # Extract Name (h1 inside role="main" or top h1)
            name_tag = soup.select_one("h1.DUwDvf") or soup.find("h1")
            name = name_tag.get_text(strip=True) if name_tag else "N/A"

            # Selects the first span directly inside the F7nice container
            rating_tag = soup.select_one(".F7nice span")
            rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"
            # Extract Phone
            phone_btn = soup.find("button", {"data-item-id": lambda x: x and "phone" in x})
            phone = phone_btn.get_text(strip=True) if phone_btn else "N/A"

            # Extract Website
            website_link = soup.find("a", {"data-item-id": "authority"})
            website = website_link.get("href") if website_link else "N/A"

            # Extract Email (Scan entire detail pane text using regex)
            full_text = soup.get_text()
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', full_text)
            email = email_match.group(0) if email_match else "N/A"

            # Extract Social Links
            facebook = "N/A"
            instagram = "N/A"
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if "facebook.com" in href.lower() and facebook == "N/A":
                    facebook = href
                elif "instagram.com" in href.lower() and instagram == "N/A":
                    instagram = href

            lead_data = {
                "index": idx,
                "name": name,
                "rating": rating,
                "phone": phone,
                "email": email,
                "map_url": map_url,
                "website": website,
                "facebook": facebook,
                "instagram": instagram,
                }
            main_data.append(lead_data)
        except Exception as e:
            continue
    # 6. Save all collected dictionaries to JSON file
    output_filename = "total-leads.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(main_data, f, ensure_ascii=False, indent=4)
    print(f"\nSuccessfully saved {len(main_data)} records to '{output_filename}'!")

if __name__ == "__main__":
    term = input("\n[+] Enter Search Term : ")
    if term.strip() == "":
        print("\n[!] Please enter search term")
        exit()

    scrape_beauty_studios(term.strip())
    subprocess.run(["python3", "-m", "http.server", "8000"], check=True)