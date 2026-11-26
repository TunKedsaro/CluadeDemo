from datetime import datetime

from ninja import Schema
from pydantic import EmailStr, Field, field_validator


class EventOut(Schema):
    id: int
    name: str
    starts_at: datetime
    location: str
    capacity: int
    seats_remaining: int


class RegistrationIn(Schema):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr = Field(max_length=254)
    phone: str = Field(min_length=6, max_length=20, pattern=r"^[0-9+\-\s()]+$")
    consent: bool
    website: str = Field(default="", max_length=200)  # honeypot, must stay empty

    @field_validator("name", "phone", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email", mode="after")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("consent")
    @classmethod
    def consent_must_be_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("ต้องยอมรับการเก็บและใช้ข้อมูลส่วนบุคคล (consent)")
        return value


class RegistrationOut(Schema):
    id: int
    event_id: int
    status: str
    created_at: datetime


class ErrorOut(Schema):
    detail: str
