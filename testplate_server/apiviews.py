from datetime import datetime

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Count
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import APIInfo, ProModule
from testplate_server.utils.load_swagger_api import generate_from_url, generate_from_jsonfile
from testplate_server.utils.request import req_func


class ApiListSerializer(serializers.ModelSerializer):
    # 这样就可以获取枚举值的值
    status = serializers.CharField(source='get_status_display')
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    module = serializers.CharField(source='get_module_name')

    class Meta:
        model = APIInfo
        fields = ['id', 'name', 'description', 'module', 'method', 'uri', 'status', 'created_user', 'updated_time']


class ApiInfoSerializer(serializers.ModelSerializer):
    # 这样就可以获取枚举值的值，API列表跟详情用同一个序列化器，前端根据需要取字段显示
    status = serializers.CharField(source='get_status_display')
    mod_id = serializers.IntegerField(source='module_id')
    module = serializers.CharField(source='get_module_name')
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = APIInfo
        fields = "__all__"


class ApiAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIInfo
        exclude = ["updated_time"]


class ApiUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIInfo
        exclude = ["created_user", "created_time", "updated_time"]


class APIList(APIView):
    """获取api列表接口"""

    def get(self, request):
        sq = request.GET
        excluded_keys = ['size', 'page']
        filtered_params = {k: v for k, v in sq.items() if k not in excluded_keys}
        # 获取列表的查询字段后，根据需要进行模糊查询
        if 'name' in filtered_params:
            filtered_params['name__contains'] = filtered_params['name']
            filtered_params.pop('name')
        if 'module' in filtered_params:
            module_ids = ProModule.objects.filter(name__contains=filtered_params['module']).values_list('id', flat=True)
            filtered_params['module_id__in'] = module_ids
            filtered_params.pop('module')

        api_info = APIInfo.objects.filter(**filtered_params)
        size = int(request.GET.get('size'))
        page = int(request.GET.get('page'))
        queryset = api_info.annotate(count=Count('id')).order_by('-id')

        # slice方法进行分页
        start = (page - 1) * size
        end = start + size
        queryset = queryset[start:end]
        # serializer = ApiListSerializer(instance=queryset, many=True)
        serializer = ApiInfoSerializer(instance=queryset, many=True)

        result = {
            'status': True,
            'code': 200,
            'data': serializer.data,
            'total': api_info.count(),
            'page': page,
            'size': size
        }
        return Response(result)


class APIDetail(APIView):
    """获取API详情"""

    def get(self, request):
        id = request.GET.get('id')
        exists = APIInfo.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        queryset = APIInfo.objects.filter(id=id).first()
        # 获取所有字段
        serializer = ApiInfoSerializer(instance=queryset)
        result = {
            'status': True,
            'code': 200,
            'data': serializer.data
        }
        return Response(result)


class APIAdd(APIView):
    """新增接口"""

    def post(self, request):
        print(request.data)
        serializer = ApiAddSerializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['updated_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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


class APIDel(APIView):
    """删除接口"""

    def post(self, request):
        id = request.data['id']
        exists = APIInfo.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        APIInfo.objects.filter(id=id).delete()
        res = {'status': True,
               'code': '200',
               'msg': "删除成功"}
        return Response(res)


class APIUpdate(APIView):
    """修改接口"""

    def post(self, request):
        id = request.data['id']
        exists = APIInfo.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        data = request.data
        serializer = ApiUpdateSerializer(data=data)
        if serializer.is_valid():
            serializer.validated_data['updated_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            APIInfo.objects.filter(pk=id).update(**serializer.validated_data)
            res = {'status': True,
                   'code': '200',
                   'msg': "修改成功"}
            return Response(res)
        else:
            res = {'status': False,
                   'code': '500',
                   'msg': serializer.errors}
            return Response(res)


class APIDebug(APIView):
    """调试API接口"""

    def post(self, request):
        request.data['url'] = request.data['host'] + request.data['uri']
        result = req_func(request.data)
        return Response(result)


class GetAPIImportList(APIView):
    """从文件或者url获取所有接口列表"""

    def post(self, request):
        # 假设您已经有了一个名为request的HttpRequest对象
        try:
            uploaded_file = request.FILES.get('file', None)  # 从请求中获取文件
            if uploaded_file is not None and isinstance(uploaded_file,
                                                        InMemoryUploadedFile):  # 确保有文件且是InMemoryUploadedFile类型

                file_content = uploaded_file.read().decode('utf-8')  # 读取文件内容

                # 调用方法将json数据转换成字典，并获取到最后的api信息列表
                api_list = generate_from_jsonfile(file_content)
                res = {'status': True,
                       'code': '200',
                       'data': api_list,
                       'msg': "导入成功"}
                return Response(res)

            else:
                import_url = request.data.get('url')
                api_list = generate_from_url(import_url)
                res = {'status': True,
                       'code': '200',
                       'data': api_list,
                       'msg': "导入成功"}
                return Response(res)
        except:
            res = {'status': False,
                   'code': '500',
                   'msg': "导入失败"}
            return Response(res)


class ImportAPI(APIView):
    """导入接口"""

    def post(self, request):
        apis_list = request.data.get('apis_list')
        created_user = request.data.get('created_user')
        updated_user = request.data.get('updated_user')
        for i in range(len(apis_list)):
            name = apis_list[i]['name']
            description = apis_list[i]['description']
            module = 1
            method = apis_list[i]['method'].upper()
            uri = apis_list[i]['uri']
            headers = apis_list[i]['headers']
            params = apis_list[i]['params']
            body = apis_list[i]['body']
            response = apis_list[i]['response']
            import_data = {'name': name, 'description': description, 'module': module, 'method': method, 'uri': uri,
                           'headers': headers, 'params': params, 'body': body, 'response': response,
                           'created_user': created_user, 'updated_user': updated_user}
            serializer = ApiAddSerializer(data=import_data)
            if serializer.is_valid():
                serializer.validated_data['updated_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                serializer.save()
            else:
                res = {'status': False,
                       'code': '500',
                       'msg': serializer.errors}
                return Response(res)
        res = {'status': True,
               'code': '200',
               'msg': "导入成功"}
        return Response(res)
