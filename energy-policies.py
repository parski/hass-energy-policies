"""

Energy Policies
-----------------------------------

Fetches data from a Nord Pool sensor `sensor.nordpool` and creates 
entities to control the state of devices depending on input parameters.

-----------------------------------

Script should probably run once at midnight (00:00).

-----------------------------------

Parameters:

name (String): Name of policy excluding domain. Probably just the name of the device.

required_daily (Bool): Will schedule device for a set number of hours for today.

hours (Int): Hours to run every day. Required if `required_daily` is set to `True`.

factor_of_average (Float): Run if price is a factor of today's average price. 
                           Between 0-1 where 0 is free and 1 is today's average 
                           electricity price.

-----------------------------------
Copyright © Pär Strindevall 2022

"""

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

def cheapestHoursOutOfSpan(hours, span):
    pricesAndHours = list(zip(span, dates(len(span))))
    pricesAndHours.sort()

    cheapestHours = []
    for priceAndHour in pricesAndHours:
        cheapestHours.append(priceAndHour[1])

    return cheapestHours[0:hours]

def hoursUnderAverageByFactor(threshold):
    average = nordpool['attributes']['average']

    factorOfAverageHours = []
    for price in todaysPrices:
        factor = price / average
        factorOfAverageHours.append(factor)
    
    factorsAndHours = list(zip(factorOfAverageHours, dates(24)))
    factorsAndHours.sort()

    hoursUnderAverageByFactor = []
    for factorAndHour in factorsAndHours:
        factor = factorAndHour[0]
        if factor <= threshold:
            hour = factorAndHour[1]
            hoursUnderAverageByFactor.append(hour)

    return hoursUnderAverageByFactor

def policyForDevice(device):
    if 'required_daily' in device:
        if device['required_daily'] == True:
            if 'hours' not in device:
                logger.error('Devices with required_daily needs set hours.')
                return
            hours = device['hours']
            return cheapestHoursOutOfSpan(hours, todaysPrices)

    if 'factor_of_average' in device:
        factor = device['factor_of_average']
        return hoursUnderAverageByFactor(factor)

    logger.error("Can't add policy for %s. Device needs more configuration.", device['name'])

def setPolicyStateForDevice(device):
    if 'name' not in device:
        logger.error('Device needs a name to set a policy.')
        return

    policy = policyForDevice(device)
    if policy == None:
        return

    entity_id = "policy." + device['name']
    hass.states.set(entity_id, policy)

nordpool = hass.states.get("sensor.nordpool").as_dict()

def nordPoolDataIsUsable():
    if 'attributes' not in nordpool:
        logger.error('Nord Pool missing attributes.')
        return False

    if 'today' not in nordpool['attributes']:
        logger.error('Nord Pool missing today.')
        return False

    if 'average' not in nordpool['attributes']:
        logger.error('Nord Pool missing average.')
        return False

    if nordpool['attributes']['average'] == 0:
        logger.error('Nord Pool average is zero or broken.')
        return False
    
    return True

todaysPrices = nordpool['attributes']['today']

devices = data.get("devices")

if nordPoolDataIsUsable() == True:
    for device in devices:
        setPolicyStateForDevice(device)
