from django.core.exceptions import ValidationError
from django.db.models import Count
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import CronJob
from testplate_server.utils.paginator_fun import paginator_fun
from testplate_server.scheduler import (
    update_next_time,
    add_job_to_scheduler,
    remove_job_from_scheduler
)


class CronJobSerializer(serializers.ModelSerializer):
    # 查询需要转换枚举值
    type = serializers.CharField(source='get_type_display')
    env = serializers.CharField(source='get_env_name')
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    last_run_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    next_run_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = CronJob
        fields = "__all__"


class CronJobInfoSerializer(serializers.ModelSerializer):
    # 查询需要转换枚举值
    type = serializers.CharField(source='get_type_display')
    environment_id = serializers.IntegerField(source='env_id')
    env = serializers.CharField(source='get_env_name')
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    last_run_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    next_run_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = CronJob
        fields = "__all__"


class CronJobAddSerializer(serializers.ModelSerializer):
    # 新增修改不需要转换枚举值
    class Meta:
        model = CronJob
        fields = ["name", "type", "case_ids", "schedule", "is_active", "env", "created_user"]


class CronJobUpdateSerializer(serializers.ModelSerializer):
    # 新增修改不需要转换枚举值
    class Meta:
        model = CronJob
        # fields = "__all__"
        fields = ["name", "type", "case_ids", "schedule", "is_active", "env"]


class CronJobChangeIsActive(serializers.ModelSerializer):
    # 列表点击修改启用状态

    class Meta:
        model = CronJob
        fields = ["is_active"]


class CronJobList(APIView):
    """获取定时任务列表接口"""

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
            queryset = paginator_fun(table_obj=CronJob,
                                     filtered=filtered_params,
                                     order_by='-id', page=page, size=size)
            serializer = CronJobSerializer(instance=queryset[0], many=True)
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


class CronJobDetail(APIView):
    """获取任务详情接口"""

    def get(self, request):
        id = request.GET.get('id')
        exists = CronJob.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        queryset = CronJob.objects.filter(id=id).first()
        serializer = CronJobInfoSerializer(instance=queryset)
        result = {
            'status': True,
            'code': 200,
            'data': serializer.data
        }
        return Response(result)


class CronJobAdd(APIView):
    """新增任务接口"""

    def post(self, request):
        request.data['created_user'] = request.operator
        serializer = CronJobAddSerializer(data=request.data)
        if serializer.is_valid():
            # 获取下一次执行时间
            serializer.validated_data['next_run_time'] = update_next_time(request.data.get('schedule'))
            obj = serializer.save()
            res = {'status': True,
                   'code': '200',
                   'msg': "添加成功"}
            if request.data['is_active'] is True:
                add_job_to_scheduler(obj.id, obj.name, obj.case_ids, obj.schedule)
            return Response(res)
        else:
            res = {'status': False,
                   'code': '500',
                   'msg': serializer.errors}
            return Response(res)


class CronJobUpdate(APIView):
    """修改任务接口"""

    def post(self, request):
        id = request.data['id']
        exists = CronJob.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        data = request.data
        serializer = CronJobUpdateSerializer(data=data)
        if serializer.is_valid():
            # 计算下一次执行时间
            serializer.validated_data['next_run_time'] = update_next_time(request.data.get('schedule'))

            CronJob.objects.filter(pk=id).update(**serializer.validated_data)
            res = {'status': True,
                   'code': '200',
                   'msg': "修改成功"}
            
            task = CronJob.objects.get(id=id)
            if task.is_active:
                remove_job_from_scheduler(id)
                add_job_to_scheduler(id, task.name, task.case_ids, task.schedule)
            else:
                remove_job_from_scheduler(id)
                
            return Response(res)
        else:
            res = {'status': False,
                   'code': '500',
                   'msg': serializer.errors}
            return Response(res)


class CronJobIsActive(APIView):
    """修改任务启用状态接口"""

    def post(self, request):
        id = request.data['id']
        exists = CronJob.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        data = request.data
        serializer = CronJobChangeIsActive(data=data)
        if serializer.is_valid():
            task = CronJob.objects.get(id=id)
            if serializer.validated_data['is_active'] is False:
                serializer.validated_data['next_run_time'] = None
                CronJob.objects.filter(pk=id).update(**serializer.validated_data)
                remove_job_from_scheduler(id)
                res = {'status': True,
                       'code': '200',
                       'msg': "禁用成功"}
                return Response(res)
            else:
                serializer.validated_data['next_run_time'] = update_next_time(task.schedule)
                CronJob.objects.filter(pk=id).update(**serializer.validated_data)
                add_job_to_scheduler(id, task.name, task.case_ids, task.schedule)
                res = {'status': True,
                       'code': '200',
                       'msg': "启用成功"}
                return Response(res)
        else:
            res = {'status': False,
                   'code': '500',
                   'msg': serializer.errors}
            return Response(res)


class CronJobDel(APIView):
    """删除任务接口"""

    def post(self, request):
        id = request.data['id']
        exists = CronJob.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        CronJob.objects.filter(id=id).delete()
        remove_job_from_scheduler(id)
        res = {'status': True,
               'code': '200',
               'msg': "删除成功"}
        return Response(res)
