import json

import requests


def generate_from_url(swagger_url):
    """通过url格式化"""
    try:
        response = requests.get(url=swagger_url)
        apis = json.loads(response.content.decode())
        api_info = generate_api(apis)
        return api_info
    except:
        api_info = []
        return api_info


def generate_from_jsonfile(json_file_path):
    """通过json文件格式化"""
    with open(json_file_path, 'r', encoding='utf-8') as file:
        apis = json.load(file)
    api_info = generate_api(apis)
    return api_info


def generate_api(api_info):
    host = api_info.get('host')
    paths = api_info.get('paths')
    security_definitions = api_info.get('securityDefinitions')
    definitions = api_info.get('definitions')
    apis_info = []
    for path, method in paths.items():
        api_headers = None
        api_params = []
        api_body = []
        api_description = None
        api_name = None
        api_method = None
        api_path = path
        api_response = None
        consumes_headers = []
        parametes_header = []
        for method, info in method.items():
            api_method = method
            api_name = info['summary']
            api_description = info['description']
            if 'consumes' in info:
                consumes_headers = info['consumes']

            if 'parameters' in info:
                api_parameters = info['parameters']
                for i in range(len(api_parameters)):
                    if api_parameters[i]['in'] == 'query':
                        api_params.append(api_parameters[i])
                    elif api_parameters[i]['in'] == 'body':
                        if '$ref' in api_parameters[i]['schema']:
                            body_info = api_parameters[i]['schema']['$ref'].split('/')[2]
                            api_body.append(definitions[body_info]['properties'])
                        else:
                            pass
                    elif api_parameters[i]['in'] == 'header':
                        parametes_header.append(api_parameters[i])
            api_response = info['responses']
            api_headers = generate_headers(security_definitions, consumes_headers, parametes_header)
            api_params = generate_params(api_params)
            api_body = generate_body(api_body)
        apis_info.append({'name': api_name, 'description': api_description, 'method': api_method, 'uri': api_path,
                          'headers': api_headers, 'params': api_params, 'body': api_body, 'response': api_response})
    return apis_info


def generate_headers(security_headers, consumes_headers, parameters_headers):
    headers = {}
    for key, value in security_headers.items():
        headers[key] = {'value': value['name']}
    for i in range(len(consumes_headers)):
        headers['Content-Type'] = {'value': consumes_headers[i]}
    for i in range(len(parameters_headers)):
        if 'description' in parameters_headers[i]['schema']:
            headers[parameters_headers[i]['name']] = {'value': '',
                                                      'description': parameters_headers[i]['schema']['description']}
        else:
            headers[parameters_headers[i]['name']] = {'value': '',
                                                      'description': ''}
    return headers


def generate_params(swagger_params):
    params = {}
    if len(swagger_params) == 0:
        params = None
    else:
        for i in range(len(swagger_params)):
            if 'description' in swagger_params[i] and 'type' in swagger_params[i]:
                params[swagger_params[i]['name']] = {'value': swagger_params[i]['type'],
                                                     'description': swagger_params[i]['description']}
            elif 'type' in swagger_params[i]:
                params[swagger_params[i]['name']] = {'value': swagger_params[i]['type']}
            elif 'description' in swagger_params[i]:
                params[swagger_params[i]['name']] = {'value': '', 'description': swagger_params[i]['description']}
            else:
                params[swagger_params[i]['name']] = {'value': '', 'description': ''}
    return params


def generate_body(swagger_body):
    body = {}
    if len(swagger_body) == 0:
        body = None
    else:
        for i in range(len(swagger_body)):
            for key, value in swagger_body[i].items():

                if 'description' in value and 'type' in value:
                    body[key] = {'value': value['type'],
                                 'description': value['description']}
                elif 'type' in value:
                    body[key] = {'value': value['type']}
                elif 'description' in value:
                    body[key] = {'value': '',
                                 'description': value['description']}
                else:
                    body[key] = {'value': '',
                                 'description': ''}
    return body


if __name__ == '__main__':
    # url = 'http://10.81.29.157:8801/v2/api-docs'
    # api_list = generate_from_url(url)
    # print(api_list)
    file_path = 'D://liantong//工业iot//iot-manager.json'
    api_list2 = generate_from_jsonfile(file_path)
    print(api_list2)
