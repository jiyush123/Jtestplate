from datetime import datetime

from django.db.models import Count
from django.shortcuts import render
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import User
from testplate_server.utils.encrypt import md5


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
        users = User.objects.filter(**filtered_params)
        size = int(request.GET.get('size'))
        page = int(request.GET.get('page'))
        # 使用annotate()和values()方法进行分页查询
        queryset = users.annotate(count=Count('id')).order_by('-id')
        # slice方法进行分页
        start = (page - 1) * size
        end = start + size
        queryset = queryset[start:end]
        serializer = UserListSerializer(instance=queryset, many=True)
        result = {
            'status': True,
            'code': 200,
            'data': serializer.data,
            'total': users.count(),
            'page': page,
            'size': size
        }
        return Response(result)


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
