from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
from dotenv import load_dotenv
import os

load_dotenv()

aibelajarlagi_url = os.getenv("aibelajarlagi_url")
aibelajarlagi_email = os.getenv("aibelajarlagi_email")
aibelajarlagi_password = os.getenv("aibelajarlagi_password")
webdriver_path = os.getenv("webdriver")
image_dir = os.getenv("image_dir")
image_list = os.getenv("image_list")
output_file = os.getenv("output_file")

with open(image_list, "r") as file:
    images = [line.strip() for line in file]

results = []

prompt = "Lakukan image captioning dalam satu kalimat"

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--start-maximized")
service = Service(webdriver_path)

driver = webdriver.Chrome(service=service, options=chrome_options)

def text_to_be_present_in_last_element(locator, texts):
    def _predicate(driver):
        try:
            elements = driver.find_elements(*locator)
            if not elements:
                return False
            last_element_text = elements[-1].text
            return any(text in last_element_text for text in texts)
        except Exception as e:
            return False
    return _predicate

def number_of_elements_to_be(locator, count):
    def _predicate(driver):
        elements = driver.find_elements(*locator)
        return len(elements) == count
    return _predicate

try:
    driver.get(aibelajarlagi_url)

    # Login
    email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
    email_input.send_keys(aibelajarlagi_email)
    password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    password_input.send_keys(aibelajarlagi_password)
    button_login = driver.find_element(By.CSS_SELECTOR, "button")
    button_login.click()

    for i, image in enumerate(images):
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
        )

        time.sleep(5)

        div = driver.find_element(By.CSS_SELECTOR, "div[class='flex gap-2 flex-wrap justify-end items-end']")
        button_image = div.find_elements(By.CSS_SELECTOR, "button")[1]
        button_image.click()

        path = image_dir + "\\" + image
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(path)

        time.sleep(5)

        text_input = driver.find_element(By.CSS_SELECTOR, "textarea")
        text_input.send_keys(prompt)

        button_submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        button_submit.click()

        processing_texts = ["Generating...", "Thinking..."]
        response_locator = (By.CSS_SELECTOR, "div[class*='group/message'][class*='bg-muted']")
        WebDriverWait(driver, 300).until(
            number_of_elements_to_be(response_locator, i+1)
        )
        WebDriverWait(driver, 300).until(
            text_to_be_present_in_last_element(response_locator, processing_texts)
        )
        WebDriverWait(driver, 300).until_not(
            text_to_be_present_in_last_element(response_locator, processing_texts)
        )

        response = driver.find_elements(*response_locator)[-1]
        last_response = response.text

        while "Timeout" in last_response:
            print("timeout-detected")
            div = driver.find_element(By.CSS_SELECTOR, "div[class='flex gap-2 flex-wrap justify-end items-end']")
            regen_button = div.find_elements(By.CSS_SELECTOR, "button")[2]
            regen_button.click()

            WebDriverWait(driver, 300).until(
                text_to_be_present_in_last_element(response_locator, processing_texts)
            )
            WebDriverWait(driver, 300).until(
                text_to_be_present_in_last_element(response_locator, processing_texts)
            )

            response = driver.find_elements(*response_locator)[-1]
            last_response = response.text
        
        results.append({"image": image, "description": last_response})

finally:
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["image", "description"])
        writer.writeheader()
        writer.writerows(results)

    driver.quit()
