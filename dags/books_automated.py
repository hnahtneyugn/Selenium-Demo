from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime
import pendulum
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import json
import logging

# Demo for automated scraping data using Selenium with Airflow and Docker
path_to_brave = "/usr/bin/brave-browser"
path_to_chromedriver = "/usr/local/bin/chromedriver"
url_to_crawl = "https://books.toscrape.com/catalogue/category/books/humor_30/index.html"

def scrape():
    log_path = f"/opt/airflow/logs/chromedriver_{pendulum.now('Asia/Ho_Chi_Minh').strftime('%Y%m%d_%H%M%S')}.log"
    data_output_path = f"/opt/airflow/data/automated_scraping/{pendulum.now('Asia/Ho_Chi_Minh').strftime('%Y%m%d_%H%M%S')}_books.json"

    def get_driver():
        options = Options()
        options.binary_location = path_to_brave
        options.add_argument("--headless")  # No GUI when crawling data
        options.add_argument("--window-size=1920,1080") # Fixed window-size
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Specify Chromedriver path and path to log file
        service = webdriver.ChromeService(executable_path=path_to_chromedriver, log_output=log_path)

        # Create a Brave WebDriver by using Chromedriver + Brave binary
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def get_books():
        driver = get_driver()
        driver.get(url=url_to_crawl)
        books_list = []
        rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

        try:
            while True:
                books = driver.find_elements(By.CSS_SELECTOR, "article.product_pod")
                for book in books:
                    # Returns "star rating" and "Four"
                    rating_string = book.find_element(By.CSS_SELECTOR, "p.star-rating").get_attribute("class") 
                    rating_text = rating_string.split()[1]
                    price = book.find_element(By.CSS_SELECTOR, "div.product_price p.price_color").text
                    stock = book.find_element(By.CSS_SELECTOR, "div.product_price p.instock.availability").text
                    description_link = book.find_element(By.CSS_SELECTOR, "h3 > a").get_attribute("href")
                    title = book.find_element(By.CSS_SELECTOR, "h3 > a").get_attribute("title")

                    # Create a new tab and switch to it to get the description of the book
                    # driver.execute_script("window.open(arguments[0]);", description_link)
                    # driver.switch_to.window(driver.window_handles[1])  # switch to new tab

                    driver.get(description_link)
                    try:
                        description = driver.find_element(By.CSS_SELECTOR, "article.product_page > p").text.strip('“”"')
                    except NoSuchElementException:  # Handle books without descriptions
                        description = ""
                    driver.back()

                    # After getting description, close the tab
                    # driver.close()      
                    
                    # Switch back to category
                    # driver.switch_to.window(driver.window_handles[0])
                    
                    # Store all information of books inside a dictionary
                    info = {'title': title, 'rating': rating_map[rating_text], 'price': price, 'stock': stock, 'description': description}
                    books_list.append(info)

                try:
                    # Find URL to the next page
                    next_page = driver.find_element(By.CSS_SELECTOR, "ul.pager > li.next > a")
                    next_page_link = next_page.get_attribute("href")

                    # If we're in the last page, break the loop
                    if not next_page_link:
                        break
            
                    # Otherwise, move to next page with the same category and keep getting books
                    driver.get(next_page_link)

                except NoSuchElementException:
                    break
        finally:
            driver.quit()

        return books_list
    
    books_list = get_books()

    with open(data_output_path, "w", encoding="utf-8") as file:
        json.dump(books_list, file, ensure_ascii=False, indent=4)

    logging.info(f"Saved {len(books_list)} books to {data_output_path}")


with DAG(
    dag_id = "automated_book_scraper",
    description = "Automated scraper demo",
    schedule="*/5 16 * * *",
    start_date= pendulum.datetime(2025, 11, 19, tz='Asia/Ho_Chi_Minh'),
    end_date= pendulum.datetime(2025, 11, 20, tz='Asia/Ho_Chi_Minh'),
    catchup=False) as dag:
    task_1 = PythonOperator(task_id="book_scraper", python_callable=scrape)
