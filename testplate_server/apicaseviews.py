import time
from datetime import datetime

from django.db.models import Count
from django.http import QueryDict
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import APICase, APICaseStep, Report, ReportCaseInfo
from testplate_server.utils.built_in_methods import ExtractVariables  # 处理前后置参数vars.get() vars.put()
from testplate_server.utils.extract_params import extract_func
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


class APICaseDebug(APIView):
    def post(self, request):
        # print(request.data)
        steps = request.data.get('steps')
        host = request.data.get('env')
        # 获取用例步骤
        len_steps = len(steps)
        # 遍历步骤，要记录每一次的返回和耗时
        resp = []
        steps_time = []
        extract_data = {}
        for i in range(len_steps):
            start_time = time.time_ns()
            step = steps[i]

            url = host + step.get('uri')
            # 这里获取前置处理代码并执行
            before_code = step.get('before_code')
            vars = ExtractVariables(extract_data)  # vars在前后置处理时使用vars.get() vars.put()
            try:
                exec(before_code)
            except Exception:
                pass
            # 这里生成请求数据
            req_data = {'url': url, 'method': step.get('method'), 'headers': step.get('headers'),
                        'params': step.get('params'), 'body': step.get('body'),
                        'assert_result': step.get('assert_result')}
            # url是否含${}，循环查找请求头，请求参数，请求体，断言中v['value']是否含${}
            req_data['url'] = extract_func(req_data['url'], extract_data)
            if req_data['headers'] is not None:
                for k, v in req_data['headers'].items():
                    v['value'] = extract_func(v.get('value'), extract_data)
            if req_data['params'] is not None:
                for k, v in req_data['params'].items():
                    v['value'] = extract_func(v.get('value'), extract_data)
            if req_data['body'] is not None:
                for k, v in req_data['body'].items():
                    v['value'] = extract_func(v.get('value'), extract_data)
            if req_data['assert_result'] is not None:
                for k, v in req_data['assert_result'].items():
                    v['value'] = extract_func(v.get('value'), extract_data)
            debug_result = req_func(req_data)
            end_time = time.time_ns()
            run_time = (end_time - start_time) / 1000000
            steps_time.append(run_time)

            resp.append(debug_result)

            # 获取提取参数，根据jsonpath获取响应值extract_val
            if step.get('extract') is not None:
                extract = step.get('extract')
                for k, v in extract.items():
                    extract_jsonpath = v['value'].split('.')
                    extract_val = debug_result
                    for i in extract_jsonpath:
                        if i in extract_val:
                            extract_val = extract_val[i]
                        else:
                            extract_val = None
                            break
                    # 存到临时字典extract_data中
                    extract_data[k] = extract_val
                # 这里获取后置处理代码并执行
                after_code = step.get('after_code')
                try:
                    exec(after_code)
                except Exception:
                    pass

        res = {'status': True,
               'code': '200',
               'data': {'res': resp, 'time': steps_time},
               'msg': "调试完成"}
        return Response(res)


