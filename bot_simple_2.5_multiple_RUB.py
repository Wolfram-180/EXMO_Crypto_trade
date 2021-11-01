import urllib, http.client
import time
import json
# эти модули нужны для генерации подписи API
import hmac, hashlib
import random

print('')
print('')
print('>>>> Version : bot_2.5 build 1145-311021 - multiple pairs')
print('')
print('')

# ключи API, которые предоставила exmo
API_KEY = 'K-.........................................'
# обратите внимание, что добавлена 'b' перед строкой
API_SECRET = b'S-........................................'

# Тонкая настройка
CURRENCY_1 = 'WAVES'
CURRENCY_2 = 'RUB'
CURRENT_PAIR = '{}_{}'.format(CURRENCY_1, CURRENCY_2)
PAIRS_LIST = [
     'DASH_RUB', 'LTC_RUB', 'WAVES_RUB', 'ETH_RUB', 
]

#CURRENCY_1_MIN_QUANTITY = 0.001  # минимальная сумма ставки - берется из https://api.exmo.com/v1/pair_settings/

ORDER_LIFE_TIME = 1440  # 720 = 12 ч; через сколько минут отменять неисполненный ордер на покупку CURRENCY_1
AVG_PRICE_PERIOD = 4320 # 4320 - 3 суток; 1440 = сутки; 20160 - 14; 80640 - 56 суток; За какой период брать среднюю цену (мин)

AVG_PRICE_DISCOUNT = 0.5 # снижение в % от средней цены AVG_PRICE_PERIOD, чтобы купить пониже 

STOCK_FEE = 0.008  # ставлю 3% ---- Комиссия, которую берет биржа (0.002 CAN_SPEND= 0.2%)
PROFIT_MARKUP = 0.02  # Какой навар нужен с каждой сделки? (0.001 = 0.1%)  **********  IMP  *************

CAN_SPEND = 550  # Сколько тратить CURRENCY_2 каждый раз при покупке CURRENCY_1  **********  IMP  *************
CAN_SPEND_LIST = []

#CAN_SPEND_LIST.append(CAN_SPEND)

CAN_SPEND_LIST.append(8000)
CAN_SPEND_LIST.append(7000)
CAN_SPEND_LIST.append(6000)
CAN_SPEND_LIST.append(5000)
CAN_SPEND_LIST.append(4000)
CAN_SPEND_LIST.append(3000)
CAN_SPEND_LIST.append(2000)
CAN_SPEND_LIST.append(1000)
CAN_SPEND_LIST.append(500)

CAN_SPEND_MIN = 50

makesmalls = True

if makesmalls:
    for n in range(15, 1, -1):
        CAN_SPEND_ = CAN_SPEND + random.randint(1, 10)
        CAN_SPEND_LIST.append(CAN_SPEND_)

    for n in range(5, 1, -1):
        CAN_SPEND_LIST.append(90)    

    for n in range(5, 1, -1):
        CAN_SPEND_LIST.append(60)    

    for n in range(9, 1, -1):
        CAN_SPEND_LIST.append(30)  

    CAN_SPEND_MIN = 8
    for n in range(9, 1, -1):
        CAN_SPEND_LIST.append(CAN_SPEND_MIN) 

DEBUG = True  # True - выводить отладочную информацию, False - писать как можно меньше

STOCK_TIME_OFFSET = 0  # Если расходится время биржи с текущим

random.seed()

# базовые настройки
API_URL = 'api.exmo.com'
API_VERSION = 'v1'

# Свой класс исключений
class ScriptError(Exception):
    pass


class ScriptQuitCondition(Exception):
    pass


# все обращения к API проходят через эту функцию
def call_api(api_method, http_method="POST", **kwargs):
    # Составляем словарь {ключ:значение} для отправки на биржу
    # пока что в нём {'nonce':123172368123}
    payload = {'nonce': int(round(time.time() * 1000))}

    # Если в ф-цию переданы параметры в формате ключ:значение
    if kwargs:
        # добавляем каждый параметр в словарь payload
        # Получится {'nonce':123172368123, 'param1':'val1', 'param2':'val2'}
        payload.update(kwargs)

    # Переводим словарь payload в строку, в формат для отправки через GET/POST и т.п.
    payload = urllib.parse.urlencode(payload)

    # Из строки payload получаем "подпись", хешируем с помощью секретного ключа API
    # sing - получаемый ключ, который будет отправлен на биржу для проверки
    H = hmac.new(key=API_SECRET, digestmod=hashlib.sha512)
    H.update(payload.encode('utf-8'))
    sign = H.hexdigest()

    # Формируем заголовки request для отправки запроса на биржу.
    #     Передается публичный ключ  API и подпись, полученная с  помощью     hmac
    
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Key": API_KEY,
               "Sign": sign}

    # Создаем подключение к бирже, если в течении 60 сек не удалось подключиться, обрыв соединения
    conn = http.client.HTTPConnection(API_URL, timeout=60)
    # После установления связи, запрашиваем переданный адрес
    # В заголовке запроса уходят headers, в теле - payload
    conn.request(http_method, "/" + API_VERSION + "/" + api_method, payload, headers)
    # Получаем ответ с биржи и читаем его в переменную response
    response = conn.getresponse().read()
    # Закрываем подключение
    conn.close()

    try:
        # Полученный ответ переводим в строку UTF, и пытаемся преобразовать из текста в объект Python
        obj = json.loads(response.decode('utf-8'))

        # Смотрим, есть ли в полученном объекте ключ "error"
        if 'error' in obj and obj['error']:
            # Если есть, выдать ошибку, код дальше выполняться не будет
            raise ScriptError(obj['error'])
        # Вернуть полученный объект как результат работы ф-ции
        return obj
    except ValueError:
        # Если не удалось перевести полученный ответ (вернулся не JSON)
        raise ScriptError('Ошибка анализа возвращаемых данных, получена строка', response)


