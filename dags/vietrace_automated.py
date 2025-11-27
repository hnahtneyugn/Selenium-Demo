from airflow.sdk import dag, task
from airflow.providers.standard.operators.python import PythonOperator
import pendulum
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import csv
import logging
import pandas as pd
import psycopg2
import time

path_to_brave = "/usr/bin/brave-browser"
path_to_chromedriver = "/usr/local/bin/chromedriver"
url_to_crawl = "https://vietrace365.vn/races/25-000-km-move-on-run-more"

@dag(
    dag_id = "automated_vietrace_scraper",
    description = "Scraping Vietrace 365 Data (TaskFlow API)",
    schedule="*/10 * * * *",
    start_date= pendulum.datetime(2025, 11, 27, tz='Asia/Ho_Chi_Minh'),
    catchup=False,
    tags=["web-scraping", "vietrace"]
)

def main_dag():

    @task(retries=3, retry_delay=pendulum.duration(seconds=30), do_xcom_push=True)
    def scrape(**context):
        def get_paths():
            log_path = f"/opt/airflow/logs/vietrace/{pendulum.now('Asia/Ho_Chi_Minh').strftime('%Y%m%d_%H%M%S')}.log"
            data_output_path = f"/opt/airflow/data/vietrace/{pendulum.now('Asia/Ho_Chi_Minh').strftime('%Y%m%d_%H%M%S')}_scoreboard.csv"
        
            return log_path, data_output_path
        

        def get_driver(log_path):
            options = Options()
            options.binary_location = path_to_brave
            options.add_argument("--headless")  # No GUI when crawling data
            options.add_argument("--window-size=1920,1080") # Fixed window-size
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu") 
            options.add_argument("--disable-extensions")

            # Specify Chromedriver path and path to log file
            service = webdriver.ChromeService(executable_path=path_to_chromedriver, log_output=log_path)

            # Create a Brave WebDriver by using Chromedriver + Brave binary
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        
        def get_scoreboard(log_path):
            driver = get_driver(log_path=log_path)
            driver.get(url=url_to_crawl)
            scoreboard = []
            
            wait = WebDriverWait(driver=driver, timeout=30)
            
            buttons = driver.find_elements(By.CSS_SELECTOR, "div.tabs.race-content-tabs.ng-isolate-scope ul li")
            link = buttons[3].find_element(By.TAG_NAME, "a")
            driver.execute_script("arguments[0].click();", link)
            
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.racer-list-table")))
            
            try:
                page_count = 0
                while True:
                    page_count += 1
                    logging.info(f"Processing page {page_count}")
                    
                    # Wait for table to be stable
                    time.sleep(2)  # Give the page time to fully render
                    
                    # Wait until rows are loaded
                    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "table.racer-list-table > tbody > tr")) > 0)
                    
                    # Re-fetch elements on each iteration to avoid stale references
                    first_scroll_div = driver.find_element(By.CSS_SELECTOR, "div.vertical-scroll")
                    athletes = first_scroll_div.find_elements(By.CSS_SELECTOR, "table.racer-list-table > tbody > tr")
                    visible_athletes = [a for a in athletes if a.is_displayed()]
                    
                    logging.info(f"Found {len(visible_athletes)} visible athletes on page {page_count}")
                    
                    # Process each athlete immediately (don't store elements)
                    for i, athlete in enumerate(visible_athletes):
                        try:
                            # Re-fetch the element to avoid stale reference
                            first_scroll_div = driver.find_element(By.CSS_SELECTOR, "div.vertical-scroll")
                            current_athletes = first_scroll_div.find_elements(By.CSS_SELECTOR, "table.racer-list-table > tbody > tr")
                            current_visible = [a for a in current_athletes if a.is_displayed()]
                            
                            if i >= len(current_visible):
                                logging.warning(f"Skipping index {i} - element no longer available")
                                continue
                                
                            athlete = current_visible[i]
                            
                            rank = athlete.find_element(By.CSS_SELECTOR, "td.race-result-item-count > span").text.strip()
                            name = athlete.find_element(By.CSS_SELECTOR, "td.race-result-item-name span.user-name").text.strip()
                            department = athlete.find_element(By.CSS_SELECTOR, "td.race-result-item-name span.text-info").text.strip()
                            staff_code = athlete.find_element(By.CSS_SELECTOR, "td.race-result-item-name span.visible-xs-inline").get_attribute("textContent").strip()
                            run_distance = athlete.find_element(By.XPATH, ".//span[@ng-bind=\"racer.distanceByTypes['Run']|number:1\"]").text.strip()
                            walk_distance = athlete.find_element(By.XPATH, ".//span[@ng-bind=\"racer.distanceByTypes['Walk']|number:1\"]").text.strip()
                            
                            result_td = athlete.find_element(By.CSS_SELECTOR, "td.race-result-item-result")
                            total_distance = result_td.find_element(By.XPATH, ".//span[contains(@ng-bind, 'racer.complete')]").text.strip()
                            
                            pace_text = result_td.find_element(By.XPATH, ".//span[contains(@ng-bind, 'racer.avgPace')]").text.strip()
                            
                            # Handle pace parsing safely
                            pace_minutes = "0"
                            pace_seconds = "0"
                            if pace_text and ":" in pace_text:
                                pace_parts = pace_text.split(":")
                                if len(pace_parts) >= 2:
                                    pace_minutes = pace_parts[0]
                                    pace_seconds = pace_parts[1]
                                else:
                                    logging.warning(f"Unexpected pace format: {pace_text}")
                            
                            speed = result_td.find_element(By.XPATH, ".//span[contains(@ng-bind, 'racer.avgSpeed')]").text.strip()
                            
                            logging.info(f"Processed: {rank} - {name}")
                            
                            scoreboard.append((rank, name, department, staff_code, run_distance, walk_distance,
                                            total_distance, pace_minutes, pace_seconds, speed))
                        
                        except Exception as e:
                            logging.error(f"Error processing athlete at index {i}: {str(e)}")
                            continue
                    
                    # Store last rank before pagination
                    try:
                        current_athletes = driver.find_elements(By.CSS_SELECTOR, "table.racer-list-table > tbody > tr")
                        last_rank_on_page = current_athletes[-1].find_element(
                            By.CSS_SELECTOR, "td.race-result-item-count > span"
                        ).text.strip()
                    except:
                        logging.info("Could not get last rank, assuming last page")
                        break
                    
                    # Check for next button
                    try:
                        li_list = driver.find_elements(By.CSS_SELECTOR, "div.ng-scope > div.racer-list > nav > ul > li")
                        logging.info(f"Total pagination elements: {len(li_list)}")
                        
                        next_button_li = None
                        for li in li_list:
                            if "pagination-next" in li.get_attribute("class"):
                                next_button_li = li
                                break
                        
                        if next_button_li is None or "disabled" in next_button_li.get_attribute("class"):
                            logging.info("Reached last page!")
                            break
                        
                        # Click next page
                        next_button = next_button_li.find_element(By.TAG_NAME, "a")
                        driver.execute_script("arguments[0].click();", next_button)
                        
                        # Wait for page to change with better condition
                        wait.until(lambda d: d.find_element(
                            By.CSS_SELECTOR, 
                            "table.racer-list-table > tbody > tr:first-child td.race-result-item-count > span"
                        ).text.strip() != last_rank_on_page)
                        
                        # Additional wait for stability
                        time.sleep(2)
                        
                    except NoSuchElementException:
                        logging.info("No more pages")
                        break
                    except TimeoutException:
                        logging.warning("Timeout waiting for next page, assuming we're done")
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
        
        # Task execution
        log_path, data_output_path = get_paths()

        scoreboard = get_scoreboard(log_path=log_path)
        write_to_csv(data=scoreboard, data_path=data_output_path)

        logging.info(f"Saved scoreboard to {data_output_path}")

        # Push data_output_path to XComs
        return data_output_path


    @task(retries=3, retry_delay=pendulum.duration(seconds=30))
    def insert_data(**context):
        # Read data output path from XComs
        data_output_path = context["ti"].xcom_pull(task_ids="scrape", key="return_value")

        # Read CSV into a Pandas DataFrame
        df = pd.read_csv(data_output_path, header=0)

        # Connect to PostgreSQL DB inside Docker Compose
        conn = psycopg2.connect(
            host="postgres",
            port=5432,
            database="airflow",
            user="airflow",
            password="airflow"
        )
        cur = conn.cursor()

        # Create table
        cur.execute(query="""
        DROP TABLE IF EXISTS vietrace;
                    
        CREATE TABLE vietrace (
        RANK INT PRIMARY KEY,
        NAME TEXT,
        DEPARTMENT TEXT,
        STAFFCODE TEXT,
        RUN_DISTANCE DOUBLE PRECISION,
        WALK_DISTANCE DOUBLE PRECISION,
        TOTAL_DISTANCE DOUBLE PRECISION,
        PACE_MINUTES TEXT,
        PACE_SECONDS TEXT,
        SPEED DOUBLE PRECISION);
        """)


        # Iterate through each row and insert into DB
        for _, row in df.iterrows():
            cur.execute(
                """
                INSERT INTO vietrace (
                    RANK,
                    NAME,
                    DEPARTMENT,
                    STAFFCODE,
                    RUN_DISTANCE,
                    WALK_DISTANCE,
                    TOTAL_DISTANCE,
                    PACE_MINUTES,
                    PACE_SECONDS,
                    SPEED
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row['Rank'],
                    row['Name'],
                    row['Department'],
                    row['Staff Code'],
                    row['Run Distance (km)'],
                    row['Walk Distance (km)'],
                    row['Total Distance (km)'],
                    row['Pace Minutes'],
                    row['Pace Seconds'],
                    row['Speed (km/h)'],
                )
            )

        conn.commit()
        cur.close()
        conn.close()

        # Finished loading data
        logging.info("CSV data loaded into PostgreSQL!")

    scrape() >> insert_data()

main_dag()    
