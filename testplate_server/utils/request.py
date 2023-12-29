import requests


def req_func(req_data):
    try:
        url = req_data.get('url')
        method = req_data.get('method')
        headers = {}
        params = {}
        body = {}
        if req_data['body'] is not None:
            for k, v in req_data['body'].items():
                body[k] = v['value']
        if req_data['params'] is not None:
            for k, v in req_data['params'].items():
                params[k] = v['value']
        if req_data['headers'] is not None:
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
    except Exception as e:
        result = {
            'status': False,
            'status_code': 500,
            'response': e,
            'msg': "执行失败"
        }
        return result

