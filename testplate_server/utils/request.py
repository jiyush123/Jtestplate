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
        print(req_data)
        if req_data['body'] is not None:
            for k, v in req_data['body'].items():
                body[k] = v['value']
        if req_data['params'] is not None:
            for k, v in req_data['params'].items():
                params[k] = v['value']
        if req_data['headers'] is not None:
            for k, v in req_data['headers'].items():
                headers[k] = v['value']
        try:
            if req_data['assert_result'] is not None:
                for k, v in req_data['assert_result'].items():
                    assert_result[k] = v['value']
        except:
            assert_result = {}

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
        status_code = response.status_code
        response = json.loads(response.content.decode())
        result = {
            'status': True,
            'status_code': status_code,
            'response': response,
            'msg': "执行成功",
        }
        assert_info = []
        if assert_result == {}:
            assert_info.append({'assert_expect': '',
                                'assert_value': '',
                                'assert_result': 'success'})
        else:
            for k, v in assert_result.items():
                # 将前端传过来的.字符串切割成引用目标字符串，最后得到的值再对比目标值v
                key = k.split('.')
                assert_response = result
                for i in key:
                    if i in assert_response:
                        assert_response = assert_response[i]
                    else:
                        assert_response = None
                        break

                if assert_response == v:
                    assert_info.append({'assert_expect': v,
                                        'assert_value': assert_response,
                                        'assert_result': 'success'})
                else:
                    assert_info.append({'assert_expect': v,
                                        'assert_value': assert_response,
                                        'assert_result': 'error'})
        return result, assert_info
    except Exception as e:
        result = {
            'status': False,
            'status_code': 500,
            'response': e,
            'msg': "执行失败"
        }
        assert_info = []
        return result, assert_info
