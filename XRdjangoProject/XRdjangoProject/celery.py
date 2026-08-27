# myproject/myproject/celery.py (或 XRdjangoProject/XRdjangoProject/celery.py)
import os
from celery import Celery

# 设置Django的settings模块环境变量，以便Celery可以找到它
# 将 'myproject.settings' 替换为您的实际项目settings路径
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'XRdjangoProject.settings') # 根据您的项目名称修改

# 创建Celery应用实例
# 将 'myproject' 替换为您的项目名称
app = Celery('XRdjangoProject') # 根据您的项目名称修改

# 使用Django的settings文件配置Celery。
# namespace='CELERY'意味着所有Celery相关的配置键在settings.py中都应以CELERY_为前缀。
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动从所有已注册的Django app中加载任务模块（tasks.py）。
app.autodiscover_tasks()

# 可选的调试任务，用于测试Celery worker是否正常运行
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')