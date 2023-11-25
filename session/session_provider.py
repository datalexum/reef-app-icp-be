import logging
from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
from requests import RequestException


class SessionProviderException(Exception):
    pass


class LoginException(Exception):
    pass


class AbstractSessionProvider(ABC):
    provider_name = "GenericProvider"

    @abstractmethod
    def get_session(self, username: str, password: str) -> requests.Session:
        """
        Retrieve a session.
        """
        pass

    @abstractmethod
    def destroy_session(self, session: requests.Session):
        """
        Destroy a session.
        """
        pass


class FaunaMarinSessionProvider(AbstractSessionProvider):
    provider_name = "FaunaMarin"
    LOGIN_PAGE_URL = 'https://lab.faunamarin.de/de/login'
    LOGOUT_PAGE_URL = 'https://lab.faunamarin.de/de/logout'
    MAIN_PAGE = 'https://lab.faunamarin.de/'

    def get_session(self, username: str, password: str):
        session = requests.Session()
        try:
            login_page_response = session.get(self.LOGIN_PAGE_URL)
            login_page_response.raise_for_status()
        except RequestException as e:
            logging.error(f"Network error occurred: {e}")
            raise SessionProviderException("Failed to retrieve the login page")
        soup = BeautifulSoup(login_page_response.content, 'lxml')

        token_input = soup.find('input', {'name': '_token'})
        token = token_input['value'] if token_input else None

        if not token:
            raise SessionProviderException("Failed to retrieve the login token")

        login_data = {
            '_token': token,
            'email': username,
            'password': password
        }

        try:
            response = session.post(self.LOGIN_PAGE_URL, data=login_data)
            response.raise_for_status()
        except RequestException as e:
            logging.error(f"Login failed: {e}")
            raise LoginException("Failed to login. Please check the credentials and try again.")

        return session

    def destroy_session(self, session: requests.Session):
        main_page_response = session.get(self.MAIN_PAGE)
        soup = BeautifulSoup(main_page_response.content, 'lxml')

        token_input = soup.find('input', {'name': '_token'})
        logout_token = token_input['value'] if token_input else None

        if not logout_token:
            raise SessionProviderException("Failed to find the logout token")

        session.post(self.LOGOUT_PAGE_URL, data={'_token': logout_token}, verify=False)
