import pandas as pd 
import requests 
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
# from requests.packages.urllib3.poolmanager import PoolManager
import time
import cloudscraper
import urllib3

# import ssl

# class MyAdapter(HTTPAdapter):
#     def init_poolmanager(self, connections, maxsize, block=False):
#         self.poolmanager = PoolManager(num_pools=connections,
#                                 maxsize=maxsize,
#                                 block=block,
#                                 ssl_version=ssl.PROTOCOL_TLSv1)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

df = pd.read_csv('Websites.csv')
output_data = pd.DataFrame(columns=['url', 'status', 'access_denied', 'data', 'has_captcha', 'end_result'])
number_urls = df.shape[0]

i = 0

for url in df['urls']:

    session = requests.Session()
    # retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=3)
    adapter.max_retries.respect_retry_after_header = False
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    # if url.startswith('http'):
    #     url = url
    # elif url.startswith('https'):
    #     url = url
    # else:
    #     url = ('https://' + url)

    print(url)

    ua = UserAgent()
    header = {'User-Agent':str(ua.chrome)}
    
    try:
        # Status
        start = time.time()
        response = session.get(url, headers={"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}, verify=False, timeout=0.5)
        request_time = time.time() - start
        info = "Request completed in {0:.0f}ms".format(request_time)
        print(info)
        status = response.status_code
        if (status == 200):
            status = "Connection Successful"
        if (status == 404):
            status = "404 Error"
        if (status == 403):
            status = "403 Error"
        if (status == 503):
            status = "503 Error"
        print(status)

        # Access Denied
        def access():
            start = time.time()
            soup = BeautifulSoup(response.content, 'html.parser')
            results = soup.find()
            job_elems = results.find_all('title')
            access_denied = "Access denied" in str(job_elems)
            access_time = time.time() - start
            access_info = "Access() function completed in {0:.0f}ms".format(access_time)
            print(access_info)
            return access_denied
        
        # Is there any data there?
        def any_data():
            start = time.time()
            soup = BeautifulSoup(response.content, 'html.parser')
            results = soup.find()
            job_elems = results.find_all('span')
            if str(job_elems) == "[]":
                any_data = "No Data"
            else:
                any_data = "Data Available"
            data_time = time.time() - start
            data_info = "Any_Data() function completed in {0:.0f}ms".format(data_time)
            print(data_info)
            return any_data

        def has_captcha():
            start = time.time()
            try:
                scraper = cloudscraper.create_scraper()
                response = scraper.get(url, timeout=0.5)
                captcha = False
            except cloudscraper.exceptions.CloudflareChallengeError:
                captcha = True
            except cloudscraper.exceptions.CloudflareCode1020:
                captcha = "N/A"
            except cloudscraper.exceptions.CloudflareCaptchaProvider:
                captcha = True
            captcha_time = time.time() - start
            captcha_info = "has_captcha() function completed in {0:.0f}ms".format(captcha_time)
            print(captcha_info)
            return captcha

        if (status == "404 Error"):
            output_data.loc[i] = [df.iloc[i, 0], status, "N/A", "N/A", "N/A", "Dead"]
        else:
            if access() == True:
                access =  "TRUE"
                end_result = "Blocked"
            else:
                access = "FALSE"
                if any_data() == "No Data":
                    any_data = "No Data"
                    has_captcha = "N/A"
                    end_result = "Dead"
                else:
                    any_data = "Data Available"
                    if status == "Connection Successful":
                            end_result = "Working"
                            if has_captcha() == True:
                                has_captcha = "Captcha Required"
                                end_result = "Captcha Required"
                            else:
                                has_captcha = "No Captcha"
                    else:
                        end_result = "Dead"
                        if has_captcha() == True:
                            has_captcha = "Captcha Required"
                            end_result = "Captcha Required"
                        else:
                            has_captcha = "No Captcha"
            output_data.loc[i] = [df.iloc[i, 0], status, access, any_data, has_captcha, end_result]

        i += 1

    except requests.exceptions.Timeout:
        status = "Connection Timed Out"
        access = "N/A"
        any_data = "N/A"
        captcha = "N/A"
        end_result = "Dead"
        print(status)
        request_time = time.time() - start
        info = "TimeOut in {0:.0f}ms".format(request_time)
        print(info)

        output_data.loc[i] = [df.iloc[i, 0], status, access, any_data, captcha, end_result]
        i += 1

    except requests.exceptions.ConnectionError:
        status = "Connection Refused"
        access = "N/A"
        any_data = "N/A"
        captcha = "N/A"
        end_result = "Dead"
        print(status)
        request_time = time.time() - start
        info = "Connection Error in {0:.0f}ms".format(request_time)
        print(info)

        output_data.loc[i] = [df.iloc[i, 0], status, access, any_data, captcha, end_result]
        i += 1

output_data.to_csv('dead_blocked.csv', index=False)
print('CSV file created!')
