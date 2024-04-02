import requests
from django.db.models import Count
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from datetime import datetime

from testplate_server.models import CronJob

""" 启动定时任务 """
from apscheduler.triggers.cron import CronTrigger

# # Create your views here.
from apscheduler.schedulers.background import BackgroundScheduler  # 使用它可以使你的定时任务在后台运行
from django_apscheduler.jobstores import DjangoJobStore

job_defaults = {'max_instances': 5}  # 增加调度器
scheduler = BackgroundScheduler(jobstores={'default': DjangoJobStore()})  # 创建定时任务的调度器对象——实例化调度器
scheduler.configure(job_defaults=job_defaults)

scheduler.start()  # 控制定时任务是否开启


def update_next_time(schedule):
    # 计算下一次执行时间
    # 创建cron迭代器时需要提供一个包含秒的完整时间点作为起始时间
    cron_data = schedule.split(' ')
    # 周为?时，使用*代替?每一周都执行
    cron = {"second": cron_data[0], "minute": cron_data[1], "hour": cron_data[2], "day": cron_data[3],
            "month": cron_data[4],
            "day_of_week": "*", "year": cron_data[6]}

    trigger = CronTrigger(**cron)

    # 获取下一次执行时间
    next_run_time = trigger.get_next_fire_time(None, datetime.now())
    # 解析字符串为aware datetime对象
    aware_datetime = datetime.fromisoformat(str(next_run_time))

    # 转换为UTC并移除时区信息
    next_run_time = aware_datetime.replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')
    return next_run_time


def run_test(task_id, case_ids, schedule):
    # 保存上次执行时间
    last_run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    CronJob.objects.filter(pk=task_id).update(last_run_time=last_run_time)
    protocol = CronJob.objects.filter(pk=task_id).values_list('env__protocol', flat=True).first()
    if protocol == 1:
        protocol = 'http'
    else:
        protocol = 'https'
    host = CronJob.objects.filter(pk=task_id).values_list('env__host', flat=True).first()
    port = CronJob.objects.filter(pk=task_id).values_list('env__port', flat=True).first()
    # 更新下次执行时间
    next_run_time = update_next_time(schedule)
    CronJob.objects.filter(pk=task_id).update(next_run_time=next_run_time)
    # 执行用例
    url = 'http://127.0.0.1:8000/apicase/run/'
    host = protocol + '://' + host + ':' + str(port)
    headers = {'Authorization': 'super_admin_request'}
    data = {'ids': case_ids, 'created_user': '超级管理员', 'host': host}
    try:
        requests.post(url=url, headers=headers, data=data)
    except:
        print('任务异常')


# 从数据库读取任务并添加到scheduler
for scheduled_task in CronJob.objects.filter(is_active=True).all():
    print('加载任务', scheduled_task.name)
    cron_data = scheduled_task.schedule.split(' ')
    cron = {"second": cron_data[0], "minute": cron_data[1], "hour": cron_data[2], "day": cron_data[3],
            "month": cron_data[4],
            "day_of_week": "*", "year": cron_data[6]}
    trigger = CronTrigger(**cron)

    scheduler.add_job(
        func=run_test,
        args=(scheduled_task.id, scheduled_task.case_ids, scheduled_task.schedule),
        trigger=trigger,
        id=str(scheduled_task.id),
        name=scheduled_task.name,
        replace_existing=True,  # 如果任务已经存在，则替换旧任务
    )


def add_job(id):
    try:
        queryset = CronJob.objects.filter(id=id).first()
        serializer = CronJobInfoSerializer(instance=queryset)
        active_cron_data = serializer.data.get('schedule').split(' ')
        active_cron = {"second": active_cron_data[0], "minute": active_cron_data[1],
                       "hour": active_cron_data[2], "day": active_cron_data[3],
                       "month": active_cron_data[4], "day_of_week": "*", "year": active_cron_data[6]}
        active_trigger = CronTrigger(**active_cron)

        scheduler.add_job(
            func=run_test,
            args=(serializer.data['id'], serializer.data['case_ids'], serializer.data['schedule']),
            trigger=active_trigger,
            id=str(serializer.data['id']),
            name=serializer.data['name'],
            replace_existing=True,  # 如果任务已经存在，则替换旧任务
        )
    except Exception as e:
        print(str(e))


def del_job(id):
    try:
        scheduler.remove_job(str(id))
    except:
        pass


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
        # fields = "__all__"
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
        sq = request.GET
        excluded_keys = ['size', 'page']
        filtered_params = {k: v for k, v in sq.items() if k not in excluded_keys}
        # 获取列表的查询字段后，根据需要进行模糊查询
        if 'name' in filtered_params:
            filtered_params['name__contains'] = filtered_params['name']
            filtered_params.pop('name')
        cronjob = CronJob.objects.filter(**filtered_params)
        size = int(request.GET.get('size'))
        page = int(request.GET.get('page'))
        # 使用annotate()和values()方法进行分页查询
        queryset = cronjob.annotate(count=Count('id')).order_by('-id')
        # slice方法进行分页
        start = (page - 1) * size
        end = start + size
        queryset = queryset[start:end]
        serializer = CronJobSerializer(instance=queryset, many=True)
        result = {
            'status': True,
            'code': 200,
            'data': serializer.data,
            'total': cronjob.count(),
            'page': page,
            'size': size
        }
        return Response(result)


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

        serializer = CronJobAddSerializer(data=request.data)
        if serializer.is_valid():
            # 获取下一次执行时间
            serializer.validated_data['next_run_time'] = update_next_time(request.data.get('schedule'))
            obj = serializer.save()
            res = {'status': True,
                   'code': '200',
                   'msg': "添加成功"}
            if request.data['is_active'] is False:
                pass
            else:
                add_job(obj.id)
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
            if serializer.data['is_active'] is False:
                del_job(id)
            else:
                del_job(id)
                add_job(id)
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
            if serializer.validated_data['is_active'] is False:
                serializer.validated_data['next_run_time'] = None
                CronJob.objects.filter(pk=id).update(**serializer.validated_data)
                res = {'status': True,
                       'code': '200',
                       'msg': "禁用成功"}
                del_job(id)
                return Response(res)
            else:
                schedule = CronJob.objects.filter(id=id).first().schedule
                serializer.validated_data['next_run_time'] = update_next_time(schedule)
                CronJob.objects.filter(pk=id).update(**serializer.validated_data)
                add_job(id)
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
        del_job(id)
        res = {'status': True,
               'code': '200',
               'msg': "删除成功"}
        return Response(res)
