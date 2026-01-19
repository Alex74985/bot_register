import time
from datetime import datetime, timedelta


datas = [datetime.now() + timedelta(days=i) for i in range(30)]

datas_f = [el.strftime("%d-%m") for el in datas]

start_time = datetime.now() + timedelta(hours=2)
end_time = datetime.now().replace(hour=20, minute=0, second=0, microsecond=0)

start_time = start_time.replace(day=20, hour=10, minute=30, second=0, microsecond=0)
end_time = end_time.replace(day=20)

if start_time.minute < 30:
    # Округляем до :30
    rounded_time = start_time.replace(minute=30, second=0, microsecond=0)
else:
    # Округляем до следующего часа
    rounded_time = start_time.replace(hour=start_time.hour + 1, minute=0, second=0, microsecond=0)


timeslots_count = (end_time - rounded_time) // timedelta(minutes=30)
timeslots = [rounded_time]
for i in range(timeslots_count):
    timeslots.append(rounded_time + timedelta(minutes=30))
    rounded_time += timedelta(minutes=30)

timeslots_f = [el.strftime("%H:%M") for el in timeslots]


print(*timeslots_f, sep="\n")