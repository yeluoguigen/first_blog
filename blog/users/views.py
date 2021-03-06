from django.shortcuts import render
from django.http import HttpResponseBadRequest,HttpResponse
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http import JsonResponse
from utils.response_code import RETCODE
from random import randint
from libs.yuntongxun.sms import CCP
import re
from users.models import User
from django.db import DatabaseError
from django.shortcuts import redirect
from django.urls import reverse

from django.contrib.auth import login
from django.contrib.auth import authenticate
from django.contrib.auth import logout

from django.contrib.auth.mixins import LoginRequiredMixin
import logging
import traceback
from django.views import View
from home.models import ArticleCategory,Article
logger=logging.getLogger('django')

class RegisterView(View):
    def get(self,request):
        """
        提供注册页面
        :param request:请求对象
        :return:注册界面
        """
        return render(request,'register.html')

    def post(self,request):
        #接收参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        smscode = request.POST.get('sms_code')
        #判断参数是否齐全
        if not all([mobile,password,password2,smscode]):
            return HttpResponseBadRequest("缺少必传参数")
        #判断手机号是否违法
        if not re.match(r'^1[3,9]\d{9}$',mobile):
            return HttpResponseBadRequest("请输入正确的手机号")
        #判断密码是否是8-20位的数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return HttpResponseBadRequest('请输入8到20位的密码')
        #判断两次密码是否一致：
        if password != password2:
            return HttpResponseBadRequest('两次输入的密码不一致')
        #验证短信验证码
        redis_conn = get_redis_connection('default')
        sms_code_server = redis_conn.get('sms:%s'%mobile)
        if sms_code_server is None:
            return HttpResponseBadRequest('短信验证码已过期')
        if smscode != sms_code_server.decode():
            return HttpResponseBadRequest('短信验证码错误')
        print('{}-{}'.format(mobile,password))
        #保存注册数据
        try:
            user = User.objects.create_user(username=mobile,mobile = mobile,password = password)
        except DatabaseError:
            print(traceback.format_exc())
            return HttpResponseBadRequest('注册失败')
        #实现状态保持
        from django.contrib.auth import login
        login(request,user)
        #跳转到首页
        response = redirect(reverse('home:index'))
        #设置cookie
        #登录状态，会话结束后自动过期
        response.set_cookie('is_login',True)
        #设置用户名有效期是1个月
        response.set_cookie('username',user.username,max_age=30*24*3600)
        return response


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

class SmsCodeView(View):
    def get(self,request):
        #接收参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
        mobile = request.GET.get('mobile')

        #校验参数
        if not all([image_code_client,uuid,mobile]):
            return JsonResponse({"code":RETCODE.NECESSARYPARAMERR,"ERRMSG":"缺少必传参数"})
        #创建连接到redis的对象
        redis_conn= get_redis_connection('default')
        #提取图形验证码
        image_code_server = redis_conn.get('img:%s'%uuid)
        if image_code_server is None:
            return JsonResponse({"code":RETCODE.IMAGECODEERR,"errmsg":"验证码失效"})
        #删除验证码，避免恶意测试验证码
        try:
            redis_conn.delete('img:%s'%uuid)
        except Exception as e:
            logger.error(e)
        #对比图形验证码
        image_code_server = image_code_server.decode() #byte转字符串
        if image_code_server.lower() != image_code_client.lower():
            return JsonResponse({"code":RETCODE.IMAGECODEERR,"errmsg":"输入验证码有误"})
        #生成短信验证码:生成6位数验证码
        sms_coed = '%06d'%randint(0,999999)
        logger.info(sms_coed)
        #保存验证码到redis中，并设置有效期
        redis_conn.setex('sms:%s'%mobile,300,sms_coed)
        #发送短信验证码
        CCP().send_template_sms(mobile,[sms_coed,5],1)

        #响应结果
        return JsonResponse({"code":RETCODE.OK,"errmsg":"发送短信成功"})

