"""
URL configuration for Jtestplate project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from testplate_server.apicaseviews import APICaseAdd, APICaseList, APICaseDel, APICaseDetail, APICaseUpdate, \
    APICaseTest, APICaseDebug
from testplate_server.apiviews import APIList, APIDetail, APIAdd, APIDel, APIUpdate, APIDebug, APIImport
from testplate_server.authview import LoginView, LogoutView
from testplate_server.cronjobviews import CronJobList, CronJobDetail, CronJobAdd, CronJobUpdate, CronJobDel, \
    CronJobIsActive
from testplate_server.environmentviews import EnvironmentList, EnvironmentDetail, EnvironmentAdd, EnvironmentUpdate, \
    EnvironmentDel
from testplate_server.homeviews import APICountView, APICaseCountView
from testplate_server.promoduleviews import ModuleList
from testplate_server.reportviews import ReportList, ReportDel, ReportDetail, ReportCaseDetail
from testplate_server.userviews import UserAdd, UserDetail, UserList, UserUpdate, UserDel
from testplate_server.views import TestView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('test/', TestView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    # 用户接口
    path('user/list/', UserList.as_view()),
    path('user/detail/', UserDetail.as_view()),
    path('user/add/', UserAdd.as_view()),
    path('user/update/', UserUpdate.as_view()),
    path('user/del/', UserDel.as_view()),
    # 环境接口
    path('environment/list/', EnvironmentList.as_view()),
    path('environment/detail/', EnvironmentDetail.as_view()),
    path('environment/add/', EnvironmentAdd.as_view()),
    path('environment/update/', EnvironmentUpdate.as_view()),
    path('environment/del/', EnvironmentDel.as_view()),
    # 模块接口
    path('module/list/', ModuleList.as_view()),
    # api接口
    path('api/list/', APIList.as_view()),
    path('api/add/', APIAdd.as_view()),
    path('api/del/', APIDel.as_view()),
    path('api/detail/', APIDetail.as_view()),
    path('api/update/', APIUpdate.as_view()),
    path('api/debug/', APIDebug.as_view()),
    path('api/import/', APIImport.as_view()),
    # 接口测试用例
    path('apicase/list/', APICaseList.as_view()),
    path('apicase/add/', APICaseAdd.as_view()),
    path('apicase/del/', APICaseDel.as_view()),
    path('apicase/detail/', APICaseDetail.as_view()),
    path('apicase/update/', APICaseUpdate.as_view()),
    path('apicase/run/', APICaseTest.as_view()),
    path('apicase/debug/', APICaseDebug.as_view()),
    # 任务接口
    path('cronjob/list/', CronJobList.as_view()),
    path('cronjob/detail/', CronJobDetail.as_view()),
    path('cronjob/add/', CronJobAdd.as_view()),
    path('cronjob/update/', CronJobUpdate.as_view()),
    path('cronjob/is_active/', CronJobIsActive.as_view()),
    path('cronjob/del/', CronJobDel.as_view()),
    # 报告
    path('report/list/', ReportList.as_view()),
    path('report/del/', ReportDel.as_view()),
    path('report/detail/', ReportDetail.as_view()),
    path('report/case/detail/', ReportCaseDetail.as_view()),
    # 首页统计数据
    path('api/acount/', APICountView.as_view()),
    path('apicase/acount/', APICaseCountView.as_view()),
]
