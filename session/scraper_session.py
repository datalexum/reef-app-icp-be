import hashlib
import logging
from threading import Timer

from fastapi import HTTPException

from session.session_provider import AbstractSessionProvider


class ScraperSession:
    def __init__(self):
        self.sessions = {}
        self.timers = {}

    @staticmethod
    def get_session_id(username, password, session_provider: AbstractSessionProvider):
        return hashlib.sha256(str(username + password + session_provider.provider_name).encode("UTF-8")).digest()

    def get_session(self, username, password, session_provider):
        session_id = self.get_session_id(username, password, session_provider)
        if session_id in self.sessions:
            self.reset_timer(username, password, session_provider)
            return self.sessions[session_id]
        else:
            return self.start_new_session(username, password, session_provider)

    def start_new_session(self, username: str, password: str, session_provider: AbstractSessionProvider):
        try:
            session = session_provider.get_session(username, password)
        except Exception:
            raise HTTPException(status_code=400, detail="Login failed")

        session_id = self.get_session_id(username, password, session_provider)
        self.sessions[session_id] = session
        self.reset_timer(username, password, session_provider)
        return session

    def reset_timer(self, username, password, session_provider: AbstractSessionProvider):
        print("Timer resetted")
        print(self.sessions)
        session_id = self.get_session_id(username, password, session_provider)
        if session_id in self.timers:
            self.timers[session_id].cancel()

        timer = Timer(600, lambda: self.end_session(username, password, session_provider))
        timer.start()
        self.timers[session_id] = timer

    def end_session(self, username, password, session_provider: AbstractSessionProvider):
        session_id = self.get_session_id(username, password, session_provider)
        print("Ending session", session_id)

        if session_id in self.sessions:
            try:
                session_provider.destroy_session(self.sessions[session_id])
            except:
                logging.error("Logout failed, session destroyed.")

            self.sessions[session_id].close()
            del self.sessions[session_id]
            del self.timers[session_id]
        print("Session ended")
