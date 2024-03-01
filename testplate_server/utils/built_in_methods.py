"""项目的内置方法"""
"""使用前后置处理时使用vars_get()和vars_put()方法"""


class ExtractVariables:
    def __init__(self, extract_data=None):
        if extract_data is None:
            self.extract_data = {}
        else:
            self.extract_data = extract_data

    def get(self, key):
        return self.extract_data.get(key)

    def put(self, key, value):
        self.extract_data[key] = value


if __name__ == '__main__':
    vars = ExtractVariables()
    vars.put('name', 'xxx')
    vars.get('name')
