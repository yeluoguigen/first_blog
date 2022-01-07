from django.urls import path
from users.views import RegisterView,ImageCodeView,SmsCodeView,LoginView,ForgetPasswordView,UserCenterView,LogoutView
app_name = 'users'
urlpatterns = [
    #参数1:路由
    #参数2:视图函数
    #参数3:路由名，方便通过reverse 来获取路由
    path('register/',RegisterView.as_view(),name='register'),
    path('imagecode/',ImageCodeView.as_view(),name='imagecode'),
    path('smscode/',SmsCodeView.as_view(),name='smscode'),
    path('login/',LoginView.as_view(),name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgetpassword/',ForgetPasswordView.as_view(),name = 'forgetpassword'),
    path('center/',UserCenterView.as_view(),name='center'),
]


