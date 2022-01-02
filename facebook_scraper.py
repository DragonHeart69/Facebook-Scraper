###Addons
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as Wait
import selenium.webdriver.support.ui as UI
from selenium.common.exceptions import *
from urllib.parse import parse_qs,urlparse,unquote
from pathlib import PurePosixPath
import time
import re
import mysql.connector
import configparser
import sys

###Import settings.ini
settings = configparser.ConfigParser()
settings.read('settings.ini')

###DBConnection
try:
    mydb = mysql.connector.connect( host = settings['mysqlDB']['host'],
                                    user = settings['mysqlDB']['user'], 
                                    password = settings['mysqlDB']['pass'], 
                                    database = settings['mysqlDB']['db'])
except Exception as err:
    print("Error: " + str(err))
    sys.exit(1)


###Chrome Settings

chromeDriverPath = Service(settings['chrome']['driver'])
userdatadir = settings['chrome']['profile']
chromeOptions = webdriver.ChromeOptions() 
chromeOptions.add_argument(f'--user-data-dir={userdatadir}')
#!!!Enable this 2 lines only when you set a proxy server insite your settings file!!!#
#PROXY = settings['proxy']['proxy']
#chromeOptions.add_argument('--proxy-server=%s' % PROXY)
chromeOptions.add_argument('--disable-notifications')
chrome = webdriver.Chrome(service=chromeDriverPath, options=chromeOptions) 

###open site
chrome.get("https://m.facebook.com/home.php?sk=h_chr")
time.sleep(10)

###login
###cookie accept
try:
    button = Wait(chrome, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title='Alle cookies toestaan']"))).click()
except:
    pass
###target username & password & login
try:
    username = Wait(chrome, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']")))
    password = Wait(chrome, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass']")))
    username.clear()
    username.send_keys(settings['facebook-login']['username'])
    time.sleep(2)
    password.clear()
    password.send_keys(settings['facebook-login']['password'])
    time.sleep(3)
    button = Wait(chrome, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[name='login']"))).click()
except:
    pass

###scroll to buttom
while True:
    previous_height = chrome.execute_script('return document.body.scrollHeight')
    chrome.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    time.sleep(5)
    new_height= chrome.execute_script('return document.body.scrollHeight')
    if new_height == previous_height:
        break
chrome.execute_script('window.scrollTo(0, 0);')

###get all articles
links = chrome.find_elements(By.XPATH, "//a[@class='_26yo']")
hrefs =[]
for link in links:
    hrefs.append(link.get_attribute('href'))

###check if article already exist & scrapit 
mycursor = mydb.cursor(buffered=True)
for href in hrefs:
    tested_url = urlparse(href)
    try:
        tested_id = parse_qs(tested_url.query)['story_fbid'][0]
        find = "SELECT COUNT(*) FROM scraper where story_fbid = " + tested_id
        mycursor.execute(find)
        result=mycursor.fetchone()
        number_of_rows=result[0]
        if number_of_rows == 0:
            chrome.get(href)
            time.sleep(10)
            fbs_time = chrome.find_elements(By.XPATH, "//a[@class='_26yo']")
            authors = chrome.find_elements(By.XPATH, "//h3")
            texts = chrome.find_elements(By.XPATH, "//div[@class='_5rgt _5nk5']")
            for fb_time, author, text in zip(fbs_time, authors, texts):
                try:
                    link_date = fb_time.get_attribute('href')
                    parsed_url = urlparse(link_date)
                    try:
                        id = parse_qs(parsed_url.query)['id'][0]
                    except KeyError:
                        print(link_date)
                        id = None
                    try:
                        story_fbid = parse_qs(parsed_url.query)['story_fbid'][0]
                    except KeyError:
                        story_fbid = None
                    try:
                        time1 = parse_qs(parsed_url.query, keep_blank_values=True)['_ft_'][0]
                        times2 = re.split(':',time1)
                        for time2 in times2:
                            if time2.startswith("view_time"):
                                time3 = time2
                                time4 = time3.lstrip("view_time.")
                    except KeyError:
                        time4 = int(time.time())
                    sql = "INSERT INTO scraper (date, author, text, href, story_fbid, fb_id, status, needed) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    val = (time4, author.text, text.text, href, story_fbid, id, "new", "verify")
                    mycursor.execute(sql, val)
                    mydb.commit()
                    print(mycursor.rowcount, "record added.")
                    time.sleep(10)
                    chrome.find_element(By.XPATH, "//a[@class='_6j_c']").click()
                    time.sleep(10)
                except StaleElementReferenceException:
                    pass
        else:
            print(number_of_rows, "record already exists.")
    except KeyError:
        id = PurePosixPath(unquote(urlparse(href).path)).parts[3]
        story_fbid= PurePosixPath(unquote(urlparse(href).path)).parts[4]
        find = "SELECT COUNT(*) FROM scraper where story_fbid = " + story_fbid
        mycursor.execute(find)
        result=mycursor.fetchone()
        number_of_rows=result[0]
        if number_of_rows == 0:
            chrome.get(href)
            time.sleep(10)
            fbs_time = chrome.find_elements(By.XPATH, "//abbr[@data-sigil='timestamp']")
            authors = chrome.find_elements(By.XPATH, "//strong [@class='actor']")
            texts = chrome.find_elements(By.XPATH, "//div[@class='msg']/div")
            for fb_time, author, text in zip(fbs_time, authors, texts):
                try:
                    link_date = fb_time.get_attribute('data-store')
                    try:
                        time1 = link_date
                        times2 = re.split(',',time1)
                        for time2 in times2:
                            if time2.startswith('{"time":'):
                                time3 = time2
                                time4 = time3.lstrip('{"time":')
                    except KeyError:
                        time4 = int(time.time())
                
                    sql = "INSERT INTO scraper (date, author, text, href, story_fbid, fb_id, status, needed) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    val = (time4, author.text, text.text, href, story_fbid, id, "new", "verify")
                    mycursor.execute(sql, val)
                    mydb.commit()
                    print(mycursor.rowcount, "photo record added.")
                    time.sleep(10)
                    chrome.find_element(By.XPATH, "//a[@class='_6j_c']").click()
                    time.sleep(10)
                except StaleElementReferenceException:
                    pass
        else:
            print(number_of_rows, "photo record already exists.")
mycursor.close()

###find interessting items
mycursor = mydb.cursor(buffered=True)
find = "SELECT ID, needed FROM scraper where needed LIKE '%verify%' AND text LIKE '%werken%' OR text LIKE '%afsluit%' OR text LIKE '%afgesloten%' OR text LIKE '%ongeval%' GROUP BY ID"
mycursor.execute(find)
result = mycursor.fetchall()
number_of_rows=result[0]
if number_of_rows != 0:
    for ID, needed in result:
        sql  = "UPDATE scraper SET needed = 'interesting', status ='verify' where id = " + str(ID)
        mycursor.execute(sql)
        mydb.commit()
        print(mycursor.rowcount, "changed to interesting")
sql2 = "UPDATE scraper SET needed = 'archive', status ='archive' where needed LIKE '%verify%' "
mycursor.execute(sql2)
mydb.commit()
print(mycursor.rowcount, "referred to the archive")
mycursor.close()

mydb.close()

chrome.quit()