def get_pair_info(pair_curr_, param_):
    # r = requests.get('https://api.exmo.com/v1/pair_settings')
    r = call_api('pair_settings')[pair_curr_]
    return r[param_]


def get_pair_ticker(pair_curr_, param_):
    r = call_api('ticker')[pair_curr_]
    return r[param_]


# Реализация алгоритма
def main_flow():
    for CURRENT_PAIR in PAIRS_LIST:
        #CURRENCY_1 = CURRENT_PAIR[:3]
        #CURRENCY_2 = CURRENT_PAIR[-3:]
        CURRENCY_1 = CURRENT_PAIR.split('_')[0]
        CURRENCY_2 = CURRENT_PAIR.split('_')[1]
        CURRENCY_1_MIN_QUANTITY = float(get_pair_info(CURRENT_PAIR, 'min_quantity'))

        print(' >>>>>>>>   ', CURRENT_PAIR, '  :   CURRENCY_1_MIN_QUANTITY : ',  CURRENCY_1_MIN_QUANTITY, '   <<<<<')
        print(get_pair_ticker(CURRENT_PAIR, 'sell_price'))

        try:
            # Получаем список активных ордеров
            try:
                opened_orders = call_api('user_open_orders')[CURRENT_PAIR]
            except KeyError:
                if DEBUG:
                    print('Открытых ордеров нет')
                opened_orders = []

            sell_orders = []
            # Есть ли неисполненные ордера на продажу CURRENCY_1?
            for order in opened_orders:
                if order['type'] == 'sell':
                    # Есть неисполненные ордера на продажу CURRENCY_1, выход
                    raise ScriptQuitCondition(
                        'Выход, ждем пока не исполнятся/закроются все ордера на продажу (один ордер может быть разбит биржей на несколько и исполняться частями)')
                else:
                    # Запоминаем ордера на покупку CURRENCY_1
                    sell_orders.append(order)

            # Проверяем, есть ли открытые ордера на покупку CURRENCY_1
            if sell_orders:  # открытые ордера есть
                for order in sell_orders:
                    # Проверяем, есть ли частично исполненные
                    if DEBUG:
                        print('Проверяем, что происходит с отложенным ордером', order['order_id'])
                    try:
                        order_history = call_api('order_trades', order_id=order['order_id'])
                        # по ордеру уже есть частичное выполнение, выход
                        raise ScriptQuitCondition(
                            'Выход, продолжаем надеяться докупить валюту по тому курсу, по которому уже купили часть')
                    except ScriptError as e:
                        if 'Error 50304' in str(e):
                            if DEBUG:
                                print('Частично исполненных ордеров нет')

                            time_passed = time.time() + STOCK_TIME_OFFSET * 60 * 60 - int(order['created'])

                            if time_passed > ORDER_LIFE_TIME * 60:
                                # Ордер уже давно висит, никому не нужен, отменяем
                                call_api('order_cancel', order_id=order['order_id'])
                                raise ScriptQuitCondition(
                                    'Отменяем ордер - за ' + str(ORDER_LIFE_TIME) + ' минут не удалось купить ' + str(
                                        CURRENCY_1))
                            else:
                                raise ScriptQuitCondition(
                                    'Выход, продолжаем надеяться купить валюту по указанному ранее курсу, со времени создания ордера прошло {} минут из {} минут периода жизни ордера'.format(str(round(time_passed/60, 0)), str(ORDER_LIFE_TIME)))
                        else:
                            raise ScriptQuitCondition(str(e))

            else:  # Открытых ордеров нет
                balances = call_api('user_info')['balances']
                if float(balances[
                             CURRENCY_1]) >= CURRENCY_1_MIN_QUANTITY:  # Есть ли в наличии CURRENCY_1, которую можно продать?
                    """
                        Высчитываем курс для продажи.
                        Нам надо продать всю валюту, которую купили, на сумму, за которую купили + немного навара и минус комиссия биржи
                        При этом важный момент, что валюты у нас меньше, чем купили - бирже ушла комиссия
                        0.00134345 1.5045
                    """
                    try:
                        # wanna_get = CAN_SPEND_LEVEL + CAN_SPEND_LEVEL * (STOCK_FEE + PROFIT_MARKUP)  # сколько хотим получить за наше кол-во
                        # price_ = round((wanna_get / float(balances[CURRENCY_1])), 2)

                        # изменяю - цена берется как текущая + накидка процента
                        exmo_sell_price = float(get_pair_ticker(CURRENT_PAIR, 'sell_price'))
                        price_ = (exmo_sell_price +
                                  exmo_sell_price * (STOCK_FEE + PROFIT_MARKUP))

                        price_ = round(price_, 2)

                        print('sell ', CURRENT_PAIR, ' vol= ', balances[CURRENCY_1], price_)
                        new_order = call_api(
                            'order_create',
                            pair=CURRENT_PAIR,
                            quantity=balances[CURRENCY_1],
                            price=price_,
                            type='sell'
                        )
                    except:
                        print('EXCEPT: sell ', CURRENT_PAIR, ' vol= ', balances[CURRENCY_1], price_)
                        print('EXCEPT: ', new_order)
                        pass
                    print(new_order)
                    if DEBUG:
                        print('Создан ордер на продажу', CURRENCY_1, new_order['order_id'])
                else:
                    # CURRENCY_1 нет, надо докупить
                    # Достаточно ли денег на балансе в валюте CURRENCY_2 (Баланс >= CAN_SPEND)
                    if float(balances[CURRENCY_2]) >= CAN_SPEND_MIN:
                        # Узнать среднюю цену за AVG_PRICE_PERIOD, по которой продают CURRENCY_1
                        """
                         Exmo не предоставляет такого метода в API, но предоставляет другие, к которым можно попробовать привязаться.
                         У них есть метод required_total, который позволяет подсчитать курс, но,
                             во-первых, похоже он берет текущую рыночную цену (а мне нужна в динамике), а
                             во-вторых алгоритм расчета скрыт и может измениться в любой момент.
                         Сейчас я вижу два пути - либо смотреть текущие открытые ордера, либо последние совершенные сделки.
                         Оба варианта мне не слишком нравятся, но завершенные сделки покажут реальные цены по которым продавали/покупали,
                         а открытые ордера покажут цены, по которым только собираются продать/купить - т.е. завышенные и заниженные.
                         Так что берем информацию из завершенных сделок.
                        """
                        deals = call_api('trades', pair=CURRENT_PAIR)
                        prices = []
                        for deal in deals[CURRENT_PAIR]:
                            time_passed = time.time() + STOCK_TIME_OFFSET * 60 * 60 - int(deal['date'])
                            if time_passed < AVG_PRICE_PERIOD * 60:
                                prices.append(float(deal['price']))
                        try:
                            avg_price = sum(prices) / len(prices)

                            avg_price = avg_price / 100 * (100 - AVG_PRICE_DISCOUNT) # add 13.07.2020

                            """
                                Посчитать, сколько валюты CURRENCY_1 можно купить.
                                На сумму CAN_SPEND за минусом STOCK_FEE, и с учетом PROFIT_MARKUP
                                ( = ниже средней цены рынка, с учетом комиссии и желаемого профита)
                            """
                            # купить больше, потому что биржа потом заберет кусок
                            my_need_price = round((avg_price - avg_price * (STOCK_FEE + PROFIT_MARKUP)), 2)

                            for CAN_SPEND_LEVEL in CAN_SPEND_LIST:
                                my_amount = round((CAN_SPEND_LEVEL / my_need_price), 6)

                                print(CURRENT_PAIR, 'buy', my_amount, my_need_price)

                                # Допускается ли покупка такого кол-ва валюты (т.е. не нарушается минимальная сумма сделки)
                                if my_amount >= CURRENCY_1_MIN_QUANTITY:
                                    try:
                                        new_order = call_api(
                                            'order_create',
                                            pair=CURRENT_PAIR,
                                            quantity=my_amount,
                                            price=my_need_price,
                                            type='buy'
                                        )
                                        print(new_order)
                                        if DEBUG:
                                            print('Создан ордер на покупку', new_order['order_id'])
                                    except:
                                        print('CAN_SPEND_LEVEL: ', CAN_SPEND_LEVEL, '  ===>  not enough')
                                        pass
                                else:  # мы можем купить слишком мало на нашу сумму
                                    raise ScriptQuitCondition('Выход, не хватает денег на создание ордера')

                        except ZeroDivisionError:
                            print('Не удается вычислить среднюю цену', prices)
                    else:
                        raise ScriptQuitCondition('Выход, не хватает денег')

        except ScriptError as e:
            print(e)
        except ScriptQuitCondition as e:
            if DEBUG:
                print(e)
                print('')
                print('Ждем пару секунд чтоб не бомбить')
                print('...')
                time.sleep(random.randint(1, 2))
                print('Еще секунда и погнали')
                print('......')
                time.sleep(random.randint(1, 2))
            pass
        except Exception as e:
            print("!!!!", e)


while (True):
    main_flow()
    time.sleep(random.randrange(1, 3))
