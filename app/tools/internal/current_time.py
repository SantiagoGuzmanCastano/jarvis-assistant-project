
from sqlalchemy.orm import Session

from datetime import datetime


def get_current_time(arguments: dict, user_id:int, session: Session) ->dict:

    current_time = datetime.now()

    return {
        "current_time": current_time.isoformat()
    }