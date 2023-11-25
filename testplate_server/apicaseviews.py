from datetime import datetime

from django.db.models import Count
from django.shortcuts import render
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import APICase, APICaseStep


class APICaseAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = APICase
        exclude = ["status", "updated_time", "last_time"]


class APICaseStepAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = APICaseStep
        fields = "__all__"


class APICaseListSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='get_status_display')
    level = serializers.CharField(source='get_level_display')
    result = serializers.CharField(source='get_result_display')
    last_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = APICase
        fields = ["id", "name", "level", "status", "result", "last_time"]


class APICaseAdd(APIView):
    """新增接口测试用例"""

    def post(self, request):
        case = request.data
        steps = request.data.get('steps')
        del case['steps']

        case_serializer = APICaseAddSerializer(data=case)

        if case_serializer.is_valid():
            case_serializer.validated_data['updated_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            case_serializer.save()
        else:
            res = {'status': False,
                   'code': '500',
                   'msg': case_serializer.errors}
            return Response(res)
        len_steps = len(steps)
        for i in range(len_steps):
            step = steps[i]
            step['api_case'] = case_serializer.instance.id  # 把用例ID添加到步骤数据中
            step_serializer = APICaseStepAddSerializer(data=step)

            if step_serializer.is_valid():
                step_serializer.save()

            else:
                res = {'status': False,
                       'code': '500',
                       'msg': step_serializer.errors}
                return Response(res)
        res = {'status': True,
               'code': '200',
               'msg': "添加成功"}
        return Response(res)


class APICaseList(APIView):
    """获取api测试用例列表接口"""

    def get(self, request):
        sq = request.GET
        excluded_keys = ['size', 'page']
        filtered_params = {k: v for k, v in sq.items() if k not in excluded_keys}
        # 获取列表的查询字段后，根据需要进行模糊查询
        if 'name' in filtered_params:
            filtered_params['name__contains'] = filtered_params['name']
            filtered_params.pop('name')

        api_info = APICase.objects.filter(**filtered_params)
        size = int(request.GET.get('size'))
        page = int(request.GET.get('page'))
        queryset = api_info.annotate(count=Count('id')).order_by('-id')

        # slice方法进行分页
        start = (page - 1) * size
        end = start + size
        queryset = queryset[start:end]
        serializer = APICaseListSerializer(instance=queryset, many=True)

        result = {
            'status': True,
            'code': 200,
            'data': serializer.data,
            'total': api_info.count(),
            'page': page,
            'size': size
        }
        return Response(result)
