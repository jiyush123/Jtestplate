from django.db import models


# Create your models here.
class User(models.Model):
    """用户表"""
    name = models.CharField(max_length=32, verbose_name='姓名', blank=False)
    username = models.CharField(max_length=32, verbose_name='用户名', blank=False)
    password = models.CharField(max_length=64, verbose_name='密码', blank=False)
    created_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_time = models.DateTimeField(verbose_name='修改时间')
    login_time = models.DateTimeField(verbose_name='登录时间', blank=True, null=True)

    def __str__(self):
        return self.name


class Token(models.Model):
    """这是token表"""
    token = models.CharField(max_length=256, verbose_name='token', blank=False)
    user = models.ForeignKey(to="User", to_field="id", on_delete=models.CASCADE, verbose_name='关联用户', blank=False)
    created_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    timeout_time = models.DateTimeField(verbose_name='失效时间',
                                        blank=True,
                                        null=True)


class ProModule(models.Model):
    """项目模块表"""
    name = models.CharField(verbose_name='模块名称', max_length=50)

    # 是否子模块
    # 父模块id

    def __str__(self):
        return self.name


class APIInfo(models.Model):
    """API表"""
    name = models.CharField(verbose_name='接口名称', max_length=200)
    description = models.TextField(verbose_name='描述', blank=True, default='')
    module = models.ForeignKey(to="ProModule", to_field="id", on_delete=models.SET_NULL,
                               verbose_name='所属模块', blank=True, null=True)
    method = models.CharField(verbose_name='请求方式', max_length=10)
    uri = models.CharField(verbose_name='路径', max_length=200)
    headers = models.JSONField(blank=True, null=True)
    params = models.JSONField(blank=True, null=True)
    body = models.JSONField(blank=True, null=True)
    response = models.JSONField(blank=True, null=True)
    status_choices = (
        (1, "未开始"),
        (2, "进行中"),
        (3, "已完成")
    )
    status = models.SmallIntegerField(verbose_name='状态', choices=status_choices, default=1)
    created_user = models.CharField(verbose_name='创建人', max_length=32)
    updated_user = models.CharField(verbose_name='修改人', max_length=32)
    created_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)  # auto_now_add=True
    updated_time = models.DateTimeField(verbose_name='修改时间')

    class Meta:
        db_table = 'api_info'  # 设置数据表名

    def __str__(self):
        return self.name

    def get_module_name(self):
        if self.module:
            return self.module.name
        return None


class Environment(models.Model):
    """环境表"""
    name = models.CharField(verbose_name='环境名称', max_length=50)
    protocol_choices = (
        (1, "http"),
        (2, "https")
    )
    protocol = models.SmallIntegerField(verbose_name='环境名称', choices=protocol_choices, default=1)
    host = models.CharField(verbose_name='地址', max_length=50)
    port = models.IntegerField(verbose_name='端口')

    def __str__(self):
        return self.name


class APICase(models.Model):
    """测试用例表"""
    name = models.CharField(verbose_name='用例名称', max_length=200)
    level_choices = (
        (1, "1"),
        (2, "2"),
        (3, "3")
    )
    level = models.SmallIntegerField(verbose_name='优先级', choices=level_choices)
    status_choices = (
        (1, "未开始"),
        (2, "进行中"),
        (3, "已完成")
    )
    status = models.SmallIntegerField(verbose_name='状态', choices=status_choices, default=1)
    result_choices = (
        (1, "成功"),
        (2, "失败"),
        (3, "无")
    )
    result = models.SmallIntegerField(verbose_name='结果', choices=result_choices, default=3)
    last_time = models.DateTimeField(verbose_name='最后一次执行时间', blank=True, null=True)
    created_user = models.CharField(verbose_name='创建人', max_length=32)
    updated_user = models.CharField(verbose_name='修改人', max_length=32)
    created_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_time = models.DateTimeField(verbose_name='修改时间')

    class Meta:
        db_table = 'api_case'


class APICaseStep(models.Model):
    """测试用例步骤表"""
    name = models.CharField(verbose_name='步骤名称', max_length=200)
    sort = models.SmallIntegerField(verbose_name='第几步')
    method = models.CharField(verbose_name='请求方式', max_length=10)
    uri = models.CharField(verbose_name='路径', max_length=200)
    headers = models.JSONField(blank=True, null=True)
    params = models.JSONField(blank=True, null=True)
    body = models.JSONField(blank=True, null=True)
    assert_result = models.JSONField(verbose_name='断言', blank=True, null=True)
    # 是否禁用
    before_code = models.TextField(verbose_name='前置处理',blank=True, null=True)
    after_code = models.TextField(verbose_name='后置处理',blank=True, null=True)
    extract = models.JSONField(verbose_name='提取参数', blank=True, null=True)
    api_case = models.ForeignKey(to="APICase", to_field="id", on_delete=models.CASCADE, verbose_name='关联用例')

    class Meta:
        db_table = 'api_case_step'

    def __str__(self):
        return self.name


class Report(models.Model):
    """报告表"""
    name = models.CharField(verbose_name='报告标题', max_length=200)
    end_time = models.DateTimeField(verbose_name='结束时间', blank=True, null=True)

    success_nums = models.IntegerField(verbose_name='成功用例数', default=0)
    error_nums = models.IntegerField(verbose_name='失败用例数', default=0)
    cases = models.JSONField(verbose_name='用例', blank=True, null=True)
    result_choices = (
        (1, "成功"),
        (2, "失败"),
        (3, "无")
    )
    status_choices = (
        (1, "进行中"),
        (2, "已完成")
    )
    status = models.SmallIntegerField(verbose_name='状态', choices=status_choices, default=1)
    result = models.SmallIntegerField(verbose_name='结果', choices=result_choices, default=3)
    created_user = models.CharField(verbose_name='创建人', max_length=32)
    created_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    total_time = models.IntegerField(verbose_name='执行时间', blank=True, null=True)

    class Meta:
        db_table = 'report'


class ReportCaseInfo(models.Model):
    """报告用例详情表"""
    case_id = models.IntegerField(verbose_name='用例id', blank=False)
    step_name = models.CharField(verbose_name='步骤名称', max_length=200)
    run_time = models.IntegerField(verbose_name='执行时间', blank=True, null=True)
    step_result_choices = (
        (1, "成功"),
        (2, "失败"),
        (3, "无")
    )
    step_result = models.SmallIntegerField(verbose_name='结果', choices=step_result_choices, default=3)
    step_response = models.JSONField(verbose_name='响应', blank=True, null=True)
    assert_info = models.JSONField(verbose_name='断言结果', blank=True, null=True)
    report = models.ForeignKey(to="Report", to_field="id", on_delete=models.CASCADE, verbose_name='关联报告')

    class Meta:
        db_table = 'report_case_info'
