from django.urls import path
from users.views import RegisterView,ImageCodeView,SmsCodeView
app_name = 'users'
urlpatterns = [
    #参数1:路由
    #参数2:视图函数
    #参数3:路由名，方便通过reverse 来获取路由
    path('register/',RegisterView.as_view(),name='register'),
    path('imagecode/',ImageCodeView.as_view(),name='imagecode'),
    path('smscode/',SmsCodeView.as_view(),name='smscode'),
]