import os

from fastapi import FastAPI, Security, HTTPException
from typing import List

from fastapi.security import APIKeyHeader
from starlette import status

from models.APIModels import ICPProviders, ICPProvider, ReefTank, Credentials, ICPAnalysis
from session.scraper_session import ScraperSession

api_keys = [os.getenv("API_KEY")]
api_key_header = APIKeyHeader(name="X-API-Key")


def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header in api_keys:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )


app = FastAPI()
scraper_session = ScraperSession()


@app.get("/icp_providers", )
async def list_icp_providers(api_key: str = Security(get_api_key)):
    return ICPProviders(icp_providers=[e.value for e in ICPProvider])


# Endpoints
@app.get("/{icp_provider}/reef_tanks/", response_model=List[ReefTank])
async def list_reef_tanks(icp_provider: ICPProvider, username: str, password: str, api_key: str = Security(get_api_key)):
    scraper = icp_provider.get_scraper_instance()
    session = scraper_session.get_session(username, password, scraper.session_provider)
    return scraper.get_tanks(session)


@app.post("/{icp_provider}/reef_tanks/{tank_id}/analyses/", response_model=ICPAnalysis)
async def create_icp_analysis(icp_provider: ICPProvider, tank_id: str, analysis: ICPAnalysis, api_key: str = Security(get_api_key)):
    raise NotImplementedError


@app.get("/{icp_provider}/reef_tanks/{tank_id}/analyses/")
async def list_icp_analyses(icp_provider: ICPProvider, tank_id: str, username, password, api_key: str = Security(get_api_key)):
    scraper = icp_provider.get_scraper_instance()
    session = scraper_session.get_session(username, password, scraper.session_provider)
    return scraper.list_analysis(session, tank_id)


@app.get("/{icp_provider}/reef_tanks/{tank_id}/analyses/{analysis_id}")
async def get_icp_analysis(icp_provider: ICPProvider, tank_id: str, analysis_id: str, username, password, api_key: str = Security(get_api_key)):
    scraper = icp_provider.get_scraper_instance()
    session = scraper_session.get_session(username, password, scraper.session_provider)
    analysis = scraper.get_analysis(session, tank_id, analysis_id)
    return analysis


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
