


from pydantic import BaseModel, Field


class UserSettingsCreate(BaseModel):
    assistant_name: str | None = None
    assistant_personality: str | None = None
    language_mode: str = 'auto'


class UserSettingsUpdate(BaseModel):
    assistant_name: str | None = None
    assistant_personality: str | None = None
    language_mode: str | None = None

class UserSettingsResponse(BaseModel):
    user_id: int
    assistant_name: str
    assistant_personality: str
    language_mode: str