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

# 创建Pydantic警告过滤器
class PydanticWarningFilter(logging.Filter):
    def filter(self, record):
        # 过滤掉特定的Pydantic废弃警告
        if "PydanticDeprecatedSince211" in record.getMessage() and \
           "model_fields" in record.getMessage() and \
           "litellm_core_utils" in record.pathname:
            return False
        return True

# 配置基础日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    stream=sys.stdout,
)

# 为特定logger添加过滤器
deprecated_filter = PydanticWarningFilter()
logging.getLogger().addFilter(deprecated_filter)
# 为litellm相关的logger添加过滤器
logging.getLogger('litellm').addFilter(deprecated_filter)

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