from django.db import models
from users.models import User
from django.utils import timezone

class ArticleCategory(models.Model):
    """
    文章分类
    """
    #栏目标题
    title = models.CharField(max_length=100,blank=True)
    #创建时间
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'tb_category'
        verbose_name = '类别管理'
        verbose_name_plural = verbose_name

class Article(models.Model):
    """
    文章
    """
    author = models.ForeignKey(User,on_delete=models.CASCADE)
    #文章标题图
    avatar = models.ImageField(upload_to='article/%Y%m%d',blank=True)
    #文章栏目的一对多外键
    category = models.ForeignKey(
        ArticleCategory,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='article'
    )
    #文章标签
    tags = models.CharField(max_length=20,blank=True)
    #文章标题
    title = models.CharField(max_length=100,null=False,blank=False)
    #概要
    sumary = models.CharField(max_length=200,null=False,blank=True)
    #文章正文
    content = models.TextField()
    #浏览量
    total_views = models.PositiveIntegerField(default=0)
    #文章评论数
    comments_count = models.PositiveIntegerField(default=0)
    #文章创建时间
    created= models.DateTimeField(default=timezone.now)
    #文章更新时间
    updated = models.DateTimeField(auto_now=True)

    #内部类 class Meta 用于给model定义元数据
    class Meta:
        ordering = ('-created',)
        db_table = 'tb_article'
        verbose_name='文章管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title
class Comment(models.Model):
    #评论内容
    content = models.TextField()
    #评论的文章
    article = models.ForeignKey(Article,on_delete=models.SET_NULL,null=True)
    #发表评论的用户
    user = models.ForeignKey('users.User',on_delete=models.SET_NULL,null=True)
    #评论发布时间
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.article.title
    class Meta:
        db_table = 'tb_comment'
        verbose_name = '评论管理'
        verbose_name_plural = verbose_name


