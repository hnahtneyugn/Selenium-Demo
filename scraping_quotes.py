from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import json

path_to_brave = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
path_to_chromedriver = "/usr/local/bin/chromedriver"
url_to_crawl = "https://quotes.toscrape.com"
log_path = "./logs/quote_logging.txt"

def get_driver():
    options = Options()
    options.binary_location = path_to_brave

    service = webdriver.ChromeService(executable_path=path_to_chromedriver, log_output=log_path)

    driver = webdriver.Chrome(service=service, options=options)
    return driver

def get_quotes():
    driver = get_driver()
    driver.get(url=url_to_crawl)
    quotes_list = []

    try: 
        while True:
            quotes = driver.find_elements(By.CSS_SELECTOR, "div.quote")

            for quote in quotes:
                text = quote.find_element(By.CSS_SELECTOR, "span.text").text.strip('“”"')
                author = quote.find_element(By.CSS_SELECTOR, "small.author").text
                tags = quote.find_elements(By.CSS_SELECTOR, "a.tag")
                tag_list = [tag.text for tag in tags]
                info = {"Text": text, "Author": author, "Tags": tag_list}
                quotes_list.append(info)
            
            try:
                next_page = driver.find_element(By.CSS_SELECTOR, "ul.pager > li.next > a")
                next_page_link = next_page.get_attribute("href")

                if not next_page_link:
                    break
            
                driver.get(next_page_link)

            except Exception as e:
                print(e)
                break
        
    finally:
        driver.quit()
    
    return quotes_list


if __name__ == "__main__":
    quotes_list = get_quotes()
    with open("./data/quotes.json", "w", encoding="utf-8") as file:
        json.dump(quotes_list, file, ensure_ascii=False, indent=4)
