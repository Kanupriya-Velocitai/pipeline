from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import psycopg2
import os

# Path to ChromeDriver (installed in GitHub Actions)
service = Service("/usr/local/bin/chromedriver")
options = Options()

# Add headless mode and required arguments for CI environments
options.add_argument("--headless")  # Run Chrome in headless mode
options.add_argument("--no-sandbox")  # Required for running as root in CI
options.add_argument("--disable-dev-shm-usage")  # Prevent shared memory issues
options.add_argument("--disable-gpu")  # Disable GPU acceleration
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

# Initialize the WebDriver
driver = webdriver.Chrome(service=service, options=options)

try:
    # Connect to PostgreSQL database
    conn = psycopg2.connect(
        host="localhost",
        database="RetailPrice",
        user="postgres",
        password="root"
    )
    cursor = conn.cursor()

    # Create table if it does not exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_data (
            id SERIAL PRIMARY KEY,
            product_name TEXT,
            source TEXT,
            category TEXT,
            actual_price TEXT,
            discount TEXT,
            price_after_discount TEXT,
            technical_details TEXT,
            total_reviews TEXT,
            reviews_and_ratings TEXT,
            detailed_elements TEXT,
            actual_reviews_and_ratings TEXT,
            specification TEXT,
            product_url TEXT
        );
    """)
    conn.commit()

    # Navigate to the Flipkart search results page
    search_url = "https://www.flipkart.com/search?q=television&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off"
    driver.get(search_url)
    wait = WebDriverWait(driver, 20)

    # Close popup if it appears
    try:
        close_button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@class='_2KpZ6l _2doB4z']")))
        close_button.click()
        print("Popup closed.")
    except Exception as e:
        print("Popup not found or already closed:", e)

    # Collect product data
    product_names = driver.find_elements(By.CLASS_NAME, "KzDlHZ")
    prices = driver.find_elements(By.CSS_SELECTOR, ".Nx9bqj._4b5DiR")
    product_links = driver.find_elements(By.CLASS_NAME, "CGtC98")

    for i in range(len(product_names)):
        name = product_names[i].text if i < len(product_names) else "N/A"
        price = prices[i].text if i < len(prices) else "N/A"
        product_url = product_links[i].get_attribute('href') if i < len(product_links) else "N/A"

        # Insert data into the database
        cursor.execute("""
            INSERT INTO product_data (
                product_name, source, category, actual_price, price_after_discount, product_url
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, "Flipkart", "Television", price, price, product_url))
        conn.commit()

    print("Data inserted into the database.")

except Exception as e:
    print("An error occurred:", e)

finally:
    driver.quit()
    if 'conn' in locals():
        cursor.close()
        conn.close()

