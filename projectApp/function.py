from datetime import datetime

def AlertClassifier(temperature, humidity, light, sound, roomStatus):
    # roomStatus 0 Available 1 Occupied
    res = {} # res['type'] 0 不异常 1 异常
    message = ''
    # 阈值
    NightLight = 60
    EmptyRoomSound = 30
    RoomSound = 100
    Fire = 35
    # get当前时间
    current_datetime = datetime.now()
    year = current_datetime.year
    month = current_datetime.month
    day = current_datetime.day
    hour = current_datetime.hour
    minute = current_datetime.minute
    second = current_datetime.second
    # 是不是晚上
    atNight = False
    if hour <= 6 or hour >= 19:
        atNight = True
    # 0 忘关灯
    if atNight and light >= NightLight:
        message += 'Forgot to Turn Off the Light'
    # 1 空房间吵 或 2 不管是不是空但特别吵
    if (roomStatus == 0 and sound >= EmptyRoomSound) or sound >= RoomSound:
        if len(message) != 0:
            message += '\n'
        message += 'Too Noisy'
    # 3 火了
    if temperature >= Fire:
        if len(message) != 0:
            message += '\n'
        message += 'On Fire'
    # 4 水了
    if humidity > 100:
        if len(message) != 0:
            message += '\n'
        message += 'Too Wet'

    if len(message) == 0: # 没异常
        res['type'] = 0
    else:
        res['type'] = 1
    res['message'] = message
    return res