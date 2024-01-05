import json

import requests


def req_func(req_data):
    try:
        url = req_data.get('url')
        method = req_data.get('method')
        headers = {}
        params = {}
        body = {}
        assert_result = {}
        if req_data['body'] is not None:
            for k, v in req_data['body'].items():
                body[k] = v['value']
        if req_data['params'] is not None:
            for k, v in req_data['params'].items():
                params[k] = v['value']
        if req_data['headers'] is not None:
            for k, v in req_data['headers'].items():
                headers[k] = v['value']
        if req_data['assert_result'] is not None:
            for k, v in req_data['assert_result'].items():
                assert_result[k] = v['value']

        if method == 'POST':
            response = requests.post(url=url, json=body, headers=headers)
        elif method == 'GET':
            response = requests.get(url=url, params=params, headers=headers)
        else:
            result = {
                'status': str(False),
                'status_code': '500',
                'msg': "暂不支持请求方式"
            }
            return result
        status_code = response.status_code
        response = json.loads(response.content.decode())
        result = {
            'status': str(True),
            'status_code': str(status_code),
            'response': response,
            'msg': "执行成功",
            'result': []
        }
        if assert_result == {}:
            result['result'].append('success')
        else:
            for k, v in assert_result.items():

                if result.get(k) == v:
                    result['result'].append('success')
                else:
                    result['result'].append('error')
        return result
    except Exception as e:
        result = {
            'status': str(False),
            'status_code': '500',
            'response': e,
            'msg': "执行失败"
        }
        return result

