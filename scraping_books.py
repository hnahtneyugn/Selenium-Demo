from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import json

# Specify paths
path_to_brave = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
path_to_chromedriver = "/usr/local/bin/chromedriver"
url_to_crawl = "https://books.toscrape.com/"
log_path = "./logs/book_logging.txt"

def get_driver():
    options = Options()
    options.binary_location = path_to_brave
    options.add_argument("--headless")  # No GUI when crawling data
    options.add_argument("--window-size=1920,1080") # Fixed window-size

    # Specify Chromedriver path and path to log file
    service = webdriver.ChromeService(executable_path=path_to_chromedriver, log_output=log_path)

    # Create a Brave WebDriver by using Chromedriver + Brave binary
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def get_categories(driver):
    # Navigate to https://books.toscrape.com/
    # and get the list of categries
    driver.get(url=url_to_crawl)
    category_objects = driver.find_elements(By.CSS_SELECTOR, "div.side_categories ul ul li a")
    category_list = [c.get_attribute("href") for c in category_objects]
    return category_list

def get_books():
    driver = get_driver()
    driver.get(url=url_to_crawl)
    category_list = get_categories(driver=driver)
    books_list = []
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

    try:
        for category in category_list:      # Scrape for each category
            driver.get(category)

            while True:
                # Get all books that belong to a category
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
                    driver.execute_script("window.open(arguments[0]);", description_link)
                    driver.switch_to.window(driver.window_handles[1])  # switch to new tab

                    try:
                        description = driver.find_element(By.CSS_SELECTOR, "article.product_page > p").text.strip('“”"')
                    except NoSuchElementException:  # Handle books without descriptions
                        description = ""
                    
                    # After getting description, close the tab
                    driver.close()      
                    
                    # Switch back to category
                    driver.switch_to.window(driver.window_handles[0])
                    
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

if __name__ == "__main__":
    books_list = get_books()

    # Dump data in JSON format
    with open("./data/books.json", "w", encoding="utf-8") as file:
        json.dump(books_list, file, ensure_ascii=False, indent=4)
