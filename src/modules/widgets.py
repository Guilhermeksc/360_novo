# modules/widgets.py

# Utilidades
from src.modules.utils.icon_loader import load_icons

# Importações de views
# from src.modules.pca.pca import PCAWidget
from src.modules.inicio.inicio import InicioWidget
# from src.modules.pncp.pncp import PNCPWidget
# from src.modules.planejamento_novo.antigo_planejamento_button import PlanejamentoWidget
from src.modules.dispensa_eletronica.views import DispensaEletronicaWidget
from src.modules.planejamento.views import LicitacaoWidget
from src.modules.atas_novo.views import GerarAtasView
# from src.modules.atas.classe_atas import AtasWidget
from src.modules.contratos.views import ContratosView

# Importações de models
from src.modules.dispensa_eletronica.models import DispensaEletronicaModel
from src.modules.planejamento.models import LicitacaoModel
from src.modules.atas_novo.models import GerarAtasModel
# from src.modules.pca.models import PCAModel  # Exemplo para PCA
# from src.modules.atas.models import AtasModel  # Exemplo para Atas
from src.modules.contratos.models import ContratosModel 

# Importações de controllers
from src.modules.dispensa_eletronica.controller import DispensaEletronicaController
from src.modules.planejamento.controller import LicitacaoController
from src.modules.dashboard.dashboard_controle import DashboardWidget
from src.modules.atas_novo.controller import GerarAtasController
from src.modules.contratos.controller import ContratosController

__all__ = [
    # Views
    # "PCAWidget",
    "InicioWidget",
    # "PNCPWidget",
    "LicitacaoWidget",
    "DispensaEletronicaWidget",
    "DashboardWidget",
    "GerarAtasView",
    # "AtasWidget",
    "ContratosView",
    
    # Models
    "DispensaEletronicaModel",
    "LicitacaoModel",
    "GerarAtasModel",
    "ContratosModel",
    # "PCAModel",
    # "AtasModel",

    # Controllers
    "DispensaEletronicaController",
    "LicitacaoController",
    "GerarAtasController",
    "ContratosController",

    # Utils
    "load_icons"
]