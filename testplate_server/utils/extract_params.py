import re


# 定义一个函数来查找匹配项并从字典中获取替换值
def replace_placeholder(match, ext_params):
    placeholder = match.group(1)
    ext_val = ext_params.get(placeholder, placeholder)
    return str(ext_val)  # 如果字典中没有对应的键，则返回原样，全部转换成字符串


# 使用正则表达式和上面定义的函数替换字符串
def extract_func(param, ext_params):
    # 判断传入的参数是否为字符串，只有字符串才能使用正则替换
    if isinstance(param, str):
        output_string = re.sub(r'\$\{(\w+)\}', lambda m: replace_placeholder(m, ext_params), param)
        return output_string
    else:
        return param


if __name__ == '__main__':
    result = {'toekn': 'abcdefg'}
    ext_params = {'token': 'result.token', 'name': '123', 'page': 456}
    header = {'X-token': "bearer ${token}aaa${name}fdsfsd",
              'page': '${page}'}
    print(extract_func(header['X-token'], ext_params), header)
