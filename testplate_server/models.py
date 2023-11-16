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
