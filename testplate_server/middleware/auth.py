# from django.shortcuts import redirect
import datetime

from django.utils.deprecation import MiddlewareMixin
# from rest_framework.response import Response
from django.http import JsonResponse

from testplate_server.models import Token


class Auth(MiddlewareMixin):
    """前置方法"""

    def process_request(self, request):
        # 登录，退出不需要判断
        if request.path_info in ['/login/', '/logout/', '/auth/']:
            # 获取用户当前请求的URL
            return
        # 登录才能访问，没登录跳转回登录页
        # 前后端分离项目使用token校验
        try:
            token = request.headers['Authorization']
            # 如果token是super_admin_request，代表后端直接调用，不需要继续校验
            if token == 'super_admin_request':
                return
            else:
                token = Token.objects.filter(token=token).first()
                if not token:
                    # 这个是django返回的路径，如果是用前后端分离的方式，需要返回一个code让前端重定向
                    result = {
                        'status': False,
                        'code': 401,
                        'msg': "登录超时，请重新登录"
                    }
                    return JsonResponse(result,json_dumps_params={"ensure_ascii": False})
                elif token.timeout_time < datetime.datetime.now():
                    Token.objects.filter(token=token.token).delete()
                    result = {
                        'status': False,
                        'code': 401,
                        'msg': "登录超时，请重新登录"
                    }
                    return JsonResponse(result,json_dumps_params={"ensure_ascii": False})
        except:
            result = {
                'status': False,
                'code': 401,
                'msg': "登录超时，请重新登录"
            }
            return JsonResponse(result,json_dumps_params={"ensure_ascii": False})

    # def process_response(self, request, response):
    #     return response
