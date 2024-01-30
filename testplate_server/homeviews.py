from rest_framework import serializers, generics, status
from rest_framework.response import Response
# Create your views here.
# from rest_framework.views import APIView

from testplate_server.models import APIInfo, APICase


class APICountSerializer(serializers.Serializer):
    not_started_total = serializers.IntegerField()
    in_progress_total = serializers.IntegerField()
    completed_total = serializers.IntegerField()
    total = serializers.IntegerField()


class APICountView(generics.GenericAPIView):
    serializer_class = APICountSerializer

    def get(self, request, *args, **kwargs):
        not_started_count = APIInfo.objects.filter(status=1).count()
        in_progress_count = APIInfo.objects.filter(status=2).count()
        completed_count = APIInfo.objects.filter(status=3).count()

        data = {
            'not_started_total': not_started_count,
            'in_progress_total': in_progress_count,
            'completed_total': completed_count,
            'total': not_started_count+in_progress_count+completed_count
        }

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)  # 验证数据是否符合序列化器结构要求
        result = {
            'status': True,
            'code': 200,
            'data': serializer.data
        }

        return Response(result, status=status.HTTP_200_OK)


class APICaseCountSerializer(serializers.Serializer):
    not_started_total = serializers.IntegerField()
    in_progress_total = serializers.IntegerField()
    completed_total = serializers.IntegerField()
    total = serializers.IntegerField()
    pass_percent = serializers.FloatField()


class APICaseCountView(generics.GenericAPIView):
    serializer_class = APICaseCountSerializer

    def get(self, request, *args, **kwargs):
        not_started_count = APICase.objects.filter(status=1).count()
        in_progress_count = APICase.objects.filter(status=2).count()
        completed_count = APICase.objects.filter(status=3).count()
        pass_percent = round((APICase.objects.filter(result=1).count() / APICase.objects.count())*100,2)

        data = {
            'not_started_total': not_started_count,
            'in_progress_total': in_progress_count,
            'completed_total': completed_count,
            'total': not_started_count+in_progress_count+completed_count,
            'pass_percent': pass_percent
        }

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)  # 验证数据是否符合序列化器结构要求
        result = {
            'status': True,
            'code': 200,
            'data': serializer.data
        }

        return Response(result, status=status.HTTP_200_OK)
