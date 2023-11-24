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
        exclude = ["status", "updated_time"]


class APICaseStepAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = APICaseStep
        fields = "__all__"


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
