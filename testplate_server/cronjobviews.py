from django.db.models import Count
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import CronJob


class CronJobSerializer(serializers.ModelSerializer):
    # 查询需要转换枚举值
    type = serializers.CharField(source='get_type_display')
    env = serializers.CharField(source='get_env_name')
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = CronJob
        fields = "__all__"


class CronJobInfoSerializer(serializers.ModelSerializer):
    # 查询需要转换枚举值
    type = serializers.CharField(source='get_type_display')
    environment_id = serializers.IntegerField(source='env_id')
    env = serializers.CharField(source='get_env_name')
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

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
            CronJob.objects.filter(pk=id).update(**serializer.validated_data)
            res = {'status': True,
                   'code': '200',
                   'msg': "修改成功"}
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
            CronJob.objects.filter(pk=id).update(**serializer.validated_data)
            res = {'status': True,
                   'code': '200',
                   'msg': "修改成功"}
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
        res = {'status': True,
               'code': '200',
               'msg': "删除成功"}
        return Response(res)
