"""FastAPI 依赖注入"""

from ..config import get_config_manager
from ..llm.manager import get_llm_manager
from ..database.manager import get_db_manager
from ..database.history import get_history_manager
from ..database.templates import get_template_manager as get_db_template_manager


def get_config():
    return get_config_manager()


def get_llm():
    return get_llm_manager()


def get_db():
    return get_db_manager()


def get_history():
    return get_history_manager()


def get_template_manager():
    return get_db_template_manager()
