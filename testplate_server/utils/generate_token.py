"""生成token"""
import uuid
import datetime


# 生成随机字符串
def generate_token():
    return str(uuid.uuid4())


# 设置Token有效期
def get_expiration_time():
    return datetime.datetime.now() + datetime.timedelta(hours=8)


# 返回Token给用户
def generate_and_return_token():
    token = generate_token()
    expiration_time = get_expiration_time()
    # save_token(token, expiration_time)
    return token, expiration_time


if __name__ == '__main__':
    print(generate_and_return_token()[0], generate_and_return_token()[1])

