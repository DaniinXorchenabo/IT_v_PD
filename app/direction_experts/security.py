from datetime import timedelta

from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pony.orm import db_session

from app.utils.pydantic_security import *
from app.settings.config import cfg
from app.dependencies import *
from app.db.raw_models import DirectionExpert
from app.utils.utils_of_security import generate_security, basic_login


SECRET_KEY = cfg.get('keys', "direction_expert")
ACCESS_TOKEN_TIME = int(cfg.get('keys', "direction_expert_time"))
token_path = "direction_expert_token"
direction_expert_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=token_path)
[get_direction_expert,
 authenticate_direction_expert,
 get_current_direction_expert,
 create_direction_expert_access_token
 ] = generate_security(DirectionExpert)

direction_expert = APIRouter(
    tags=["direction_expert"],
    responses={404: {"description": "Not found"}},
    # dependencies=[Depends(open_db_session)]
)


@direction_expert.post("/" + token_path, response_model=Token)
@db_session
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.scopes:
        form_data.scopes = set(form_data.scopes.append("direction_expert"))
    else:
        form_data.scopes = ["direction_expert"]
    return basic_login(form_data,
                       authenticate=authenticate_direction_expert,
                       access_token_time=ACCESS_TOKEN_TIME,
                       create_access_token=create_direction_expert_access_token)


@direction_expert.get("/direction_expert", response_class=HTMLResponse)
async def login_direction_expert(request: Request):
    return login_templates.TemplateResponse(
        "login.html", {"request": request, "who": "Админа", "auth_url": "/" + token_path})