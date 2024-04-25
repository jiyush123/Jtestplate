from django.core.exceptions import ValidationError
from django.db.models import Count
from django.shortcuts import render
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import Environment
from testplate_server.utils.paginator_fun import paginator_fun


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
        try:
            sq = request.GET
            excluded_keys = ['size', 'page']
            filtered_params = {k: v for k, v in sq.items() if k not in excluded_keys}
            # 获取列表的查询字段后，根据需要进行模糊查询
            if 'name' in filtered_params:
                filtered_params['name__contains'] = filtered_params['name']
                filtered_params.pop('name')
            size = int(request.GET.get('size', 10))  # 设置默认值以避免ValueError
            page = int(request.GET.get('page', 1))
            # 使用django的分页方法
            queryset = paginator_fun(table_obj=Environment,
                                     filtered=filtered_params,
                                     order_by='-id', page=page, size=size)
            serializer = EnvironmentSerializer(instance=queryset[0], many=True)
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
