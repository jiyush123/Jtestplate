import time
from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import QueryDict
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import APICase, APICaseStep, Report, ReportCaseInfo
from testplate_server.utils.built_in_methods import ExtractVariables  # 处理前后置参数vars.get() vars.put()
from testplate_server.utils.extract_params import extract_func
from testplate_server.utils.paginator_fun import paginator_fun
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
        request.data['created_user'] = request.operator
        request.data['updated_user'] = request.operator
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
        try:
            # 使用字典推导式过滤参数，增加输入验证
            sq = request.GET
            excluded_keys = ['size', 'page']
            # 键k不在excluded_keys列表中且值v不为空
            filtered_params = {k: v for k, v in sq.items() if k not in excluded_keys and v}

            # 处理模糊查询参数映射
            if 'name' in filtered_params:
                filtered_params['name__contains'] = filtered_params.pop('name')
            size = int(request.GET.get('size', 10))  # 设置默认值以避免ValueError
            page = int(request.GET.get('page', 1))
            # 使用django的分页方法
            queryset = paginator_fun(table_obj=APICase,
                                     filtered=filtered_params,
                                     order_by='-id', page=page, size=size)
            serializer = APICaseListSerializer(instance=queryset[0], many=True)

            result = {
                'status': True,
                'code': 200,
                'data': serializer.data,
                'total': queryset[1],  # 使用paginator的count属性
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
        request.data['updated_user'] = request.operator
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
        steps = request.data.get('steps')
        host = request.data.get('env')
        # 获取用例步骤
        len_steps = len(steps)
        # 遍历步骤，要记录每一次的返回和耗时
        resp = []
        extract_data = {}
        for i in range(len_steps):
            step = steps[i]

            url = host + step.get('uri')
            # 这里获取前置处理代码并执行
            before_code = step.get('before_code')
            vars = ExtractVariables(extract_data)  # vars在前后置处理时使用vars.get() vars.put()
            execute_before_after_code(before_code)
            # 这里生成请求数据
            req_data = {'url': url, 'method': step.get('method'), 'headers': step.get('headers'),
                        'params': step.get('params'), 'body': step.get('body'),
                        'assert_result': step.get('assert_result')}
            # 根据提取参数重构请求参数
            req_data = generate_req_data(req_data, extract_data)

            debug_result = req_func(req_data)

            resp.append(debug_result)

            # 获取提取参数
            save_extract(extract_data, step.get('extract'), debug_result)

            # 这里获取后置处理代码并执行
            after_code = step.get('after_code')
            execute_before_after_code(after_code)

        res = {'status': True,
               'code': '200',
               'data': {'res': resp},
               'msg': "调试完成"}
        return Response(res)


class APICaseTest(APIView):
    # 接收测试用例id
    def post(self, request):
        # 因为是drf封装了一层request，所以通过后端直接发送的字典会变成QueryDict（定时任务触发），而QueryDict只能通过getlist方法保留完整的列表，所以要判断类型
        if isinstance(request.data, QueryDict):
            ids = request.data.getlist('ids')  # 获取ids的列表
        else:
            ids = request.data['ids']  # 正常触发执行获取列表
        success_cases = 0  # 初始化成功的用例数
        error_cases = 0  # 初始化失败的用例数
        # 生成报告
        start_run_time = time.time_ns()  # 报告开始时间
        created_user = request.operator  # operator是通过django中间件根据token的用户信息插入到请求的

        case_info = []  # 初始化用例id列表
        step_list = []  # 步骤详情列表
        # 开始组织用例
        for i in range(len(ids)):
            # 判断用例是否存在
            exists = APICase.objects.filter(id=ids[i]).exists()
            if not exists:
                res = {'status': False,
                       'code': '500',
                       'msg': "数据不存在"}
                return Response(res)
            # 找到对应的数据
            # 获取用例信息
            case_queryset = APICase.objects.filter(id=ids[i]).first()
            case_serializer = APICaseInfoSerializer(instance=case_queryset)
            # 更新用例上一次操作时间
            APICase.objects.filter(pk=ids[i]).update(last_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            # 获取步骤信息
            step_queryset = APICaseStep.objects.filter(api_case=case_serializer.data['id']).order_by('sort')
            step_serializer = APICaseStepInfoSerializer(instance=step_queryset, many=True)
            len_step = len(step_serializer.data)  # 获取步骤数量
            host = request.data['host']
            error_num = 0  # 设置步骤失败次数为0
            response = []  # 还没存库，设置返回为空列表
            # 执行用例
            start_time = time.time_ns()  # 这是纳秒，用例开始的时间
            extract_data = {}  # 提取参数临时变量
            for j in range(len_step):
                try:
                    step_data = dict(step_serializer.data[j])
                    # 这里获取前置处理代码并执行
                    vars = ExtractVariables(extract_data)  # vars在前后置处理时使用vars.get() vars.put()
                    before_code = step_data.get('before_code')
                    execute_before_after_code(before_code)  # 执行自定义代码
                    step_data['url'] = host + step_data['uri']
                    # 根据提取参数重构请求参数
                    step_data = generate_req_data(step_data, extract_data)
                    # 执行用例，提取结果和时间和断言详情
                    result = req_func(step_data)
                    assert_info = result.get('assert_info')
                    active_time = result.get('run_time')
                    # 获取提取参数
                    save_extract(extract_data, step_data.get('extract'), result)

                    # 根据断言结果判断步骤是否成功
                    # step_result = 3  # 3为无结果
                    for k, v in assert_info.items():
                        if v.get('result') == 'error':
                            error_num += 1
                            step_result = 2
                            break
                    # for else 循环没有经过break跳出，则最后执行else语句
                    else:
                        step_result = 1
                    response.append(result.get('response'))
                    # 保存到用例详情表
                    # 排除键为assert_info，则排除断言信息
                    step_response = {k: v for k, v in result.items() if (k != 'assert_info' or k != 'run_time')}

                    # 步骤详情
                    step_info = {'case_id': ids[i], 'step_name': step_data['name'], 'run_time': active_time,
                                 'step_result': step_result, 'step_response': step_response,
                                 'assert_info': assert_info}
                    # 步骤详情列表
                    step_list.append(step_info)
                    # 这里获取后置处理代码并执行
                    after_code = step_data.get('after_code')
                    execute_before_after_code(after_code)

                except Exception as e:
                    error_num = error_num + 1
                    response.append(e)

            end_time = time.time_ns()  # 用例结束时间
            run_time = (end_time - start_time) / 1000000  # 转化成ms
            case_result = self.update_result(ids[i], error_num)  # 更新用例结果
            # 生成用例执行详情
            case_info.append({'case_id': ids[i],
                              'case_name': case_serializer.data['name'],
                              'run_time': run_time,
                              'case_result': case_result})

            if case_result:
                success_cases = success_cases + 1
            else:
                error_cases = error_cases + 1
        # 报告结束时间
        report_end_time = datetime.fromtimestamp(time.time_ns() / 1000000000).strftime('%Y-%m-%d %H:%M:%S')
        total_time = (time.time_ns() - start_run_time) / 1000000  # 报告运行时间ms单位
        if error_cases > 0:
            case_result = 2
        else:
            case_result = 1

        # 最后一次生成报告插入数据库
        # 获取报告id
        report_id = self.save_report(created_user=created_user, cases=case_info, success_nums=success_cases,
                                     error_nums=error_cases,
                                     end_time=report_end_time, result=case_result, status=2,
                                     total_time=total_time)  # 保存报告返回报告的id，用于后续更新状态

        # 生成步骤详情
        for i in range(len(step_list)):
            print(step_list[i])
            self.save_report_case_info(report_id=report_id, **step_list[i])

        result = {
            'status': True,
            'code': '200',
            'msg': "执行完成,成功{}个用例，失败{}个用例".format(success_cases, error_cases)
        }
        return Response(result)

    def save_report(self, created_user, **kwargs):
        # 生成报告
        name = '测试报告' + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        created_user = created_user
        created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_report = Report(name=name, created_user=created_user, created_time=created_time, **kwargs)
        new_report.save()
        report_id = new_report.id
        return report_id

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

    def save_report_case_info(self, case_id, step_name, run_time, step_result, step_response, assert_info,
                              report_id):
        # 生成报告的用例详情
        case_info = ReportCaseInfo(case_id=case_id, step_name=step_name, run_time=run_time, step_result=step_result,
                                   step_response=step_response, assert_info=assert_info, report_id=report_id)
        case_info.save()


def generate_req_data(req_data, extract_data):
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
    return req_data


def save_extract(extract_data, requset_extract, result):
    # 根据jsonpath获取响应值extract_val
    if requset_extract:
        for k, v in requset_extract.items():
            extract_jsonpath = v['value'].split('.')
            extract_val = result
            for obj in extract_jsonpath:
                extract_val = extract_val.get(obj)
                # 如果匹配不到返回None,则将期望值直接赋值为None并退出循环
                if extract_val is None:
                    break
            # 存到临时字典extract_data中
            extract_data[k] = extract_val


def execute_before_after_code(code):
    try:
        exec(code)
    except Exception as e:
        print(e)
