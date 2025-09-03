import calendar


def get_text_calendar():
    # Get a calendar for August 2025 as a string
    cal = calendar.TextCalendar(firstweekday=6)  # 6 = Sunday, matches `cal`
    cal_str = cal.formatmonth(2025, 8)
    return cal_str
