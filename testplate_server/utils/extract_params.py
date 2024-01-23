import re


# 定义一个函数来查找匹配项并从字典中获取替换值
def replace_placeholder(match, ext_params):
    placeholder = match.group(1)
    ext_val = ext_params.get(placeholder, placeholder)
    return str(ext_val)  # 如果字典中没有对应的键，则返回原样，全部转换成字符串


# 使用正则表达式和上面定义的函数替换字符串
def extract_func(param, ext_params):
    # 判断传入的参数是否为字符串，只有字符串才使用正则替换
    if isinstance(param, str):
        if len(param) >= 4:
            # 如果字符串只有一个${}没有其它字符,提取中间字符串匹配对应值，直接替换
            # 第一个第二个为'${'时，往后找第一个}，如果}后面没有字符串，则匹配
            if param[0] == '$' and param[1] == '{' and param[-1] == '}' and '}' not in param[2:-1]:
                output_params = ext_params[param[2:-1]]  # 直接拿提取的字符串匹配键值对，拿到值直接返回
                return output_params
            else:
                # 替换字符串
                output_params = re.sub(r'\$\{(\w+)\}', lambda m: replace_placeholder(m, ext_params), param)
                return output_params
    else:
        return param


if __name__ == '__main__':
    result = {'toekn': 'abcdefg'}
    ext_params = {'token': 'result.token', 'name': '123', 'page': 456}
    header = {'X-token': "bearer ${token}aaa${name}fdsfsd",
              'page': '${page}'}
    print(extract_func(header['X-token'], ext_params), header)
