PROXY = {
    "enabled": True,
    "host": "your.proxy.server",
    "port": 1234,
    "username": "user",
    "password": "pass"
}

def with_proxy(options):
    from selenium.webdriver.common.proxy import Proxy, ProxyType
    if PROXY["enabled"]:
        proxy = f'{PROXY["host"]}:{PROXY["port"]}'
        options.add_argument(f'--proxy-server=http://{proxy}')
