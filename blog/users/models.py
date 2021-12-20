from django.db import models
from django.contrib.auth.models import AbstractUser
class User(AbstractUser):
    #手机号
    mobile = models.CharField(max_length=20,unique=True,blank=True)
    #头像
    avatar = models.ImageField(upload_to='avatar/%Y%m%d/',blank=True)
    #个人简介
    user_desc= models.TextField(max_length=500,blank=True)
    #修改认证字段
    USERNAME_FIELD = 'mobile'

    #创建超级管理员的需要必须输入的字段
    REQUIRED_FIELDS = ['username','email']
    #内部类class Meta 用于给model定义元数据
    class Meta:
        db_table = 'tb_user'     #修改默认的表名
        verbose_name = '用户信息'  #Admin后台显示
        verbose_name_plural = verbose_name  #Admin后台显示

    def __str__(self):
        return self.mobile
