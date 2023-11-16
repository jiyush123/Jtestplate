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
    class Meta:
        model = User
        fields = ["id", "name", "username", "login_time"]


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
