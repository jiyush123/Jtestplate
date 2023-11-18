from django.db.models import Count
from django.shortcuts import render
from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView

from testplate_server.models import ProModule


class ModuleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProModule
        fields = "__all__"


class ModuleList(APIView):
    """获取模块列表接口"""

    def get(self, request):
        module = ProModule.objects.all()
        serializer = ModuleListSerializer(instance=module, many=True)

        result = {
            'status': True,
            'code': 200,
            'data': serializer.data
        }
        return Response(result)