class LoginView(View):
    def get(self,request):
        return render(request,'login.html')
    def post(self,request):
        #接收参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        #检查参数是否齐全
        if not all([mobile,password]):
            return HttpResponseBadRequest('缺少必传参数')
        #判断手机号是否正确
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return HttpResponseBadRequest('请输入正确的手机号')
        #判断密码是否是8到20位数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return HttpResponseBadRequest('密码最少8位，最长20位')
        #认证登录用户
        #认证字段已经在User 模型中的USERNAME='mobile'修改
        user = authenticate(mobile=mobile,password=password)
        if user is None:
            return HttpResponseBadRequest('用户名或密码错误')
        #实现状态保持
        login(request,user)
        #响应登录结果
        next = request.GET.get('next')
        if next:
            response = redirect(next)
        else:
            response = redirect(reverse('home:index'))
        #设置状态保持的周期
        if remember != 'on':
            #没有记住用户，浏览器会话结合就过期
            request.session.set_expiry(0)
            #设置cookie
            response.set_cookie('is_login',True)
            response.set_cookie('username',user.username,max_age=30*24*3600)
        else:
            #记住用户：None表示两周后过期
            request.session.set_expiry(None)
            #设置Cookie
            response.set_cookie('is_login',True,max_age=14*24*3600)
            response.set_cookie('username',user.username,max_age=30*24*3600)
        #返回响应
        return response


class LogoutView(View):
    def get(self,request):
        #清理session
        logout(request)
        #退出登录，重新跳转到首页
        response = redirect(reverse('home:index'))
        #退出登录时清除cookie中登录状态
        response.delete_cookie('is_login')
        return response

class ForgetPasswordView(View):
    def get(self,request):
        return render(request,'forget_password.html')
    def post(self,request):
        #接收参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        smscode = request.POST.get('sms_code')
        #判断参数是否齐全
        if not all([mobile,password,password2,smscode]):
            return HttpResponseBadRequest('缺少必传参数')
        #判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return HttpResponseBadRequest('请输入正确的电话号码')
        #判断密码是否是8到20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return HttpResponseBadRequest('请输入8到20位的密码')
        #判断两次密码是否一致
        if password != password2:
            return HttpResponseBadRequest('两次的密码不一致')
        #验证短信验证码
        redis_conn = get_redis_connection('default')
        sms_code_server = redis_conn.get('sms:%s'%mobile)
        if sms_code_server is None:
            return HttpResponseBadRequest('短信验证码已过期')
        if smscode !=sms_code_server.decode():
            return HttpResponseBadRequest('短信验证码错误')
        #根据手机号查询数据
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            #如果手机号不存在，则注册个新用户
            try:
                User.objects.create_user(username=mobile,mobile=mobile,password=password)
            except Exception:
                return HttpResponseBadRequest('修改失败，请稍后再试')
        else:
            #修改用户密码
            user.set_password(password)
            user.save()
        #跳转到登录页面
        response=  redirect(reverse('users:login'))
        return response

class UserCenterView(LoginRequiredMixin,View):
    def get(self,request):
        #获取用户信息
        user = request.user
        #组织模板渲染数据
        context = {
            'username':user.username,
            'mobile':user.mobile,
            'avatar':user.avatar.url if user.avatar else None,
            'user_desc':user.user_desc
        }
        return render(request,'center.html',context=context)

    def post(self,request):
        #接收数据
        user = request.user
        avatar = request.FILES.get('avatar')
        username = request.POST.get('username',user.username)
        user_desc = request.POST.get('desc',user.user_desc)
        #修改数据库数据
        try:
            user.username = username
            user.user_desc = user_desc
            if avatar:
                user.avatar = avatar
            user.save()
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('更新失败，请稍后再试')
        # 返回响应，刷新页面
        response = redirect(reverse('users:center'))
        #更新cookie信息
        response.set_cookie('username',user.username,max_age=30*24*3600)
        return response

class WriteBlogView(LoginRequiredMixin,View):
    def get(self,request):
        #获取博客分类信息
        categories = ArticleCategory.objects.all()
        context = {
            'categories':categories
        }
        return render(request,'write_blog.html',context)

    def post(self,request):
        #接收数据
        avatar = request.FILES.get('avatar')
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        tags = request.POST.get('tags')
        sumary = request.POST.get('sumary')
        content = request.POST.get('content')
        user = request.user

        #验证数据是否齐全
        if not all([avatar,title,category_id,sumary,content]):
            return HttpResponseBadRequest('参数不全')
        #判断文章分类id数据是否正确
        try:
            article_category = ArticleCategory.objects.get(id=category_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseBadRequest('没有此类信息')
        #保存到数据库
        try:
            Article.objects.create(
                author=user,
                avatar=avatar,
                category=article_category,
                tags=tags,
                title=title,
                sumary=sumary,
                content=content
            )
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('发布失败,请稍后再试')
        #返回响应，跳转到文章详情页面
        #暂时跳转到首页
        return redirect(reverse('home:index'))




