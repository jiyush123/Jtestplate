from datetime import datetime

from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import Token, User

from testplate_server.utils.encrypt import md5
from testplate_server.utils.token import generate_and_return_token


class LoginSerializers(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class LoginView(APIView):
    def post(self, request):
        data = request.data
        serializer = LoginSerializers(data=data, many=False)
        if serializer.is_valid():
            # 跟user表的账号密码对比
            username = serializer.validated_data['username']
            password = md5(serializer.validated_data['password'])
            user = User.objects.filter(username=username).first()
            if password == user.password:
                # 密码正确
                """这里生成token"""

                # 删除原有的Token
                old_token = Token.objects.filter(user_id=user.id)
                if old_token:
                    old_token.delete()
                # 创建新的Token
                token = generate_and_return_token()[0]
                Token.objects.create(token=token, user_id=user.id)
                login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                User.objects.filter(id=user.id).update(login_time=login_time)
                res = {"status": True, "code": 200, "data": {"user_id": user.id, "name": user.name, "token": token},
                       "msg": "登录成功"}
                return Response(res)
            res = {"status": False, "code": 500, "msg": "账号或密码不正确"}
            return Response(res)
        return Response(serializer.errors)


class AuthView(APIView):
    def post(self, request):
        data = request.data
        token = Token.objects.filter(token=data['token'])
        if token:
            res = {"status": True, "code": 200, "msg": "验证成功"}
            return Response(res)
        res = {"status": False, "code": 401, "msg": "验证失败"}
        return Response(res)


class LogoutView(APIView):
    def post(self, request):
        """退出登录"""
        id = request.data['id']
        user = User.objects.filter(id=id).first()
        # 删除原有的Token
        old_token = Token.objects.filter(user_id=user.id)
        if old_token:
            old_token.delete()
            res = {"status": True, "code": 200, "msg": "退出成功"}
            return Response(res)
        res = {"status": True, "code": 200, "msg": "退出成功"}
        return Response(res)
