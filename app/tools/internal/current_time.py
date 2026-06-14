

from datetime import datetime


def get_current_time(arguments: dict) ->dict:

    current_time = datetime.now()

    return {
        "current_time": current_time.isoformat()
    }