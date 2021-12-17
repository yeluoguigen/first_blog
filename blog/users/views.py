from django.shortcuts import render

from django.views import View

class RegisterView(View):
    def get(self,request):
        """
        提供注册页面
        :param request:请求对象
        :return:注册界面
        """
        return render(request,'register.html')
