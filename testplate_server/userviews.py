from datetime import datetime

from django.core.exceptions import ValidationError
from django.db.models import Count
from django.shortcuts import render
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import User
from testplate_server.utils.encrypt import md5
from testplate_server.utils.paginator_fun import paginator_fun


class UserListSerializer(serializers.ModelSerializer):
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = User
        fields = ["id", "name", "username", "updated_time"]


class UserAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name", "username", "password"]


class UserList(APIView):
    """获取用户列表接口"""

    def get(self, request):
        try:
            sq = request.GET
            excluded_keys = ['size', 'page']
            filtered_params = {k: v for k, v in sq.items() if k not in excluded_keys}
            # 获取列表的查询字段后，根据需要进行模糊查询
            if 'name' in filtered_params:
                filtered_params['name__contains'] = filtered_params['name']
                filtered_params.pop('name')
            if 'username' in filtered_params:
                filtered_params['username__contains'] = filtered_params['username']
                filtered_params.pop('username')
            size = int(request.GET.get('size', 10))  # 设置默认值以避免ValueError
            page = int(request.GET.get('page', 1))
            # 使用django的分页方法
            queryset = paginator_fun(table_obj=User,
                                     filtered=filtered_params,
                                     order_by='-id', page=page, size=size)
            serializer = UserListSerializer(instance=queryset[0], many=True)
            result = {
                'status': True,
                'code': 200,
                'data': serializer.data,
                'total': queryset[1],
                'page': page,
                'size': size
            }
            return Response(result)
        except (ValueError, ValidationError) as e:
            # 处理整数转换失败或验证错误的情况
            return Response({'status': False, 'code': 400, 'message': str(e)}, status=400)
        except Exception as e:
            # 捕获其他潜在异常
            return Response({'status': False, 'code': 500, 'message': 'Internal Server Error'}, status=500)


class UserDetail(APIView):
    """获取用户详情接口"""

    def get(self, request):
        id = request.GET.get('id')
        exists = User.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        queryset = User.objects.filter(id=id).first()
        # 获取字与新增一致用同一个序列化器
        serializer = UserAddSerializer(instance=queryset)
        result = {
            'status': True,
            'code': 200,
            'data': serializer.data
        }
        return Response(result)

class UserAdd(APIView):
    """新增用户接口"""

    def post(self, request):

        serializer = UserAddSerializer(data=request.data)
        if serializer.is_valid():
            # 密码用md5加密
            password = serializer.validated_data['password']
            serializer.validated_data['password'] = md5(password)
            serializer.validated_data['updated_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            serializer.save()
            res = {'status': True,
                   'code': '200',
                   'msg': "添加成功"}
            return Response(res)
        else:
            res = {'status': False,
                   'code': '500',
                   'msg': serializer.errors}
            return Response(res)


class UserUpdate(APIView):
    """修改用户接口"""

    def post(self, request):
        id = request.data['id']
        exists = User.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        data = request.data
        serializer = UserAddSerializer(data=data)
        if serializer.is_valid():
            password = serializer.validated_data['password']
            serializer.validated_data['password'] = md5(password)
            serializer.validated_data['updated_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            User.objects.filter(pk=id).update(**serializer.validated_data)
            res = {'status': True,
                   'code': '200',
                   'msg': "修改成功"}
            return Response(res)
        else:
            res = {'status': False,
                   'code': '500',
                   'msg': serializer.errors}
            return Response(res)


class UserDel(APIView):
    """删除用户接口"""

    def post(self, request):
        id = request.data['id']
        exists = User.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        User.objects.filter(id=id).delete()
        res = {'status': True,
               'code': '200',
               'msg': "删除成功"}
        return Response(res)
