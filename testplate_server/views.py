# from django.shortcuts import render
# from rest_framework import serializers
from rest_framework.response import Response
# Create your views here.
from rest_framework.views import APIView


class TestView(APIView):
    def get(self, request):
        name = request.GET.get('name')
        res = {'code': 200, 'status': True, 'name': name}
        return Response(res)
