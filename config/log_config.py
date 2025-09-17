import logging
import structlog
import sys
from config import get_config
# 导入coloredlogs，项目已包含此依赖
import coloredlogs

config = get_config()

# 配置coloredlogs - 设置不同日志级别的颜色
coloredlogs.DEFAULT_LEVEL_STYLES = {
    'debug': {'color': 'blue', 'faint': True},
    'info': {'color': 'green'},
    'warning': {'color': 'yellow', 'bold': True},
    'error': {'color': 'red', 'bold': True},
    'critical': {'color': 'red', 'bold': True, 'background': 'white'}
}

# 配置coloredlogs - 自定义日志格式
coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
coloredlogs.DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 配置基础日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    stream=sys.stdout,
)

# 应用coloredlogs配置到根logger
coloredlogs.install(level=getattr(logging, config.LOG_LEVEL.upper()))

# 配置structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.render_to_log_kwargs,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

def get_logger(name):
    return structlog.get_logger(name)