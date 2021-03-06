from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.common.exceptions import *
from urllib.parse import parse_qs,urlparse,unquote
from pathlib import PurePosixPath
import time
import re
import mysql.connector
import configparser
import sys

while 1:
    ###Import settings.ini
    settings = configparser.ConfigParser()
    settings.read('settings.ini')

    ###DBConnection
    try:
        mydb = mysql.connector.connect( host = settings['mysqlDB']['host'],
                                        user = settings['mysqlDB']['user'], 
                                        password = settings['mysqlDB']['pass'], 
                                        database = settings['mysqlDB']['db'], 
                                        charset='utf8mb4')
    except Exception as err:
        print("Error: " + str(err))
        sys.exit(1)
    mycursor = mydb.cursor(buffered=True)
    mycursor.execute("set names utf8mb4;")
    ###Create DB if not exist
    mycursor.execute('''CREATE TABLE IF NOT EXISTS {tab} (
    `ID` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `date` bigint(20) NOT NULL,
    `author` varchar(255) DEFAULT NULL,
    `text` longtext DEFAULT NULL,
    `href` varchar(255) NOT NULL,
    `story_fbid` varchar(254) NOT NULL,
    `fb_id` varchar(254) NOT NULL,
    `status` varchar(254) NOT NULL,
    `needed` varchar(254) NOT NULL
    );'''.format(tab=settings['mysqlDB']['table']))
    mydb.commit()
    mycursor.close()
    mydb.close()

    ###Chrome Settings
    print("Set Chrome settings") 
    chromeOptions = webdriver.ChromeOptions()
    if settings['chrome_windows']['state'] == 'true':
        chromeDriverPath = Service(settings['chrome_windows']['driver'])
        userdatadir = settings['chrome_windows']['profile']
    if settings['chrome_docker']['state'] == "true":
        chromeDriverPath = Service(settings['chrome_docker']['driver'])
        userdatadir = settings['chrome_docker']['profile']
    chromeOptions.add_argument(f'--user-data-dir={userdatadir}')
    if settings['proxy']['state'] == 'true':
        PROXY = settings['proxy']['proxy']
        chromeOptions.add_argument('--proxy-server=%s' % PROXY)
    if settings['headless']['state'] == 'true':
        chromeOptions.add_argument("--headless")
    chromeOptions.add_argument("--no-sandbox")
    chromeOptions.add_argument("--disable-dev-shm-usage")
    chrome = webdriver.Chrome(service=chromeDriverPath, options=chromeOptions) 
    chrome.execute_cdp_cmd("Page.setBypassCSP", {"enabled": True})
    ###open site
    print("Open timeline on Most Recent")
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
        print("Try to login")
        username = Wait(chrome, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']")))
        password = Wait(chrome, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass']")))
        username.clear()
        username.send_keys(settings['facebook-login']['username'])
        time.sleep(2)
        password.clear()
        password.send_keys(settings['facebook-login']['password'])
        time.sleep(3)
        button = Wait(chrome, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[name='login']"))).click()
        print("Logged In")
        time.sleep(10)
        chrome.get("https://m.facebook.com/home.php?sk=h_chr")
        time.sleep(10)
    except:
        print("Already Logged In")
        pass
    
    if settings['scroll-time']['state'] == 'true':
        times = settings['scroll-time']['times']
        print("Scroll "+times+" times")
        for i in range(int(times)): 
            ActionChains(chrome).send_keys(Keys.END).perform()
            time.sleep(3)
    else:
        ###scroll to buttom
        print("Scroll to te buttom & back up")
        while True:
            previous_height = chrome.execute_script('return document.body.scrollHeight')
            chrome.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            time.sleep(5)
            new_height= chrome.execute_script('return document.body.scrollHeight')
            if new_height == previous_height:
                break
    chrome.execute_script('window.scrollTo(0, 0);')

    ###get all articles
    print("Get all the links to the Articles")
    links = chrome.find_elements(By.XPATH, "//a[@class='_26yo']")
    hrefs =[]
    for link in links:
        hrefs.append(link.get_attribute('href'))
        
    ###DBConnection
    try:
        mydb = mysql.connector.connect( host = settings['mysqlDB']['host'],
                                        user = settings['mysqlDB']['user'], 
                                        password = settings['mysqlDB']['pass'], 
                                        database = settings['mysqlDB']['db'], 
                                        charset='utf8mb4')
    except Exception as err:
        print("Error: " + str(err))
        sys.exit(1)
    mycursor = mydb.cursor(buffered=True)

    ###check if article already exist & scrapit 
    for href in hrefs:
        tested_url = urlparse(href)
        try:
            tested_id = parse_qs(tested_url.query)['story_fbid'][0]
            find = "SELECT COUNT(*) FROM " + settings['mysqlDB']['table'] + " where story_fbid = " + tested_id
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
                        parsed = urlparse(href)
                        new_netloc = 'https://www.facebook.com'
                        new_path = parsed.path
                        new_query = parsed.query
                        new_link = new_netloc+new_path+ '?' +new_query
                        sql = "INSERT INTO " + settings['mysqlDB']['table'] + " (date, author, text, href, story_fbid, fb_id, status, needed) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                        val = (time4, author.text, text.text, new_link, story_fbid, id, "new", "verify")
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
            try:
                id = PurePosixPath(unquote(urlparse(href).path)).parts[3]
                story_fbid= PurePosixPath(unquote(urlparse(href).path)).parts[4]
                find = "SELECT COUNT(*) FROM " + settings['mysqlDB']['table'] + " where story_fbid = " + story_fbid
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
                            parsed = urlparse(href)
                            new_netloc = 'https://www.facebook.com'
                            new_path = parsed.path
                            new_link = new_netloc+new_path
                            sql = "INSERT INTO " + settings['mysqlDB']['table'] + " (date, author, text, href, story_fbid, fb_id, status, needed) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                            val = (time4, author.text, text.text, new_link, story_fbid, id, "new", "verify")
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
            except:
                pass
    mycursor.close()
    mydb.close()
    chrome.quit()
    
    ###DBConnection
    try:
        mydb = mysql.connector.connect( host = settings['mysqlDB']['host'],
                                        user = settings['mysqlDB']['user'], 
                                        password = settings['mysqlDB']['pass'], 
                                        database = settings['mysqlDB']['db'], 
                                        charset='utf8mb4')
    except Exception as err:
        print("Error: " + str(err))
        sys.exit(1)
    mycursor = mydb.cursor(buffered=True)

    ###find interessting items
    find = "SELECT ID, needed FROM " + settings['mysqlDB']['table'] + " WHERE needed = 'verify' AND (" + settings['check']['query'] + ") GROUP BY ID"
    mycursor.execute(find)
    del result
    result = mycursor.fetchall()
    try:
        number_of_rows=result[0]
        if number_of_rows != 0:
            for ID, needed in result:
                sql  = "UPDATE " + settings['mysqlDB']['table'] + " SET needed = 'interesting', status ='verify' WHERE ID = " + str(ID)
                mycursor.execute(sql)
                mydb.commit()
                print(mycursor.rowcount, "changed to interesting")
        del result
    except:
        print ("no records match your search")
    try:
        sql2 = "UPDATE " + settings['mysqlDB']['table'] + " SET needed = 'archive', status ='archive' WHERE needed = 'verify' "
        mycursor.execute(sql2)
        mydb.commit()
        print(mycursor.rowcount, "referred to the archive")
    except:
        print("notting to do")
    try:
        sql3 = "DELETE FROM " + settings['mysqlDB']['table'] + " WHERE date < UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))"
        mycursor.execute(sql3)
        mydb.commit()
        print("All record older then 30 days removed from database")
        mycursor.close()
        mydb.close()
    except:
        print("notting to do")
        mycursor.close()
        mydb.close()
    def countdown(t):
        while t:
            mins, secs = divmod(t, 60) 
            hours, mins = divmod(mins, 60)
            timer = '{:02d}:{:02d}:{:02d}'.format(hours, mins, secs) 
            print(timer, end="\r") 
            time.sleep(1) 
            t -= 1

    if settings['loop-time']['state'] == "true":
        t = int(settings['loop-time']['seconds'])
    else:
        sys.exit(1)

    countdown(int(t))