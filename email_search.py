import requests
from pymongo import MongoClient
import re
from lxml.html import fromstring
import pandas as pd
def email_finder(url = None):
    link = '//a/@href'                                                  #get link xpath
    email_pat = r'[\w._]+@[._\-\w]+'                                    #email pattern
    aEmail = []
    xItems = []
    
    session = requests.Session()
    aResponse = session.get(url, timeout = 10)
    emails = re.findall(email_pat, aResponse.text)
    if emails != []:
        for mail in list(set(emails)):
            if "." in mail and ".gif" not in mail and ".png" not in mail and ".jpg" not in mail and ".jpeg" not in mail:
                aEmail.append(mail)
    else:
        if aResponse.status_code == 200:
            tree = fromstring(aResponse.text)
            
            xLinks = tree.xpath(link)
            for links in xLinks:
                if "contact" in links or "contact-us" in links or "about" in links or "about-us" in links:
                    sItem = links
                    if url not in links:
                        if links[0] == "/":
                            sItem = "{}{}".format(url,links[1:])
                        else:
                            sItem = "{}{}".format(url, links)
                    
                    xResponse = session.get(sItem, timeout = 10)
                    emails = re.findall(email_pat, xResponse.text)
                
                    if emails != []:
                        for mail in list(set(emails)):
                            if "." in mail and ".gif" not in mail and ".png" not in mail and ".jpg" not in mail and ".jpeg" not in mail:
                                aEmail.append(mail)
            
    return list(set(aEmail))
    
    
if __name__ == "__main__":
    df = pd.read_csv("sample.xlsx")
    xResults = []
    for url in df["URL"]:
        if "http" not in url:
            url = "https://{}/".format(url)
        print(url)
        xEmails = None
        try:
            xEmails = email_finder(url=url)
            xResults.append({
                "url": url,
                "email": ",".join(xEmails)
            })
        except:
            pass
        print(xEmails)
    df = pd.DataFrame(xResults, columns=["url","email"]).to_csv("results.csv", index=None)
    