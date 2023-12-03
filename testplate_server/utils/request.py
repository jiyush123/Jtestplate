import requests


def req_func(req_data):
    url = req_data.get('url')
    method = req_data.get('method')
    headers = {}
    params = {}
    body = {}

    for k, v in req_data['body'].items():
        body[k] = v['value']
    for k, v in req_data['params'].items():
        params[k] = v['value']
    for k, v in req_data['headers'].items():
        headers[k] = v['value']

    if method == 'POST':
        response = requests.post(url=url, json=body, headers=headers)
    elif method == 'GET':
        response = requests.get(url=url, params=params, headers=headers)
    else:
        result = {
            'status': False,
            'status_code': 500,
            'msg': "暂不支持请求方式"
        }
        return result
    result = {
        'status': True,
        'status_code': response.status_code,
        'response': response.content.decode(),
        'msg': "执行成功"
    }
    return result

