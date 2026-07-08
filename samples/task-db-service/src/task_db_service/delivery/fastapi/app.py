from task_db_service.delivery.fastapi.factory import FastAPIFactory
from task_db_service.ioc.container import get_container

container = get_container()
app = container.resolve(FastAPIFactory)()
