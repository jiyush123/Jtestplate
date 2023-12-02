from django.db.models import Count
from django.shortcuts import render
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import Environment


class EnvironmentSerializer(serializers.ModelSerializer):
    # 查询需要转换枚举值
    protocol = serializers.CharField(source='get_protocol_display')

    class Meta:
        model = Environment
        fields = "__all__"


class EnvironmentAddSerializer(serializers.ModelSerializer):
    # 新增修改不需要转换枚举值
    class Meta:
        model = Environment
        fields = "__all__"


class EnvironmentList(APIView):
    """获取环境列表接口"""

    def get(self, request):
        sq = request.GET
        excluded_keys = ['size', 'page']
        filtered_params = {k: v for k, v in sq.items() if k not in excluded_keys}
        # 获取列表的查询字段后，根据需要进行模糊查询
        if 'name' in filtered_params:
            filtered_params['name__contains'] = filtered_params['name']
            filtered_params.pop('name')
        enviroments = Environment.objects.filter(**filtered_params)
        size = int(request.GET.get('size'))
        page = int(request.GET.get('page'))
        # 使用annotate()和values()方法进行分页查询
        queryset = enviroments.annotate(count=Count('id')).order_by('-id')
        # slice方法进行分页
        start = (page - 1) * size
        end = start + size
        queryset = queryset[start:end]
        serializer = EnvironmentSerializer(instance=queryset, many=True)
        result = {
            'status': True,
            'code': 200,
            'data': serializer.data,
            'total': enviroments.count(),
            'page': page,
            'size': size
        }
        return Response(result)


class EnvironmentDetail(APIView):
    """获取环境详情接口"""

    def get(self, request):
        id = request.GET.get('id')
        exists = Environment.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        queryset = Environment.objects.filter(id=id).first()
        serializer = EnvironmentSerializer(instance=queryset)
        result = {
            'status': True,
            'code': 200,
            'data': serializer.data
        }
        return Response(result)


class EnvironmentAdd(APIView):
    """新增环境接口"""

    def post(self, request):

        serializer = EnvironmentAddSerializer(data=request.data)
        if serializer.is_valid():
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


class EnvironmentUpdate(APIView):
    """修改环境接口"""

    def post(self, request):
        id = request.data['id']
        exists = Environment.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        data = request.data
        serializer = EnvironmentAddSerializer(data=data)
        if serializer.is_valid():
            Environment.objects.filter(pk=id).update(**serializer.validated_data)
            res = {'status': True,
                   'code': '200',
                   'msg': "修改成功"}
            return Response(res)
        else:
            res = {'status': False,
                   'code': '500',
                   'msg': serializer.errors}
            return Response(res)


class EnvironmentDel(APIView):
    """删除用户接口"""

    def post(self, request):
        id = request.data['id']
        exists = Environment.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        Environment.objects.filter(id=id).delete()
        res = {'status': True,
               'code': '200',
               'msg': "删除成功"}
        return Response(res)
