from collections.abc import MutableMapping
import requests
from settings import settings


def get_pay_link(tg_id: int) -> str:
    """Получение ссылки на оплату"""
    link_form = settings.pay_link

    data = {
        "order_id": tg_id,
        "subscription": settings.sub_number,
        "customer_extra": "Информация об оплачиваемой подписке",
        "do": "link",
        "sys": "",
        # "products[0][name]": "Подписка на 1 мес.",
        # "products[0][price]": 50,
        # "products[0][quantity]": 1,
    }

    response = requests.get(link_form, params=data)
    payment_link = response.content.decode()
    return payment_link


def cancel_sub_by_user(phone: str, profile_id: int | None) -> requests.Response:
    """Отмена подписки клиентом, ее невозможно будет уже включить только оформить повторно"""
    url = settings.pay_link + "rest/setActivity/"

    data = {
        "subscription": settings.sub_number,
        "customer_phone": phone,
        "active_user": 0
    }

    if profile_id:
        data["profile"] = profile_id

    signature = sign(data, settings.pay_token)
    data["signature"] = signature

    response = requests.post(url, data=data)
    return response


def sign(data, secret_key):
    import hashlib
    import hmac
    import json

    deep_int_to_string(data)

    data_json = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':')).replace("/", "\\/")

    return hmac.new(secret_key.encode('utf8'), data_json.encode('utf8'), hashlib.sha256).hexdigest()


def deep_int_to_string(dictionary):
    for key, value in dictionary.items():
        if isinstance(value, MutableMapping):
            deep_int_to_string(value)
        elif isinstance(value, list) or isinstance(value, tuple):
            for k, v in enumerate(value):
                deep_int_to_string({str(k): v})
        else:
            dictionary[key] = str(value)


def http_build_query(dictionary, parent_key=False):
    items = []
    for key, value in dictionary.items():
        new_key = str(parent_key) + '[' + key + ']' if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(http_build_query(value, new_key).items())
        elif isinstance(value, list) or isinstance(value, tuple):
            for k, v in enumerate(value):
                items.extend(http_build_query({str(k): v}, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)