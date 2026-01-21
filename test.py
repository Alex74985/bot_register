import datetime


date1_start = datetime.datetime.now().replace(hour=12, minute=30)
date1_end = datetime.datetime.now().replace(hour=14, minute=30)
date2_start = datetime.datetime.now().replace(hour=11, minute=0)
date2_end = datetime.datetime.now().replace(hour=12, minute=50)

start = max(date1_start, date2_start)
end = min(date1_end, date2_end)


if start < end:
    print(f"{start.time()} - {end.time()}")
else:
    print("None")
