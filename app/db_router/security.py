from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple, Union
from pydantic import ValidationError
from collections import defaultdict

from fastapi import Depends, status, APIRouter, Request
from jose import JWTError, jwt
from pony.orm import db_session
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from app.db import models as m

from app.settings.config import cfg
from app.utils.pydantic_security import TokenData, HumanInDB, Token, BaseModel
from app.utils.utils_of_security import oauth2_scheme, PassScopes, SECRET_KEY, ALGORITHM
from app.pydantic_models.gen import db_models_for_create as pd
from app.pydantic_models.gen import all_optional_models as op_pd
from app.utils.exceptions import ChildHTTPException as HTTPException
from app.pydantic_models.standart_methhods_redefinition import AccessType


@db_session
def getter_human(username: str):
    if m.Human.exists(username=username):
        human_db = m.Human.get(username=username)
        return HumanInDB.from_pony_orm(human_db)


@db_session
def get_current_human_for_db(
        request: Request,
        security_scopes: SecurityScopes = PassScopes(),
        token: str = Depends(oauth2_scheme)):
    """ Получение текущего пользователя"""
    print('---------------------------------sdsdcasdcascdascdasdc')
    if token is None:
        return op_pd.Human(scopes=[str(AccessType.PUBLIC)])
    try:
        print(security_scopes.scopes)
        if security_scopes.scopes and bool(security_scopes.scopes):
            authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
        else:
            authenticate_value = f"Bearer"
        credentials_exception = HTTPException(
            request=request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": authenticate_value},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_scopes = payload.get("scopes", [])
            token_data = TokenData(scopes=token_scopes, username=username)
        except (JWTError, ValidationError):
            raise credentials_exception
        if (human := m.Human.get(username=token_data.username)) is None:
            raise credentials_exception
        print('roles from db', human.scopes)
        print('roles from token', token_data.scopes)
        human: pd.Human = getattr(pd, human.__class__.__name__).from_pony_orm(human)
        human.scopes = list(set(token_data.scopes) & set(human.scopes))
        setattr(request, "current_human", human)
        return human
    except HTTPException as e:
        print("---=== произошла ошибка при получении текущего пользователя в бд роуте", [e], __file__)
        raise e
    except Exception as e:
        print("Произошла ошибка в текущем пользователе!!! (бд роут)", [e], __file__)
        raise HTTPException(
            request=request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )