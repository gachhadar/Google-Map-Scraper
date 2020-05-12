#########################################Libraries#####################################################
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
import time
import re
import requests
from lxml.html import fromstring
import csv
import datetime
import pandas as pd
import os
from pymongo import MongoClient
from email_finder import email_finder
######################################################################################################

class GoogleMapScraper:
    def __init__(self, db = False):
        self.url = "https://www.google.com/maps/?hl=en"
        
        if db:
            self.client = MongoClient()
            self.stores = self.client["Stores"]
            self.collection = self.stores["Fashion Store"]
    
    def setting_config(self):    
        options = webdriver.ChromeOptions()
        # options.add_argument("download.default_directory=D:/Upwork/Web Scraping Selenium/Trading Strategy/Data")
        options.add_argument("user-agent")
        options.add_argument("--disable-notifications")
        driver = webdriver.Chrome(executable_path = "C:\\chromedriver.exe")
        
        return driver

    def get_details(self):            

        sWebsite = None
        sPhone = None
        sAddress = None  
        sLocation = None      
        status = True
        dEmail = []
        
        for aResult in self.details1:
            label = aResult.find_element_by_xpath(".//span[1]").get_attribute("aria-label")
            sText = aResult.find_element_by_xpath(".//span[3]/span[@class='widget-pane-link']").text
            if label == "Address":
                sAddress = sText
            if label == "Website":
                sWebsite = sText
                sEmails = None
                if not sWebsite.isspace() and "." in sWebsite:
                    if "http" not in sWebsite:
                        sWebsite = "https://{}/".format(sWebsite)
                        # try:
                        #     dEmail = email_finder(url=sWebsite)
                        #     sEmails = ",".join(dEmail)
                        #     print(sEmails)
                        # except:
                        #     pass
                        
            if label == "Phone":
                sPhone = sText            
            if status and label is None:
                status = False
                sLocation = sText
        
        dOutput = {
                'location': sLocation,
                'address': sAddress,
                'phone': sPhone,
                'website': sWebsite,
                # "email": sEmails
            }
        
        return dOutput
    
    def search(self, **kwargs):
        driver = kwargs["driver"]
        SearchPlace = kwargs["key"]
        driver.get(self.url)  
        time.sleep(2)
        search = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@name='q']")))
        search.send_keys(SearchPlace)
        search.send_keys(Keys.RETURN)
        time.sleep(5)
        nCount = 0
        results = []
        nPage = 0  
        while True:
            sCurrentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %p")        
            nPage += 1
            print("INFO: {} Processing page {}".format(sCurrentTime, nPage))
            top_results =  driver.find_elements_by_xpath("//div[@class='section-result-content']")
            total = len(top_results)
            print(total)
            while nCount < total:
                try:
                    top_results =  driver.find_elements_by_xpath("//div[@class='section-result-content']")
                    name = top_results[nCount].find_element_by_xpath(".//div[1]/div[1]/div[2]/h3/span")
                    # sTitle = top_results[nCount].find_element_by_xpath(".//span[@class='section-result-details']")
                    #---------------Title------------------------#
                    sName = name.text
                    print("INFO: Processing {}".format(sName))
                    #---------------Name-------------------------#
                    button = top_results[nCount].find_element_by_xpath(".//div[1]/div[1]/div[2]/h3/button")
                    driver.execute_script("arguments[0].click();", button)
                    body = driver.find_element_by_tag_name("body")
                    body.send_keys(Keys.PAGE_DOWN)
                    body.send_keys(Keys.PAGE_DOWN)
                    time.sleep(5)
                    self.details1 = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='section-info-line']")))
                    aStore = driver.find_element_by_xpath("//span[@class='section-rating-term']/span[1]/button")
                    try:
                        rating = driver.find_element_by_xpath("//div[@class='section-rating']/div[1]/span[1]/span/span")
                        rating = rating.text
                    except:
                        rating = None
                    dOutput = self.get_details()
                    dOutput.update({"name": sName, "title": SearchPlace, "store":aStore.text, "rating": rating})
                    
                    aFind = self.collection.find_one({"name": sName})
                    if aFind is None:
                        self.collection.insert_one(dOutput)
                        
                    # self.writer.writerow(dOutput)
                    back = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[@class='section-back-to-list-button blue-link noprint']")))
                    driver.execute_script("arguments[0].click();", back)
                    time.sleep(1)
                    nCount += 1
                except Exception as ex:
                    print(str(ex))
                    nCount += 1
                        
            try:    
                nextpage = driver.find_element_by_xpath("//button[@id='n7lv7yjyC35__section-pagination-button-next']")
                nextpage.click()
                time.sleep(2)
                top_results = None                
            except:
                break
            
        driver.close()        
        print("Process complete")  

    def search_list_of_cities(self, country = None):
        url = "https://www.geonames.org/search.html"
        if not os.path.exists(os.path.join(os.getcwd(), "Country.csv")):
            session = requests.Session()
            oResponse = session.get(url)
            if oResponse.status_code == 200:
                tree = fromstring(oResponse.text)
                xCountryList = tree.xpath("//select[@name='country']/option/text()")
                xCountryCode = tree.xpath("//select[@name='country']/option/@value")
                
                pd.DataFrame({
                    'Code': xCountryCode,
                    'Country': xCountryList
                }).to_csv("Country.csv", index=None)
        
        xCountry = pd.read_csv("Country.csv")
        code = xCountry.loc[xCountry["Country"].str.strip() == country, ["Code"]]
        code = list(code["Code"].values)
        xResults = []
        if code != []:
            search = "{}?country={}".format(url, code[0])
            session = requests.Session()
            oResponse = session.get(search)
            tree = fromstring(oResponse.text)
            xResults = tree.xpath("//table[@class='restable']/tr/td[2]/a/text()")
            
        return xResults
                
if __name__ == "__main__":
    nTop = 10
    scrape = GoogleMapScraper()
    xCountryList = scrape.search_list_of_cities(country="Australia")
    
    for sCountry in xCountryList:
        driver= scrape.setting_config()
        print("Processing {}".format(sCountry))
        SearchPlace = "Ethical Fashion Stores near {}".format(sCountry)
        scrape.search(driver=driver,key=SearchPlace.lower())
    
    