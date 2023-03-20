from pydantic import BaseModel

# ------------------USER SCHEMAS--------------#


class User_base(BaseModel):
    user_id: str
    user_name: str
    role: str

    class Config:
        orm_mode = True


class UserInDb(User_base):
    password: str


class Update_user(BaseModel):
    user_name: str | None = None
    role: str | None = None

    class Config:
        orm_mode = True


class New_user(BaseModel):
    user_id: str
    user_name: str
    password: str
    role: str

    class Config:
        orm_mode = True

# -------------CURVE SCHEMAS--------------#


class Curve_value_out(BaseModel):
    curve_id: str
    md: float
    cal_value: float | None
    well_id: str

    class Config:
        orm_mode = True

# --------------AUTH SCHEMAS-------------------#


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
