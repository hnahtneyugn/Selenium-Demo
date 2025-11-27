from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import json

# Specify paths
path_to_brave = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
path_to_chromedriver = r"C:\Windows\chromedriver.exe"
url_to_crawl = "https://quotes.toscrape.com"
log_path = "./logs/quote_logging.txt"

def get_driver():
    options = Options()
    options.binary_location = path_to_brave

    # Specify Chromedriver path and path to log file
    service = webdriver.ChromeService(executable_path=path_to_chromedriver, log_output=log_path)

    # Create a Brave WebDriver by using Chromedriver + Brave binary
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def get_quotes():
    driver = get_driver()           
    driver.get(url=url_to_crawl)    # Navigate to https://quotes.to.scrape.com/
    quotes_list = []

    try: 
        while True:
            # Get all quotes from main page
            quotes = driver.find_elements(By.CSS_SELECTOR, "div.quote") 

            for quote in quotes:   
                # For each quote, get quote, its author, tag list
                text = quote.find_element(By.CSS_SELECTOR, "span.text").text.strip('“”"')   
                author = quote.find_element(By.CSS_SELECTOR, "small.author").text
                tags = quote.find_elements(By.CSS_SELECTOR, "a.tag")
                tag_list = [tag.text for tag in tags]
                info = {"Text": text, "Author": author, "Tags": tag_list}
                quotes_list.append(info)    # Store each quote as a dict
            
            try:
                # Find URL to the next page
                next_page = driver.find_element(By.CSS_SELECTOR, "ul.pager > li.next > a")
                next_page_link = next_page.get_attribute("href")

                # If we're in the last page, break the loop
                if not next_page_link:
                    break
            
                # Otherwise, move to next page and keep getting quotes
                driver.get(next_page_link)

            except Exception as e:
                print(e)
                break
        
    finally:
        driver.quit()   # exit browser
    
    return quotes_list


if __name__ == "__main__":
    quotes_list = get_quotes()
    
    # Dump data in JSON format
    with open("./data/quotes.json", "w", encoding="utf-8") as file:
        json.dump(quotes_list, file, ensure_ascii=False, indent=4)
