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
                if v['datatype'] == 'int':
                    try:
                        body[k] = int(v['value'])
                    except:
                        result = {
                            'status': False,
                            'status_code': 500,
                            'msg': "数据类型错误"
                        }
                        return result
                elif v['datatype'] == 'bool':
                    if v['value'].lower() == 'false':
                        body[k] = False
                    else:
                        body[k] = True
                else:
                    body[k] = v['value']
        if req_data['params'] is not None:
            for k, v in req_data['params'].items():
                if v['datatype'] == 'int':
                    try:
                        params[k] = int(v['value'])
                    except:
                        result = {
                            'status': False,
                            'status_code': 500,
                            'msg': "数据类型错误"
                        }
                        return result
                elif v['datatype'] == 'bool':
                    if v['value'].lower() == 'false':
                        params[k] = False
                    else:
                        params[k] = True
                else:
                    params[k] = v['value']
        if req_data['headers'] is not None:
            for k, v in req_data['headers'].items():
                if v['datatype'] == 'int':
                    try:
                        headers[k] = int(v['value'])
                    except:
                        result = {
                            'status': False,
                            'status_code': 500,
                            'msg': "数据类型错误"
                        }
                        return result
                elif v['datatype'] == 'bool':
                    if v['value'].lower() == 'false':
                        headers[k] = False
                    else:
                        headers[k] = True
                else:
                    headers[k] = v['value']
        try:
            if req_data['assert_result'] is not None:
                for k, v in req_data['assert_result'].items():
                    if v['datatype'] == 'int':
                        try:
                            assert_result[k] = int(v['value'])
                        except:
                            result = {
                                'status': False,
                                'status_code': 500,
                                'msg': "数据类型错误"
                            }
                            return result
                    elif v['datatype'] == 'bool':
                        if v['value'].lower() == 'false':
                            assert_result[k] = False
                        else:
                            assert_result[k] = True
                    else:
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
