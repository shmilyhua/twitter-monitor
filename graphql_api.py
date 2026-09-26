import logging
import time
import json
import os
import glob

import bs4
import requests
from x_client_transaction.utils import generate_headers, handle_x_migration, get_ondemand_file_url
from x_client_transaction import ClientTransaction

from utils import check_initialized


class GraphqlAPI():
    initialized = False

    def __new__(cls):
        raise Exception('Do not instantiate this class!')

    @classmethod
    def init(cls) -> None:
        cls.logger = logging.getLogger('api')
        while not cls.update_api_data():
            time.sleep(10)
        cls.initialized = True

    @classmethod
    def update_api_data(cls) -> bool:
        response = requests.get(
            'https://github.com/ionic-bond/TwitterInternalAPIDocument/raw/master/docs/json/API.json', timeout=300)
        if response.status_code != 200:
            cls.logger.error('Request returned an error: {} {}.'.format(response.status_code, response.text))
            return False
        json_data = response.json()

        if not json_data.get('graphql', {}):
            cls.logger.error('Can not get Graphql API data from json')
            return False
        if not json_data.get('header', {}):
            cls.logger.error('Can not get header data from json')
            return False

        cls.graphql_api_data = json_data['graphql']
        cls.headers = json_data['header']
        cls.init_client_transaction()
        cls.logger.info('Pull GraphQL API data success, API number: {}'.format(len(cls.graphql_api_data)))
        return True

    @classmethod
    def init_client_transaction(cls) -> None:
        session = requests.Session()
        session.headers = generate_headers()

        cookies_dir = os.path.join(os.path.dirname(__file__), 'cookies')
        cookie_files = glob.glob(os.path.join(cookies_dir, '*.json'))
        
        home_page_response = None
        ondemand_file_url = None

        for cookie_file in cookie_files:
            try:
                with open(cookie_file, 'r') as f:
                    cookie_data = json.load(f)
                    auth_token = cookie_data.get("auth_token", "")
                    ct0 = cookie_data.get("ct0", "")
                    
                    if not auth_token:
                        continue
                        
                    # Inject token for this attempt
                    session.cookies.set("auth_token", auth_token, domain=".x.com")
                    session.cookies.set("ct0", ct0, domain=".x.com")
                    
                    # Request the page with the current token
                    home_page = session.get(url="https://x.com/home")
                    home_page_response = bs4.BeautifulSoup(home_page.content, 'html.parser')
                    
                    # Attempt to extract the URL. If it fails, it throws an exception.
                    ondemand_file_url = get_ondemand_file_url(response=home_page_response)
                    
                    # If extraction succeeds, stop searching.
                    if ondemand_file_url:
                        # Optional: cls.logger.info(f"Initialized successfully with {os.path.basename(cookie_file)}")
                        break 
                        
            except Exception as e:
                # cls.logger.warning(f"Token in {os.path.basename(cookie_file)} failed: {e}")
                session.cookies.clear() # Clear bad cookies before trying the next file
                continue

        if not ondemand_file_url:
            raise RuntimeError("All available cookie files failed or no valid tokens were found.")

        ondemand_file = session.get(url=ondemand_file_url)
        ondemand_file_response = bs4.BeautifulSoup(ondemand_file.content, 'html.parser')
        
        try:
            cls.ct = ClientTransaction(home_page_response=home_page_response,
                                       ondemand_file_response=ondemand_file_response)
        except Exception:
            ondemand_file_response = ondemand_file.text
            cls.ct = ClientTransaction(home_page_response=home_page_response,
                                       ondemand_file_response=ondemand_file_response)
    @classmethod
    def get_clint_transaction_id(cls, method: str, url: str) -> str:
        return cls.ct.generate_transaction_id(method=method,
                                              path=url.replace('https://x.com', '').replace('https://twitter.com', ''))

    @classmethod
    @check_initialized
    def get_api_data(cls, api_name: str) -> tuple[str, str, dict[str, str], dict]:
        if api_name not in cls.graphql_api_data:
            raise ValueError('Unkonw API name: {}'.format(api_name))

        api_data = cls.graphql_api_data[api_name]
        headers = cls.headers.copy()
        transaction_id = cls.get_clint_transaction_id(api_data['method'], api_data['url'])
        headers['x-client-transaction-id'] = transaction_id

        return api_data['url'], api_data['method'], headers, api_data['features']


GraphqlAPI.init()
