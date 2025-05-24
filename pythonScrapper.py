import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pandas as pd
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import traceback
import sys
import os

def scrape_rera_odisha_project_list():
    driver = None
    try:
        print("Setting up Chrome options...")
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # Updated headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        print("Initializing Chrome driver...")
        try:
            # Try to use the system Chrome driver first
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Error with system Chrome driver: {str(e)}")
            print("Trying webdriver-manager...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set user agent
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        print("Loading page...")
        driver.get("https://rera.odisha.gov.in/projects/project-list")
        
        # Wait for page to load completely
        time.sleep(5)  # Initial wait for page load
        
        print("Waiting for table to load...")
        wait = WebDriverWait(driver, 45)  # Increased timeout to 45 seconds
        
        # Try different selectors for the table
        selectors = [
            (By.TAG_NAME, "table"),
            (By.CLASS_NAME, "table"),
            (By.CSS_SELECTOR, "table.table"),
            (By.XPATH, "//table")
        ]
        
        table = None
        for by, selector in selectors:
            try:
                print(f"Please wait, trying to find table with selector: {selector}")
                table = wait.until(EC.presence_of_element_located((by, selector)))
                if table:
                    print(f"Found table with selector: {selector}")
                    break
            except:
                continue
        
        if not table:
            # Save page source for debugging
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("Saved page source to debug_page.html")
            return None
        
        print("Table found, extracting data...")
        
        # Get the table HTML and parse it with BeautifulSoup
        table_html = table.get_attribute('outerHTML')
        soup = BeautifulSoup(table_html, 'html.parser')
        
        # Extract headers
        headers = []
        thead = soup.find('thead')
        if thead:
            for th in thead.find_all('th'):
                headers.append(th.get_text(strip=True))
        
        if not headers:
            print("No headers found in table")
            return None
            
        # Extract rows
        data = []
        rows = soup.find_all('tr')
        for row in rows[1:]:  # Skip header row
            row_data = []
            for cell in row.find_all(['td', 'th']):
                row_data.append(cell.get_text(strip=True))
            if row_data:  # Only add if we got data
                data.append(row_data)
        
        if not data:
            print("No data rows found in table")
            return None
        
        # Create DataFrame
        df = pd.DataFrame(data, columns=headers[:len(data[0])] if data else headers)
        
        return df
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("\nDetailed error information:")
        traceback.print_exc()
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def extract_projects_from_html(html_file, n=10):
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    projects = []
    cards = soup.select('.card.project-card')
    for card in cards[:n]:
        proj = {}
        # Project Name
        name = card.select_one('.card-title')
        proj['Project Name'] = name.get_text(strip=True) if name else ''
        # Promoter Name
        promoter = card.select_one('small')
        proj['Promoter Name'] = promoter.get_text(strip=True) if promoter else ''
        # Rera Regd. No
        rera = card.select_one('.fw-bold.me-2')
        proj['Rera Regd. No'] = rera.get_text(strip=True) if rera else ''
        # Address
        address = ''
        for label in card.select('.label-control'):
            if 'Address' in label.get_text():
                strong = label.find_next('strong')
                address = strong.get_text(strip=True) if strong else ''
                break
        proj['Address'] = address
        # Project Type
        ptype = ''
        for label in card.select('.label-control'):
            if 'Project Type' in label.get_text():
                strong = label.find_next('strong')
                ptype = strong.get_text(strip=True) if strong else ''
                break
        proj['Project Type'] = ptype
        # Started From
        started = ''
        for label in card.select('.label-control'):
            if 'Started From' in label.get_text():
                strong = label.find_next('strong')
                started = strong.get_text(strip=True) if strong else ''
                break
        proj['Started From'] = started
        # Possession by
        possession = ''
        for label in card.select('.label-control'):
            if 'Possession by' in label.get_text():
                strong = label.find_next('strong')
                possession = strong.get_text(strip=True) if strong else ''
                break
        proj['Possession by'] = possession
        projects.append(proj)
    print(f"First {n} projects from debug_page.html:")
    for p in projects:
        print(p)

if __name__ == "__main__":
    extract_projects_from_html('debug_page.html', n=6)
    # print("Starting RERA Odisha project list scraper...")
    # project_list = scrape_rera_odisha_project_list()
    
    # if project_list is not None:
    #     print("\nSuccessfully scraped project list:")
    #     print(project_list.head())
        
    #     # Save to CSV
    #     csv_file = 'rera_odisha_projects.csv'
    #     project_list.to_csv(csv_file, index=False, encoding='utf-8-sig')
    #     print(f"\nData saved to '{csv_file}'")
        
    #     # Print some stats
    #     print(f"\nTotal projects scraped: {len(project_list)}")

    