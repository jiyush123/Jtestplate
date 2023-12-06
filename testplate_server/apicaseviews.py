from datetime import datetime

from django.db.models import Count
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import APICase, APICaseStep, Report
from testplate_server.utils.request import req_func


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
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = APICase
        fields = ["id", "name", "level", "status", "result", "last_time", "updated_time"]


class APICaseInfoSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='get_status_display')
    level = serializers.CharField(source='get_level_display')
    result = serializers.CharField(source='get_result_display')
    created_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    last_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = APICase
        fields = "__all__"


class APICaseStepInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = APICaseStep
        fields = "__all__"


class ApiCaseUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = APICase
        exclude = ["result", "created_user", "created_time", "updated_time", "last_time"]


class APICaseAdd(APIView):
    """新增接口测试用例"""

    def post(self, request):
        steps = request.data.get('steps')

        case_serializer = APICaseAddSerializer(data=request.data)

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


class APICaseDel(APIView):
    """删除接口测试用例"""

    def post(self, request):
        id = request.data['id']
        exists = APICase.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        APICase.objects.filter(id=id).delete()
        res = {'status': True,
               'code': '200',
               'msg': "删除成功"}
        return Response(res)


class APICaseDetail(APIView):
    """获取API详情"""

    def get(self, request):
        id = request.GET.get('id')
        exists = APICase.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        case_queryset = APICase.objects.filter(id=id).first()
        case_serializer = APICaseInfoSerializer(instance=case_queryset)

        step_queryset = APICaseStep.objects.filter(api_case=case_serializer.data['id']).order_by('sort')
        step_serializer = APICaseStepInfoSerializer(instance=step_queryset, many=True)

        result = {
            'status': True,
            'code': 200,
            'data': {"case": case_serializer.data,
                     "steps": step_serializer.data}
        }
        return Response(result)


class APICaseUpdate(APIView):
    """修改接口测试用例"""

    def post(self, request):
        id = request.data['id']
        exists = APICase.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        data = request.data
        steps = request.data.get('steps')
        case_serializer = ApiCaseUpdateSerializer(data=data)
        if case_serializer.is_valid():
            case_serializer.validated_data['updated_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            APICase.objects.filter(pk=id).update(**case_serializer.validated_data)

        else:
            res = {'status': False,
                   'code': '500',
                   'msg': case_serializer.errors}
            return Response(res)
        len_steps = len(steps)
        # 循环编辑测试步骤
        for i in range(len_steps):
            step = steps[i]
            step['api_case'] = id
            step_serializer = APICaseStepInfoSerializer(data=step)
            if step_serializer.is_valid():
                # 获取存在的步骤
                step = APICaseStep.objects.filter(api_case=id, sort=str(i))
                step_exists = step.exists()
                # 存在就更新，不存在就新增
                if step_exists:
                    step.update(**step_serializer.validated_data)
                else:
                    step_serializer.save()

            else:
                res = {'status': False,
                       'code': '500',
                       'msg': step_serializer.errors}
                return Response(res)
        # 删除多余步骤
        APICaseStep.objects.filter(api_case=id, sort__gte=len_steps).delete()
        res = {'status': True,
               'code': '200',
               'msg': "修改成功"}
        return Response(res)


class APICaseTest(APIView):
    # 接收测试用例id
    def post(self, request):
        ids = request.data['ids']
        success_cases = 0
        error_cases = 0
        # 生成报告
        created_user = request.data['created_user']
        report_id = self.save_report(ids, created_user)
        for i in range(len(ids)):
            exists = APICase.objects.filter(id=ids[i]).exists()
            if not exists:
                res = {'status': False,
                       'code': '500',
                       'msg': "数据不存在"}
                return Response(res)
            # 找到对应的数据
            case_queryset = APICase.objects.filter(id=ids[i]).first()
            case_serializer = APICaseInfoSerializer(instance=case_queryset)
            APICase.objects.filter(pk=ids[i]).update(last_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            step_queryset = APICaseStep.objects.filter(api_case=case_serializer.data['id']).order_by('sort')
            self.step_serializer = APICaseStepInfoSerializer(instance=step_queryset, many=True)
            self.len_step = len(self.step_serializer.data)
            self.host = request.data['host']
            success_num = 0
            error_num = 0
            response = []
            # 执行用例
            for j in range(self.len_step):
                result = self.test(self.step_serializer.data[j])
                if result['status_code'] == 200:
                    success_num = success_num + 1
                else:
                    error_num = error_num + 1
                response.append(result['response'])
            # result = {
            #     'status': True,
            #     'code': '200',
            #     'data': response,
            #     'msg': "执行完成,成功{}个步骤，失败{}个步骤".format(success_num, error_num)
            # }
            case_result = self.update_result(ids[i], error_num)
            if case_result:
                success_cases = success_cases + 1
            else:
                error_cases = error_cases + 1
            Report.objects.filter(pk=report_id).update(success_nums=success_cases, error_nums=error_cases)
        if error_cases > 0:
            Report.objects.filter(pk=report_id).update(result=2, status=2,
                                                       end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            result = {
                'status': True,
                'code': '200',
                # 'data': response,
                'msg': "执行完成,成功{}个用例，失败{}个用例".format(success_cases, error_cases)
            }
            return Response(result)
        Report.objects.filter(pk=report_id).update(result=1, status=2,
                                                   end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        result = {
            'status': True,
            'code': '200',
            # 'data': response,
            'msg': "执行完成,成功{}个用例，失败{}个用例".format(success_cases, error_cases)
        }
        return Response(result)

    def test(self, step_data):
        # 发请求
        step_data['url'] = self.host + step_data['uri']
        step_data = dict(step_data)
        result = req_func(step_data)
        return result

    def update_result(self, id, err_nums):
        # 更新用例结果
        if err_nums > 0:
            APICase.objects.filter(pk=id).update(result=2)
            case_result = False
            return case_result
        else:
            APICase.objects.filter(pk=id).update(result=1)
            case_result = True
            return case_result

    def save_report(self, case_ids, created_user):
        # 生成报告
        name = '测试报告' + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cases = case_ids
        # result = 3
        # status = 1
        created_user = created_user
        created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_report = Report(name=name, cases=cases, created_user=created_user, created_time=created_time)
        new_report.save()
        report_id = new_report.id
        return report_id
