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
        response_time = round(response.elapsed.total_seconds() * 1000, 2)  # 毫秒
        response = json.loads(response.content.decode())

        result = {
            'status': True,
            'status_code': status_code,
            'response': response,
            'run_time': response_time,
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
    """不推荐一边迭代一边更新字典，需要先获取需要更新的键，然后再统一更新"""
    int_list = [k for k, v in req_data.items() if v['datatype'] == 'int']  # 生成需要转换int类型的键列表
    bool_list = [k for k, v in req_data.items() if v['datatype'] == 'bool']  # 生成需要转换bool类型的键列表
    str_list = [k for k, v in req_data.items() if v['datatype'] == 'string']  # 不需要转换的键列表
    for key in int_list:
        try:
            body_in[key] = int(req_data[key]['value'])
        except:
            result = {
                'status': False,
                'status_code': 500,
                'msg': "数据类型错误"
            }
            return result
    for key in bool_list:
        if req_data[key]['value'].lower() == 'false':
            body_in[key] = False
        else:
            body_in[key] = True
    for key in str_list:
        body_in[key] = req_data[key]['value']
    return body_in
