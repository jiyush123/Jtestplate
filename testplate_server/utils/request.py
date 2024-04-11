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
            body = change_type(body, req_data['body'])
        if req_data['params'] is not None:
            params = change_type(params, req_data['params'])
        if req_data['headers'] is not None:
            headers = change_type(headers, req_data['headers'])
        try:
            if req_data['assert_result'] is not None:
                assert_result = change_type(assert_result, req_data['assert_result'])
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
        if assert_result == {}:
            assert_info = {'': {'expect': '', 'value': '', 'result': 'success'}}
        else:
            assert_info = {}
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
                    assert_info[k] = {'expect': v, 'value': assert_response, 'result': 'success'}
                else:
                    assert_info[k] = {'expect': v, 'value': assert_response, 'result': 'error'}

        result['assert_info'] = assert_info
        return result
    except Exception as e:
        result = {
            'status': False,
            'status_code': 500,
            'response': e,
            'msg': "执行失败"
        }
        return result


def change_type(body_in, req_data):
    for k, v in req_data.items():
        if v['datatype'] == 'int':
            try:
                body_in[k] = int(v['value'])
            except:
                result = {
                    'status': False,
                    'status_code': 500,
                    'msg': "数据类型错误"
                }
                return result
        elif v['datatype'] == 'bool':
            if v['value'].lower() == 'false':
                body_in[k] = False
            else:
                body_in[k] = True
        else:
            body_in[k] = v['value']
    return body_in
