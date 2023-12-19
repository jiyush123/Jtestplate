from datetime import datetime

from django.db.models import Count
from django.shortcuts import render
from rest_framework import serializers
from rest_framework.response import Response
import requests
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import APIInfo, ProModule


class ApiListSerializer(serializers.ModelSerializer):
    # 这样就可以获取枚举值的值
    status = serializers.CharField(source='get_status_display')
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    module = serializers.CharField(source='get_module_name')

    class Meta:
        model = APIInfo
        fields = ['id', 'name', 'description', 'module', 'method', 'uri', 'status', 'created_user', 'updated_time']


class ApiInfoSerializer(serializers.ModelSerializer):
    # 这样就可以获取枚举值的值，API列表跟详情用同一个序列化器，前端根据需要取字段显示
    status = serializers.CharField(source='get_status_display')
    module = serializers.CharField(source='get_module_name')
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = APIInfo
        fields = "__all__"


class ApiAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIInfo
        exclude = ["updated_time"]


class ApiUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIInfo
        exclude = ["created_user", "created_time", "updated_time"]


class APIList(APIView):
    """获取api列表接口"""

    def get(self, request):
        sq = request.GET
        excluded_keys = ['size', 'page']
        filtered_params = {k: v for k, v in sq.items() if k not in excluded_keys}
        # 获取列表的查询字段后，根据需要进行模糊查询
        if 'name' in filtered_params:
            filtered_params['name__contains'] = filtered_params['name']
            filtered_params.pop('name')
        if 'module' in filtered_params:
            module_ids = ProModule.objects.filter(name__contains=filtered_params['module']).values_list('id', flat=True)
            filtered_params['module_id__in'] = module_ids
            filtered_params.pop('module')

        api_info = APIInfo.objects.filter(**filtered_params)
        size = int(request.GET.get('size'))
        page = int(request.GET.get('page'))
        queryset = api_info.annotate(count=Count('id')).order_by('-id')

        # slice方法进行分页
        start = (page - 1) * size
        end = start + size
        queryset = queryset[start:end]
        # serializer = ApiListSerializer(instance=queryset, many=True)
        serializer = ApiInfoSerializer(instance=queryset, many=True)

        result = {
            'status': True,
            'code': 200,
            'data': serializer.data,
            'total': api_info.count(),
            'page': page,
            'size': size
        }
        return Response(result)


class APIDetail(APIView):
    """获取API详情"""

    def get(self, request):
        id = request.GET.get('id')
        exists = APIInfo.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        queryset = APIInfo.objects.filter(id=id).first()
        # 获取所有字段
        serializer = ApiInfoSerializer(instance=queryset)
        result = {
            'status': True,
            'code': 200,
            'data': serializer.data
        }
        return Response(result)


class APIAdd(APIView):
    """新增接口"""

    def post(self, request):
        print(request.data)
        serializer = ApiAddSerializer(data=request.data)
        if serializer.is_valid():
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


class APIDel(APIView):
    """删除接口"""

    def post(self, request):
        id = request.data['id']
        exists = APIInfo.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        APIInfo.objects.filter(id=id).delete()
        res = {'status': True,
               'code': '200',
               'msg': "删除成功"}
        return Response(res)


class APIUpdate(APIView):
    """修改接口"""

    def post(self, request):
        id = request.data['id']
        exists = APIInfo.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        data = request.data
        serializer = ApiUpdateSerializer(data=data)
        if serializer.is_valid():
            serializer.validated_data['updated_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            APIInfo.objects.filter(pk=id).update(**serializer.validated_data)
            res = {'status': True,
                   'code': '200',
                   'msg': "修改成功"}
            return Response(res)
        else:
            res = {'status': False,
                   'code': '500',
                   'msg': serializer.errors}
            return Response(res)


class APIDebug(APIView):
    """调试API接口"""

    def post(self, request):
        url = request.data['host'] + request.data['uri']
        method = request.data['method']
        data = {}

        headers = {}
        for k, v in request.data['headers'].items():
            headers[k] = v['value']
        if method == 'POST':
            for k, v in request.data['body'].items():
                data[k] = v['value']
            response = requests.post(url=url, json=data, headers=headers)
        else:
            for k, v in request.data['params'].items():
                data[k] = v['value']
            response = requests.get(url=url, params=data, headers=headers)
        result = {
            'status': True,
            'status_code': response.status_code,
            'response': response.content.decode(),
            'msg': "调试成功"
        }
        return Response(result)
