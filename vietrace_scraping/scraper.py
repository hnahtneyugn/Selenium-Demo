from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import csv
import time

# Specify paths
path_to_brave = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
path_to_chromedriver = "/usr/local/bin/chromedriver"
url_to_crawl = "https://vietrace365.vn/races/25-000-km-move-on-run-more"
log_path = "./logs/vietrace/race.log"
path_to_csv = "./data/vietrace/scoreboard.csv"

def get_driver():
    options = Options()
    options.binary_location = path_to_brave
    # options.add_argument("--headless")  # No GUI when crawling data
    options.add_argument("--window-size=1920,1080") # Fixed window-size

    # Specify Chromedriver path and path to log file
    service = webdriver.ChromeService(executable_path=path_to_chromedriver, log_output=log_path)

    # Create a Brave WebDriver by using Chromedriver + Brave binary
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def get_scoreboard():
    driver = get_driver()
    driver.get(url=url_to_crawl)    # Navigate to Vietrace website
    scoreboard = []

    wait = WebDriverWait(driver=driver, timeout=20)     # Wait 20 secs for each instance

    # Find the element which shows the scoreboard table
    buttons = driver.find_elements(By.CSS_SELECTOR, "div.tabs.race-content-tabs.ng-isolate-scope ul li")
    link = buttons[3].find_element(By.TAG_NAME, "a")

    # Click the <a> via JS
    driver.execute_script("arguments[0].click();", link)

    try:
        while True:
            # Wait until all tr elements from the table are loaded
            wait.until(lambda d: all(tr.text.strip() != '' 
                             for tr in d.find_elements(By.CSS_SELECTOR, "table.racer-list-table > tbody > tr")))

            # Get the scroll with the content only
            first_scroll_div = driver.find_element(By.CSS_SELECTOR, "div.vertical-scroll")
            athletes = first_scroll_div.find_elements(By.CSS_SELECTOR, "table.racer-list-table > tbody > tr")
            print(f"Total elements found: {len(athletes)}")

            # Check how many athletes are actually visible
            visible_athletes = [a for a in athletes if a.is_displayed()]
            print(f"Visible elements: {len(visible_athletes)}")

            for athlete in athletes:
                # Get information for each athlete
                rank = athlete.find_element(By.CSS_SELECTOR, "td.race-result-item-count > span").text.strip()
                name = athlete.find_element(By.CSS_SELECTOR, "td.race-result-item-name span.user-name").text.strip()
                department = athlete.find_element(By.CSS_SELECTOR, "td.race-result-item-name span.text-info").text.strip()
                staff_code = athlete.find_element(By.CSS_SELECTOR, "td.race-result-item-name span.visible-xs-inline").get_attribute("textContent").strip()
                run_distance = athlete.find_element(By.XPATH,".//span[@ng-bind=\"racer.distanceByTypes['Run']|number:1\"]").text.strip()
                walk_distance = athlete.find_element(By.XPATH,".//span[@ng-bind=\"racer.distanceByTypes['Walk']|number:1\"]").text.strip()

                result_td = athlete.find_element(By.CSS_SELECTOR, "td.race-result-item-result")
                total_distance = result_td.find_element(By.XPATH, ".//span[contains(@ng-bind, 'racer.complete')]").text.strip()
                
                pace_text = result_td.find_element(By.XPATH, ".//span[contains(@ng-bind, 'racer.avgPace')]").text.strip()
                pace_parts = pace_text.split(":")   
                pace_minutes = pace_parts[0]
                pace_seconds = pace_parts[1]
                speed = result_td.find_element(By.XPATH, ".//span[contains(@ng-bind, 'racer.avgSpeed')]").text.strip()

                # For debugging

                # print(total_distance)
                # print(staff_code)
                # print(rank)
                # print(name) 
                # print(department)
                # print(pace_text)
                # print(pace_parts)

                # Store the data inside a list of tuples
                scoreboard.append((rank, name, department, staff_code, run_distance, walk_distance, \
                                   total_distance, pace_minutes, pace_seconds, speed))
                
            try:
                # Find all the buttons below the table
                li_list = driver.find_elements(By.CSS_SELECTOR, "div.ng-scope > div.racer-list > nav > ul > li")
                print(f"Total pagination li elements: {len(li_list)}")

                # Find the FIRST next button (not the disabled one)
                next_button_li = None
                for li in li_list:
                    if "pagination-next" in li.get_attribute("class"):
                        next_button_li = li
                        break 
                
                if next_button_li is None:
                    print("No next button found!")
                    break

                # If we're in the last page, break the loop
                if "disabled" in next_button_li.get_attribute("class"):
                    print("Reached last page!")
                    break

                # Otherwise, move to the next page
                next_button = next_button_li.find_element(By.TAG_NAME, "a")
                driver.execute_script("arguments[0].click();", next_button)

            except NoSuchElementException as e:
                break

    finally:
        driver.quit()
    
    return scoreboard

def write_to_csv(data, data_path):
    headers = [
        "Rank", "Name", "Department", "Staff Code", 
        "Run Distance (km)", "Walk Distance (km)", 
        "Total Distance (km)", "Pace Minutes", "Pace Seconds", "Speed (km/h)"
    ]

    # Write each row into a CSV 
    with open(data_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)

if __name__ == "__main__":
    scoreboard = get_scoreboard()
    write_to_csv(data=scoreboard, data_path=path_to_csv)

    print("All done!")
