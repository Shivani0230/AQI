
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core.settings import settings
from app.api.routes import router

app = FastAPI(title=settings.APP_NAME, openapi_url=f"{settings.API_V1_PREFIX}/openapi.json")

app.include_router(router, prefix=settings.API_V1_PREFIX, tags=["AQI"])

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_name": settings.APP_NAME})
