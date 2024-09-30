from datetime import datetime


def get_current_year_and_month() -> tuple[int, int]:
    current_date = datetime.now()
    return current_date.year, current_date.month
