from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from models import User
from sqlalchemy.orm import Session
from db_connect import get_db
from models import User, Per_mission
from schemas import User_base, Token
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from config import settings
from enum import Enum, unique
from sqlalchemy import and_

routes = APIRouter(prefix='/auth', tags=['oauth2-security'])
oath2_security = OAuth2PasswordBearer(tokenUrl='/security/token')
cryp_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@unique
class PER(Enum):
    READ = "read_per"
    WRITE = "write_per"
    DELETE = "delete_per"


SECRECT_KEY = settings.JWT_PRIVATE_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_DAYS = settings.ACCESS_TOKEN_EXPIRE_DAYS


async def decoder_user_token(token: str, db: Session):
    '''
    decode thông tin từ token. trả về thông tin user từ database
    '''
    data = jwt.decode(token, SECRECT_KEY, ALGORITHM)
    if not data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='user token in validate')

    user_id = data['id']
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='user not validate')

    return user


async def login_user(access_token: str = Depends(oath2_security), db: Session = Depends(get_db)):
    '''
    lấy thông tin về user đã đăng nhập.
    '''
    user = await decoder_user_token(access_token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Invalid authen')
    return user


async def create_access_token(data: dict, expires_delta: timedelta | None = None):
    '''
    Tạo acccess_token dựa vào dữ liệu của người dùng.
    data : dữ liệu của người dùng bao gồm user_id, có thể thêm các thuộc tính khác nếu cần thiết.
    expires_delta : setting thời hạn mà một access_token có hiệu lực.
    '''
    data_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    data_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(data_encode, SECRECT_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authen_user(db: Session, username: str, password: str):
    '''
    Kiểm tra thông tin đăng nhập của người dùng đúng hay sai. 
    Bao gồm thông tin về tên đăng nhập và mật khẩu.
    '''
    get_user = db.query(User).filter(User.user_name == username).first()

    if not get_user:
        return False
    elif cryp_context.verify(cryp_context.hash(password), get_user.password):
        return False
    print('authen user sucsses')

    return get_user


class RoleChecker:
    def __init__(self, allowed_roles: list) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(login_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f'User: {user.user_name} do not have role to access this api')


allow_admin_roles = RoleChecker(['admin'])
allow_datamanager_roles = RoleChecker(['data', 'admin'])
allow_reviewer_roles = RoleChecker(['review', 'data', 'admin'])


class PerMission:
    def __init__(self, allow_permission: Enum, table) -> None:
        self.allow_permission = allow_permission
        self.table = table

    def __call__(self, user: User = Depends(login_user), db: Session = Depends(get_db)):
        uid = user.user_id
        get_per = db.query(Per_mission).filter(
            and_(Per_mission.user_id == uid, Per_mission.tb_name == self.table)).first()
        if not get_per or not getattr(get_per, self.allow_permission.value):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"User {user.user_name} do not permission to this api")


@routes.post('/token', response_model=Token)
async def get_token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    '''
    Thực hiện đăng nhập và trả về chuỗi access_token cho người dùng. 
    '''
    get_user = await authen_user(db, username=form.username, password=form.password)

    if not get_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f'username or password incorrect')

    time_exp = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    token = await create_access_token({'id': get_user.user_id}, time_exp)

    return {"access_token": token, "token_type": "bearer"}


@routes.get('/me', response_model=User_base)
async def get_me(curent_user: User = Depends(login_user)):
    return curent_user


@routes.get('/admin/getuser', response_model=list[User_base], dependencies=[Depends(allow_admin_roles)])
async def get_user_by_admin(db: Session = Depends(get_db)):
    """get all user by admin roles permission
    Args:
        db (Session, optional): Defaults to Depends(get_db).
        - Lấy ra database manager
    Returns:
        User_base : Trả về danh sách người dùng theo User_base shemmas
    """
    all_user = db.query(User).all()
    return all_user
