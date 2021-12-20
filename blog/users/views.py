from django.shortcuts import render
from django.views import View
from django.http import HttpResponseBadRequest,HttpResponse
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection

class RegisterView(View):
    def get(self,request):
        """
        提供注册页面
        :param request:请求对象
        :return:注册界面
        """
        return render(request,'register.html')

class ImageCodeView(View):

    def get(self,request):
        #获取前端传递过来的参数
        uuid = request.GET.get('uuid')
        #判断参数是否是Nine
        if uuid is None:
            return HttpResponseBadRequest("请求参数错误")
        #获取获取验证码内容和验证码图片二进制数据
        text,image = captcha.generate_captcha()
        #将图片验证码内容保存在redis中，并设置过期时间
        redis_conn = get_redis_connection('default')
        redis_conn.setex('img:%s'%uuid,300,text)
        print('ceshi')
        #返回相应，将生成的图片以content_type为image/jpeg的形式返回给请求
        return HttpResponse(image,content_type='image/jpeg')