class APICaseTest(APIView):
    # 接收测试用例id
    def post(self, request):
        # 因为是drf封装了一层request，所以通过后端发送的字典会变成QueryDict，而QueryDict只能通过getlist方法保留完整的列表，所以要判断类型
        if isinstance(request.data, QueryDict):
            ids = request.data.getlist('ids')
        else:
            ids = request.data['ids']
        success_cases = 0
        error_cases = 0
        # 生成报告
        start_run_time = time.time_ns()  # 报告开始时间
        created_user = request.data['created_user']
        report_id = self.save_report(created_user)
        case_info = []
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
            error_num = 0
            response = []  # 还没存库
            # 执行用例
            start_time = time.time_ns()  # 这是纳秒
            extract_data = {}  # 提取参数临时变量
            for j in range(self.len_step):
                try:
                    step_data = dict(self.step_serializer.data[j])
                    # 这里获取前置处理代码并执行
                    before_code = step_data.get('before_code')
                    vars = ExtractVariables(extract_data)  # vars在前后置处理时使用vars.get() vars.put()
                    try:
                        exec(before_code)
                    except Exception:
                        pass

                    step_data['uri'] = extract_func(step_data['uri'], extract_data)
                    if step_data['headers'] is not None:
                        for k, v in step_data['headers'].items():
                            v['value'] = extract_func(v.get('value'), extract_data)
                    if step_data['params'] is not None:
                        for k, v in step_data['params'].items():
                            v['value'] = extract_func(v.get('value'), extract_data)
                    if step_data['body'] is not None:
                        for k, v in step_data['body'].items():
                            v['value'] = extract_func(v.get('value'), extract_data)
                    if step_data['assert_result'] is not None:
                        for k, v in step_data['assert_result'].items():
                            v['value'] = extract_func(v.get('value'), extract_data)
                    # 执行用例，提取结果和时间和断言详情
                    result_info = self.test(step_data)
                    result = result_info[0]
                    assert_info = result.get('assert_info')
                    active_time = result_info[1]
                    # 获取提取参数，根据jsonpath获取响应值extract_val
                    extract = step_data.get('extract')
                    if step_data['extract'] is not None:
                        for k, v in extract.items():
                            extract_jsonpath = v['value'].split('.')
                            extract_val = result
                            for obj in extract_jsonpath:
                                if obj in extract_val:
                                    extract_val = extract_val[obj]
                                else:
                                    extract_val = None
                                    break
                            # 存到临时字典extract_data中
                            extract_data[k] = extract_val
                    # 根据断言结果判断步骤是否成功
                    step_result = 3
                    # assert_info {'key': {'expect': '', 'value': '', 'result': 'success'}}
                    for k, v in assert_info.items():
                        if v.get('result') == 'error':
                            error_num += 1
                            step_result = 2
                            break
                    if step_result != 2:
                        step_result = 1
                    response.append(result['response'])
                    # 保存到用例详情表
                    step_response = {k: v for k, v in result.items() if k != 'assert_info'}

                    self.save_report_case_info(case_id=ids[i], step_name=step_data['name'], run_time=active_time,
                                               step_result=step_result, step_response=step_response,
                                               assert_info=assert_info, report_id=report_id)
                    # 这里获取后置处理代码并执行
                    after_code = step_data.get('after_code')
                    try:
                        exec(after_code)
                    except Exception:
                        pass

                except Exception as e:
                    error_num = error_num + 1
                    response.append(e)

            end_time = time.time_ns()  # 用例结束时间
            run_time = (end_time - start_time) / 1000000  # 转化成ms
            case_result = self.update_result(ids[i], error_num)
            case_info.append({'case_id': ids[i],
                              'case_name': case_serializer.data['name'],
                              'run_time': run_time,
                              'case_result': case_result})

            if case_result:
                success_cases = success_cases + 1
            else:
                error_cases = error_cases + 1
            Report.objects.filter(pk=report_id).update(cases=case_info, success_nums=success_cases,
                                                       error_nums=error_cases,
                                                       end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        total_time = (time.time_ns() - start_run_time) / 1000000  # 报告运行时间ms单位
        if error_cases > 0:
            case_result = 2
        else:
            case_result = 1
        Report.objects.filter(pk=report_id).update(result=case_result, status=2, total_time=total_time)
        result = {
            'status': True,
            'code': '200',
            'msg': "执行完成,成功{}个用例，失败{}个用例".format(success_cases, error_cases)
        }
        return Response(result)

    def test(self, step_data):
        # 发请求
        step_data['url'] = self.host + step_data['uri']
        # 开始时间
        start_time = time.time_ns()
        test_result = req_func(step_data)
        result = test_result
        # 结束时间
        end_time = time.time_ns()
        # 执行时间
        run_time = (end_time - start_time) / 1000000
        return result, run_time

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

    def save_report(self, created_user):
        # 生成报告
        name = '测试报告' + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        created_user = created_user
        created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_report = Report(name=name, created_user=created_user, created_time=created_time)
        new_report.save()
        report_id = new_report.id
        return report_id

    def save_report_case_info(self, case_id, step_name, run_time, step_result, step_response, assert_info,
                              report_id):
        # 生成报告的用例详情
        case_info = ReportCaseInfo(case_id=case_id, step_name=step_name, run_time=run_time, step_result=step_result,
                                   step_response=step_response, assert_info=assert_info, report_id=report_id)
        case_info.save()
