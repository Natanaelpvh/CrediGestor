# ui/main_window.py
"""
Módulo que define a MainWindow, a janela principal da aplicação Gestor System.

Esta classe é responsável por:
- Montar a interface principal com abas (Dashboard, Clientes, Usuários, Empréstimos).
- Inicializar e coordenar os serviços de negócio (ClienteService, UsuarioService, EmprestimoService).
- Lidar com todas as interações do usuário, como cliques em botões e buscas.
- Orquestrar a abertura de diálogos para criação, edição e visualização de dados.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QMessageBox, QTabWidget, QFileDialog
)
from sqlalchemy.orm import Session
from services.emprestimo_service import EmprestimoService
from services.cliente_service import ClienteService
from services.usuario_service import UsuarioService
from .emprestimo_dialog import EmprestimoDialog
from models.usuario import Usuario
from .taxas_emprestimo_dialog import TaxaJurosDialog
from .clientes_tab_widget import ClientesTabWidget
from .usuarios_tab_widget import UsuariosTabWidget
from .emprestimos_tab_widget import EmprestimosTabWidget
from .dashboard_static import DashboardStatic
from backup_utils import BackupManager

class MainWindow(QMainWindow):
    """
    Janela principal da aplicação.
    """
    # --- Constantes para Colunas das Tabelas ---
    # Usar constantes em vez de números mágicos torna o código mais legível e fácil de manter.
    def __init__(self, usuario_logado: Usuario, db_session: Session):
        """
        Inicializa a janela principal da aplicação.

        Este construtor configura a janela, inicializa os serviços de negócio
        (Cliente, Usuário, Empréstimo) com a sessão do banco de dados fornecida,
        e chama a configuração da UI. Também adiciona menus específicos para
        usuários administradores.

        Args:
            usuario_logado (Usuario): O objeto do usuário que fez login.
            db_session (Session): A sessão do SQLAlchemy para interagir com o banco de dados.
        """
        super().__init__()
        self.usuario_logado = usuario_logado
        self.db_session = db_session
        self.setWindowTitle(f"Gestor System - Usuário: {self.usuario_logado.nome}")
        self.setGeometry(100, 100, 1200, 700)

        # Inicializa os serviços com a sessão do banco de dados
        self.cliente_service = ClienteService(self.db_session)
        self.usuario_service = UsuarioService(self.db_session)
        self.emprestimo_service = EmprestimoService(self.db_session)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.setup_ui()

        if hasattr(self.usuario_logado, 'role') and getattr(self.usuario_logado.role, 'value', None) == 'admin':
            self.menu_admin = self.menuBar().addMenu("Administração")
            self.menu_admin.addAction("Taxas de Juros", self.abrir_taxa_juros)
            restore_action = self.menu_admin.addAction("Restaurar Backup...")
            restore_action.triggered.connect(self.iniciar_restauracao)

    def setup_ui(self):
        """Cria e organiza os widgets da interface usando abas."""
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Aba de Dashboard
        self.dashboard_tab = DashboardStatic(
            usuario_logado=self.usuario_logado,
            emprestimo_service=self.emprestimo_service,
            cliente_service=self.cliente_service,
            on_novo_emprestimo=self._handle_novo_emprestimo_shortcut,
            on_relatorios=self._handle_relatorios_shortcut,
            on_exportar=self._handle_exportar_shortcut,
            parent=self
        )
        self.tabs.addTab(self.dashboard_tab, "Dashboard")

        # Aba de Usuários (somente para admins)
        if self.usuario_logado.role.value == 'admin':
            self.usuarios_tab = UsuariosTabWidget(self.usuario_service, self.usuario_logado, self.db_session, parent=self)
            self.tabs.addTab(self.usuarios_tab, "Usuários")

        # Aba de Clientes
        self.clientes_tab = ClientesTabWidget(self.cliente_service, self.db_session, parent=self)
        self.tabs.addTab(self.clientes_tab, "Clientes")

        # Aba de Empréstimos (somente para admins)
        if self.usuario_logado.role.value == 'admin':
            self.emprestimos_tab = EmprestimosTabWidget(
                usuario_logado=self.usuario_logado,
                emprestimo_service=self.emprestimo_service,
                cliente_service=self.cliente_service,
                usuario_service=self.usuario_service,
                parent=self
            )
            self.tabs.addTab(self.emprestimos_tab, "Empréstimos")

        self.tabs.currentChanged.connect(self.on_tab_changed)

    def _handle_novo_emprestimo_shortcut(self):
        """Abre o diálogo de novo empréstimo a partir do atalho do dashboard."""
        dialog = EmprestimoDialog(self.cliente_service, self.emprestimo_service, parent=self)
        if dialog.exec():
            # Recarrega os dados do dashboard para refletir o novo empréstimo
            self.dashboard_tab.refresh()

    def _handle_relatorios_shortcut(self):
        """Placeholder para a funcionalidade de relatórios."""
        QMessageBox.information(self, "Funcionalidade Futura", "A área de relatórios será implementada em breve.")

    def _handle_exportar_shortcut(self):
        """Placeholder para a funcionalidade de exportação."""
        QMessageBox.information(self, "Funcionalidade Futura", "A funcionalidade para exportar dados será implementada em breve.")

    def abrir_taxa_juros(self):
        """Abre o diálogo para configurar as taxas de juros globais."""
        dialog = TaxaJurosDialog(self.db_session, self)
        dialog.exec()

    def iniciar_restauracao(self):
        """
        Inicia o processo de restauração de um backup, com múltiplas confirmações
        para garantir a segurança da operação.
        """
        # 1. Abre o diálogo para selecionar o arquivo de backup
        backup_file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione o Arquivo de Backup para Restaurar",
            "",  # Diretório inicial
            "Arquivos de Backup (*.sql *.db);;Todos os Arquivos (*)"
        )

        # 2. Se o usuário cancelou, sai do método
        if not backup_file_path:
            return

        # 3. Mostra um aviso crítico sobre a perda de dados
        reply = QMessageBox.warning(
            self,
            "ATENÇÃO: Operação Destrutiva",
            "Esta ação irá apagar TODOS os dados atuais e substituí-los pelo backup.\n\n"
            "Esta operação não pode ser desfeita.\n\n"
            "Deseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Botão padrão
        )

        # 4. Se o usuário não confirmar, sai do método
        if reply == QMessageBox.StandardButton.No:
            return

        # 5. Se o usuário confirmou, executa a restauração
        try:
            backup_manager = BackupManager()
            success, message = backup_manager.perform_restore(backup_file_path)
            if success:
                QMessageBox.information(self, "Restauração Concluída", message)
            else:
                QMessageBox.critical(self, "Falha na Restauração", message)
        except Exception as e:
            QMessageBox.critical(self, "Erro na Restauração", f"Ocorreu um erro inesperado: {e}")

    def on_tab_changed(self, index):
        """
        Slot executado quando o usuário troca de aba.

        Usado para recarregar dados dinamicamente, como a lista de clientes na aba
        de empréstimos ou os dados do dashboard.

        Args:
            index (int): O índice da nova aba selecionada.
        """
        tab_text = self.tabs.tabText(index)
        if tab_text == "Dashboard":
            self.dashboard_tab.refresh()
        elif tab_text == "Clientes":
            self.clientes_tab.refresh_data()
        elif tab_text == "Usuários" and self.usuario_logado.role.value == 'admin':
            self.usuarios_tab.refresh_data()
        elif tab_text == "Empréstimos" and self.usuario_logado.role.value == 'admin':
            self.emprestimos_tab.refresh_data()

    def closeEvent(self, event) -> None:
        """
        Sobrescreve o evento de fechamento da janela para perguntar ao usuário
        se ele deseja realizar um backup antes de sair.

        Args:
            event (QCloseEvent): O evento de fechamento.
        """
        reply = QMessageBox.question(
            self,
            "Confirmar Saída",
            "Deseja fazer um backup do banco de dados antes de sair?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel  # Botão padrão
        )

        if reply == QMessageBox.StandardButton.Cancel:
            event.ignore()  # Impede que a janela feche
        elif reply == QMessageBox.StandardButton.No:
            event.accept()  # Permite que a janela feche
        elif reply == QMessageBox.StandardButton.Yes:
            # Abre um diálogo para o usuário escolher a pasta de backup
            backup_dir = QFileDialog.getExistingDirectory(self, "Selecione a Pasta para Salvar o Backup")
            
            if backup_dir:
                try:
                    backup_manager = BackupManager()
                    success, message = backup_manager.perform_backup(backup_dir)
                    if success:
                        QMessageBox.information(self, "Backup Concluído", message)
                    else:
                        QMessageBox.critical(self, "Falha no Backup", message)
                except Exception as e:
                    QMessageBox.critical(self, "Erro no Backup", f"Ocorreu um erro inesperado: {e}")
                finally:
                    event.accept()  # Fecha a aplicação após a tentativa de backup
            else:
                # Se o usuário cancelar a seleção da pasta, ignora o fechamento
                event.ignore()