from django.db.models import Count
from django.shortcuts import render
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import ProModule


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProModule
        fields = "__all__"


class ModuleList(APIView):
    """获取模块列表接口"""

    def get(self, request):
        module = ProModule.objects.all()
        serializer = ModuleSerializer(instance=module, many=True)

        def convert_to_tree(data):
            # 使用字典按id存储所有项目，便于查找
            node_map = {item['id']: {'id': item['id'], 'label': item['name'], 'parent_id': item.get('parent_id'),
                                     'children': []} for item in data}

            # 遍历数据，构建树形结构
            for item in data:
                if item['parent_id'] is not None:  # 如果有父节点
                    parent_node = node_map[item['parent_id']]
                    parent_node['children'].append(node_map[item['id']])
                else:  # 没有父节点，即根节点
                    root_nodes.append(node_map[item['id']])

            return root_nodes

        # 原始数据
        tree_data = [dict(item) for item in serializer.data]

        # 初始化根节点列表
        root_nodes = []

        # 调用函数转换数据
        tree_structure = convert_to_tree(tree_data)

        result = {
            'status': True,
            'code': 200,
            'data': tree_structure
        }
        return Response(result)


class ModuleAdd(APIView):
    """新增模块接口"""

    def post(self, request):
        serializer = ModuleSerializer(data=request.data)
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


class ModuleUpdate(APIView):
    """修改接口"""

    def post(self, request):
        id = request.data['id']
        exists = ProModule.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        data = request.data
        serializer = ModuleSerializer(data=data)
        if serializer.is_valid():
            ProModule.objects.filter(pk=id).update(**serializer.validated_data)
            res = {'status': True,
                   'code': '200',
                   'msg': "修改成功"}
            return Response(res)
        else:
            res = {'status': False,
                   'code': '500',
                   'msg': serializer.errors}
            return Response(res)


class ModuleDel(APIView):
    """删除接口"""

    def post(self, request):
        id = request.data['id']
        exists = ProModule.objects.filter(id=id).exists()
        if not exists:
            res = {'status': False,
                   'code': '500',
                   'msg': "数据不存在"}
            return Response(res)
        parent_id_exists = ProModule.objects.filter(parent_id=id).exists()
        if not parent_id_exists:
            ProModule.objects.filter(id=id).delete()
            res = {'status': True,
                   'code': '200',
                   'msg': "删除成功"}
        else:
            res = {'status': False,
                   'code': '500',
                   'msg': "该模块下存在子模块，不可删除"}
        return Response(res)
