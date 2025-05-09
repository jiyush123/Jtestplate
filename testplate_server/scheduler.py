from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from testplate_server.models import CronJob
from django.conf import settings

import requests

# 创建调度器实例
job_defaults = {'max_instances': 5}
scheduler = BackgroundScheduler(jobstores={'default': DjangoJobStore()})
scheduler.configure(job_defaults=job_defaults)

def get_service_url():
    """获取当前服务的URL"""
    try:
        # 从settings中获取服务配置
        host = getattr(settings, 'SERVICE_HOST', '127.0.0.1')
        port = getattr(settings, 'SERVICE_PORT', '8000')
        return f'http://{host}:{port}'
    except Exception as e:
        print(f"获取服务URL失败: {str(e)}")
        return 'http://127.0.0.1:8000'  # 默认值

def update_next_time(schedule):
    cron_data = schedule.split(' ')
    cron = {
        "second": cron_data[0],
        "minute": cron_data[1],
        "hour": cron_data[2],
        "day": cron_data[3],
        "month": cron_data[4],
        "day_of_week": "*",
        "year": cron_data[6]
    }
    trigger = CronTrigger(**cron)
    next_run_time = trigger.get_next_fire_time(None, datetime.now())
    aware_datetime = datetime.fromisoformat(str(next_run_time))
    return aware_datetime.replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')

def run_test(task_id, case_ids, schedule):
    # 保存上次执行时间
    last_run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    CronJob.objects.filter(pk=task_id).update(last_run_time=last_run_time)
    protocol = CronJob.objects.filter(pk=task_id).values_list('env__protocol', flat=True).first()
    if protocol == 1:
        protocol = 'http'
    else:
        protocol = 'https'
    host = CronJob.objects.filter(pk=task_id).values_list('env__host', flat=True).first()
    port = CronJob.objects.filter(pk=task_id).values_list('env__port', flat=True).first()
    # 更新下次执行时间
    next_run_time = update_next_time(schedule)
    CronJob.objects.filter(pk=task_id).update(next_run_time=next_run_time)
    # 执行用例
    service_url = get_service_url()
    url = f'{service_url}/apicase/run/'
    host = 'http://' + host + ':' + str(port)
    headers = {'Authorization': 'super_admin_request'}
    data = {'ids': case_ids, 'created_user': '超级管理员', 'host': host}
    try:
        requests.post(url=url, headers=headers, data=data)
    except Exception as e:
        print(f'任务异常: {str(e)}')

def add_job_to_scheduler(task_id, name, case_ids, schedule):
    try:
        cron_data = schedule.split(' ')
        cron = {
            "second": cron_data[0],
            "minute": cron_data[1],
            "hour": cron_data[2],
            "day": cron_data[3],
            "month": cron_data[4],
            "day_of_week": "*",
            "year": cron_data[6]
        }
        trigger = CronTrigger(**cron)
        
        scheduler.add_job(
            func=run_test,
            args=(task_id, case_ids, schedule),
            trigger=trigger,
            id=str(task_id),
            name=name,
            replace_existing=True
        )
    except Exception as e:
        print(f"添加任务失败: {str(e)}")

def remove_job_from_scheduler(task_id):
    try:
        scheduler.remove_job(str(task_id))
    except Exception as e:
        print(f"删除任务失败: {str(e)}")

def initialize_scheduler():
    """初始化调度器并加载所有活动任务"""
    try:
        if not scheduler.running:
            scheduler.start()
            
        # 加载所有活动任务
        for task in CronJob.objects.filter(is_active=True).all():
            print(f'加载任务: {task.name}')
            add_job_to_scheduler(task.id, task.name, task.case_ids, task.schedule)
    except Exception as e:
        print(f"初始化调度器失败: {str(e)}")

def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown() 