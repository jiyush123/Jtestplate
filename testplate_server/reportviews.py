from datetime import datetime

from django.core.exceptions import ValidationError
from django.db.models import Count
from django.shortcuts import render
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import Report, ReportCaseInfo
from testplate_server.utils.paginator_fun import paginator_fun


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
            queryset = paginator_fun(table_obj=Report,
                                     filtered=filtered_params,
                                     order_by='-id', page=page, size=size)
            serializer = ReportListSerializer(instance=queryset[0], many=True)
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


class ReportCaseInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCaseInfo
        fields = "__all__"


class ReportCaseDetail(APIView):
    """获取报告用例详情"""

    def get(self, request):
        case_id = request.GET.get('case_id')
        report_id = request.GET.get('report_id')
        exists = ReportCaseInfo.objects.filter(case_id=case_id, report_id=report_id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        queryset = ReportCaseInfo.objects.filter(case_id=case_id, report_id=report_id)
        # 获取所有字段
        serializer = ReportCaseInfoSerializer(instance=queryset,many=True)
        result = {
            'status': True,
            'code': 200,
            'data': serializer.data
        }
        return Response(result)
