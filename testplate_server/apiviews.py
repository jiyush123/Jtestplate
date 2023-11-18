from datetime import datetime

from django.db.models import Count
from django.shortcuts import render
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import APIInfo,ProModule


class ApiListSerializer(serializers.ModelSerializer):
    # 这样就可以获取枚举值的值
    status = serializers.CharField(source='get_status_display')
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    module = serializers.CharField(source='get_module_name')

    class Meta:
        model = APIInfo
        fields = ['id', 'name', 'description', 'module', 'method', 'uri', 'status', 'created_user', 'updated_time']


class ApiInfoSerializer(serializers.ModelSerializer):
    # 这样就可以获取枚举值的值
    status = serializers.CharField(source='get_status_display')
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = APIInfo
        fields = "__all__"


class ApiAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIInfo
        exclude = ["updated_time"]


# class ApiUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = APIInfo
#         fields = ['id', 'api_name', 'api_description', 'api_request_method',
#                   'api_uri', 'status', 'api_params', 'api_data', 'api_response',
#                   'updated_user', 'updated_time', 'api_headers']


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

        api_info = APIInfo.objects.filter(**filtered_params)
        size = int(request.GET.get('size'))
        page = int(request.GET.get('page'))
        queryset = api_info.annotate(count=Count('id')).order_by('-id')

        # slice方法进行分页
        start = (page - 1) * size
        end = start + size
        queryset = queryset[start:end]
        serializer = ApiListSerializer(instance=queryset, many=True)

        result = {
            'status': True,
            'code': 200,
            'data': serializer.data,
            'total': api_info.count(),
            'page': page,
            'size': size
        }
        return Response(result)


# class ApiInfoView(APIView):
#     """获取API详情"""
#
#     def get(self, request):
#         id = request.GET.get('id')
#         exists = APIInfo.objects.filter(id=id).exists()
#         if not exists:
#             res = {'status': False,
#                    'code': '500',
#                    'msg': "数据不存在"}
#             return Response(res)
#         queryset = APIInfo.objects.filter(id=id).first()
#         # 获取所有字段
#         serializer = ApiInfoSerializer(instance=queryset)
#         result = {
#             'status': True,
#             'code': 200,
#             'data': serializer.data
#         }
#         return Response(result)


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
