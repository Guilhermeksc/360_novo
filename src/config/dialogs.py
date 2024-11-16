# config/dialogs.py

from src.config.config_database import ConfigurarDatabaseDialog
from src.config.config_responsaveis import AgentesResponsaveisWidget
from src.config.config_om import OrganizacoesDialog
from src.config.config_template import TemplatesDialog

__all__ = [
    "ConfigurarDatabaseDialog",
    "AgentesResponsaveisWidget",
    "OrganizacoesDialog",
    "TemplatesDialog",
]
