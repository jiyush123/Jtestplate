from django.apps import AppConfig


class TestplateServerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'testplate_server'

    def ready(self):
        try:
            from .scheduler import initialize_scheduler
            initialize_scheduler()
        except Exception as e:
            print(f"初始化调度器失败: {str(e)}")
