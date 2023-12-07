from datetime import datetime

from django.db.models import Count
from django.shortcuts import render
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import Report


class ReportListSerializer(serializers.ModelSerializer):
    created_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    result = serializers.CharField(source='get_result_display')
    end_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Report
        fields = ["id", "name", "end_time", "result", "created_user", "created_time"]


class ReportInfoSerializer(serializers.ModelSerializer):
    # 这样就可以获取枚举值的值
    result = serializers.CharField(source='get_result_display')
    created_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    end_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Report
        fields = "__all__"


class ReportList(APIView):
    """获取报告列表接口"""

    def get(self, request):
        sq = request.GET
        excluded_keys = ['size', 'page']
        filtered_params = {k: v for k, v in sq.items() if k not in excluded_keys}
        # 获取列表的查询字段后，根据需要进行模糊查询
        if 'name' in filtered_params:
            filtered_params['name__contains'] = filtered_params['name']
            filtered_params.pop('name')
        report = Report.objects.filter(**filtered_params)
        size = int(request.GET.get('size'))
        page = int(request.GET.get('page'))
        # 使用annotate()和values()方法进行分页查询
        queryset = report.annotate(count=Count('id')).order_by('-created_time')
        # slice方法进行分页
        start = (page - 1) * size
        end = start + size
        queryset = queryset[start:end]
        serializer = ReportListSerializer(instance=queryset, many=True)
        result = {
            'status': True,
            'code': 200,
            'data': serializer.data,
            'total': report.count(),
            'page': page,
            'size': size
        }
        return Response(result)


class ReportDetail(APIView):
    """获取报告详情"""

    def get(self, request):
        id = request.GET.get('id')
        exists = Report.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        queryset = Report.objects.filter(id=id).first()
        # 获取所有字段
        serializer = ReportInfoSerializer(instance=queryset)
        result = {
            'status': True,
            'code': 200,
            'data': serializer.data
        }
        return Response(result)


class ReportDel(APIView):
    """删除接口"""

    def post(self, request):
        id = request.data['id']
        exists = Report.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        Report.objects.filter(id=id).delete()
        res = {'status': True,
               'code': '200',
               'msg': "删除成功"}
        return Response(res)