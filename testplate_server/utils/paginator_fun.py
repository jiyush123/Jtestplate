from django.core.paginator import Paginator
from django.db.models import Count


def paginator_fun(table_obj, filtered, order_by, page, size):
    """
    分页
    :param table_obj:数据表对象
    :param filtered:查询条件
    :param order_by:根据什么字段排序
    :param page:
    :param size:
    :return:
    """
    # 使用Django的Paginator进行分页
    # 通过annotate新生成的count字段，值为聚合函数得到的值
    query_obj = table_obj.objects.filter(**filtered).annotate(count=Count('id')).order_by(order_by)
    paginator = Paginator(query_obj, size)  # 使用Paginator
    queryset = paginator.get_page(page).object_list
    total = paginator.count
    return queryset, total
