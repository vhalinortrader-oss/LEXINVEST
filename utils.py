try:
    from .calculations import *
except ImportError:  # pragma: no cover - suporte para execução direta
    from calculations import *

try:
    from .charts import *
except ImportError:  # pragma: no cover - charts é opcional / pode não existir
    try:
        from charts import *
    except ImportError:
        pass
