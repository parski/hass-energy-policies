nordpool = hass.states.get("sensor.nordpool").as_dict()
today = nordpool['attributes']['today']
tomorrow = nordpool['attributes']['tomorrow']

def dates(count):
    times = []
    hour = 0
    date = datetime.datetime.now()
    for i in range(count):
        if hour == 24:
            date = date + datetime.timedelta(days = 1)
            hour = 0
        time = datetime.datetime(date.year, date.month, date.day, hour)
        times.append(time.isoformat())
        hour = hour + 1
    return times

def cheapest(hours, span):
    hoursAndPrice = list(zip(span, dates(len(span))))
    hoursAndPrice.sort()
    cheapestHours = []
    for hourAndPrice in hoursAndPrice:
        cheapestHours.append(hourAndPrice[1])
    return cheapestHours[0:hours]

def cheapestHoursForDevice(device):
    hours = device['hours']
    if device['required_daily'] == True:
        return cheapest(hours, today)
    else:
        # Remove passed hours
        return cheapest(hours, today + tomorrow)

def setStateForDevice(device):
    name = device['name']
    hours = cheapestHoursForDevice(device)
    entity_id = "policy." + name
    hass.states.set(entity_id, hours)

devices = data.get("devices")

for device in devices:
    setStateForDevice(device)
