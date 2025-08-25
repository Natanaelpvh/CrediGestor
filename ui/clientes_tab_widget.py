# ui/clientes_tab_widget.py
"""
Módulo que define o ClientesTabWidget.

Este widget encapsula toda a funcionalidade da aba de gerenciamento de clientes,
incluindo a interface do usuário (tabela, botões, campo de busca) e as operações
de CRUD (Criar, Ler, Atualizar, Deletar).
"""
from typing import List, Optional
import re
from datetime import datetime
from urllib.parse import quote

from PyQt6.QtCore import Qt, QTimer, QUrl, QObject, pyqtSignal, QThread
from PyQt6.QtGui import QDesktopServices
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from PyQt6.QtWidgets import (QApplication, QHeaderView, QHBoxLayout, QLabel, QMessageBox,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QLineEdit, QVBoxLayout, QWidget, QMenu)

from models.cliente import Cliente
from services.cliente_service import ClienteService
from .cliente_dialog import ClienteDialog


class ClienteLoaderWorker(QObject):
    """
    Worker que executa a busca de clientes em uma thread separada para não bloquear a UI.
    """
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, cliente_service: ClienteService, search_term: str, limit: int, offset: int):
        """
        Inicializa o worker.

        Args:
            cliente_service (ClienteService): A instância do serviço para acessar o banco de dados.
            search_term (str): O termo de busca a ser usado na consulta.
            limit (int): O número máximo de registros a serem retornados.
            offset (int): O deslocamento inicial para a paginação.
        """
        super().__init__()
        self.cliente_service = cliente_service
        self.search_term = search_term
        self.limit = limit
        self.offset = offset

    def run(self):
        """
        Executa a consulta ao banco de dados em segundo plano.
        Emite o sinal `finished` com a lista de clientes em caso de sucesso,
        ou o sinal `error` com uma mensagem de erro em caso de falha.
        """
        try:
            if self.search_term:
                clientes = self.cliente_service.search_clientes(
                    search_term=self.search_term,
                    limit=self.limit,
                    offset=self.offset
                )
            else:
                clientes = self.cliente_service.get_all_clientes(
                    limit=self.limit,
                    offset=self.offset
                )
            self.finished.emit(clientes or [])
        except Exception as e:
            self.error.emit(f"Não foi possível carregar os clientes: {e}")

class ClientesTabWidget(QWidget):
    """
    Um widget de aba para gerenciar clientes (CRUD e busca).
    Encapsula toda a lógica e UI da aba de clientes.
    """
    # Constantes para perfis de usuário para melhorar a legibilidade e manutenção
    ADMIN_ROLE = "admin"
    MANAGER_ROLE = "gerente"

    # Constantes para as colunas da tabela, movidas de MainWindow
    class _ClienteTableCols:
        """Define constantes para os índices e cabeçalhos das colunas da tabela."""
        ID, NOME, CPF, TELEFONE, EMAIL, ENDERECO, OUTRAS_INFORMACOES = range(7)
        HEADERS = ["ID", "Nome", "CPF", "Telefone", "Email", "Endereço", "Outras Informações"]
    def __init__(self, cliente_service: ClienteService, db_session: Session, user_role: str, parent: Optional[QWidget] = None):
        """
        Inicializa o widget da aba de clientes.

        Este construtor configura a UI, as permissões do usuário e inicia
        o carregamento inicial dos dados.

        Args:
            cliente_service (ClienteService): Instância do serviço para operações de cliente.
            db_session (Session): Sessão do SQLAlchemy para controle de transação em caso de erros.
            user_role (str): Perfil do usuário logado (ex: "admin", "gerente", "vendedor").
            parent (Optional[QWidget]): O widget pai.
        """
        super().__init__(parent)
        self.cliente_service = cliente_service
        self.user_role = user_role
        self.db_session = db_session
        self.page_size = 20
        self.current_offset = 0
        self._is_loading = False
        self._has_more_data_to_load = True
        self._setup_search_timer()
        self.worker = None
        self.loading_thread = None
        self._setup_ui()
        self._trigger_data_load()  # Carga inicial de dados

    def _setup_search_timer(self):
        """Configura o timer para debouncing da busca."""
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(500)  # Atraso de 500ms
        self.search_timer.timeout.connect(self._trigger_data_load)
    def _setup_ui(self):
        """Configura a interface da aba de clientes."""
        layout = QVBoxLayout(self)

        # Layout de controle (busca e botões)
        control_layout = QHBoxLayout()
        self.search_label = QLabel("Buscar por Nome ou CPF:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite para buscar...")
        
        self.add_button = QPushButton("Novo Cliente")
        self.edit_button = QPushButton("Editar Cliente")
        self.delete_button = QPushButton("Excluir Cliente")

        control_layout.addWidget(self.search_label)
        control_layout.addWidget(self.search_input)
        control_layout.addStretch()
        control_layout.addWidget(self.add_button)
        control_layout.addWidget(self.edit_button)
        control_layout.addWidget(self.delete_button)
        layout.addLayout(control_layout)

        # Tabela de clientes
        self.table = QTableWidget()
        self.table.setColumnCount(len(self._ClienteTableCols.HEADERS))
        self.table.setHorizontalHeaderLabels(self._ClienteTableCols.HEADERS)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(self._ClienteTableCols.NOME, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Indicador de carregamento
        self.loading_label = QLabel("Carregando mais clientes...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.hide() # Oculto por padrão

        layout.addWidget(self.table)
        layout.addWidget(self.loading_label)

        self._connect_signals_and_permissions()

    def _connect_signals_and_permissions(self):
        """Conecta os sinais dos widgets e ajusta permissões com base no perfil do usuário."""
        self.search_input.textChanged.connect(self.search_timer.start)
        self.table.verticalScrollBar().valueChanged.connect(self._check_scroll_position)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        # Conecta os sinais e ajusta a UI com base na permissão do usuário
        self.add_button.clicked.connect(self.add_cliente)
        if self.user_role in [self.ADMIN_ROLE, self.MANAGER_ROLE]:
            self.edit_button.clicked.connect(self.edit_cliente)
            self.delete_button.clicked.connect(self.delete_cliente)
            self.table.itemDoubleClicked.connect(self.edit_cliente)
        else:
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)

    def _get_saudacao(self) -> str:
        """Retorna a saudação apropriada baseada na hora atual."""
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            return "Bom dia"
        elif 12 <= current_hour < 18:
            return "Boa tarde"
        else:
            return "Boa noite"

    def _show_context_menu(self, position):
        """
        Mostra um menu de contexto quando o usuário clica com o botão direito
        na coluna de telefone, oferecendo opções para copiar o número ou
        iniciar uma conversa no WhatsApp.
        """
        item = self.table.itemAt(position)
        if not item or item.column() != self._ClienteTableCols.TELEFONE:
            return

        row = item.row()
        nome = self.table.item(row, self._ClienteTableCols.NOME).text()
        telefone = self.table.item(row, self._ClienteTableCols.TELEFONE).text()

        menu = QMenu(self)
        copy_action = menu.addAction("Copiar número")
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(telefone))

        whatsapp_action = menu.addAction("Chamar no WhatsApp")
        whatsapp_action.triggered.connect(lambda: self._open_whatsapp(telefone, nome))

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _open_whatsapp(self, telefone: str, nome: str):
        """Abre uma conversa no WhatsApp com uma saudação."""
        telefone_limpo = re.sub(r'\D', '', telefone)
        mensagem = f"Olá {self._get_saudacao()}, {nome}!"
        url = f"https://wa.me/{telefone_limpo}?text={quote(mensagem)}"
        QDesktopServices.openUrl(QUrl(url))

    def _append_clientes_to_table(self, clientes: List[Cliente]):
        """Adiciona uma lista de clientes ao final da tabela."""
        start_row = self.table.rowCount()
        self.table.setRowCount(start_row + len(clientes))
        for row_offset, cliente in enumerate(clientes):
            row = start_row + row_offset
            self.table.setItem(row, self._ClienteTableCols.ID, QTableWidgetItem(str(cliente.id)))
            self.table.setItem(row, self._ClienteTableCols.NOME, QTableWidgetItem(cliente.nome))
            self.table.setItem(row, self._ClienteTableCols.CPF, QTableWidgetItem(cliente.cpf))
            self.table.setItem(row, self._ClienteTableCols.TELEFONE, QTableWidgetItem(cliente.telefone))
            self.table.setItem(row, self._ClienteTableCols.EMAIL, QTableWidgetItem(cliente.email))
            self.table.setItem(row, self._ClienteTableCols.ENDERECO, QTableWidgetItem(cliente.endereco))
            self.table.setItem(row, self._ClienteTableCols.OUTRAS_INFORMACOES, QTableWidgetItem(cliente.outras_informacoes or ""))

    def _trigger_data_load(self):
        """
        Reseta o estado da tabela e inicia o carregamento dos dados de forma paginada.
        Este método é o ponto de entrada para qualquer atualização da tabela (carga inicial,
        busca, ou refresh após uma operação de CRUD).
        """
        self.current_offset = 0
        self._has_more_data_to_load = True
        self.table.setRowCount(0)
        self._load_more_clientes()

    def _load_more_clientes(self):
        """Inicia o carregamento de mais clientes em uma thread separada."""
        if self._is_loading or not self._has_more_data_to_load:
            return

        self._is_loading = True
        self.loading_label.show()

        search_term = self.search_input.text().strip()

        # Configura o worker e a thread
        # O worker e a thread DEVEM ser atributos da instância (self) para evitar
        # que sejam destruídos prematuramente pelo garbage collector.
        self.loading_thread = QThread()
        self.worker = ClienteLoaderWorker(
            cliente_service=self.cliente_service,
            search_term=search_term,
            limit=self.page_size,
            offset=self.current_offset
        )
        self.worker.moveToThread(self.loading_thread)

        # Conecta os sinais para receber os resultados ou erros
        self.loading_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_clientes_loaded)
        self.worker.error.connect(self._on_loading_error)
        
        # Limpeza da thread e do worker após a conclusão
        self.worker.finished.connect(self.loading_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.loading_thread.finished.connect(self.loading_thread.deleteLater)
        # Limpa as referências da instância para evitar acesso a objetos deletados
        self.loading_thread.finished.connect(self._clear_thread_references)

        self.loading_thread.start()

    def _on_clientes_loaded(self, novos_clientes: List[Cliente]):
        """Slot chamado quando o worker termina de carregar os clientes."""
        if novos_clientes:
            self._append_clientes_to_table(novos_clientes)
            self.current_offset += len(novos_clientes)
            if len(novos_clientes) < self.page_size:
                self._has_more_data_to_load = False
        else:
            self._has_more_data_to_load = False
        
        self._is_loading = False
        self.loading_label.hide()

    def _on_loading_error(self, error_message: str):
        """Slot chamado se ocorrer um erro no worker."""
        QMessageBox.critical(self, "Erro de Carregamento", error_message)
        self._is_loading = False
        self.loading_label.hide()
        # Se um erro ocorrer, o sinal 'finished' do worker pode não ser emitido.
        # Portanto, precisamos garantir que a thread seja encerrada para acionar a limpeza.
        if self.loading_thread:
            self.loading_thread.quit()

    def _check_scroll_position(self, value: int):
        """Verifica se o scroll chegou ao fim para carregar mais itens."""
        scrollbar = self.table.verticalScrollBar()
        if value == scrollbar.maximum():
            self._load_more_clientes()

    def add_cliente(self):
        """Abre o diálogo para adicionar um novo cliente."""
        dialog = ClienteDialog(parent=self)
        if dialog.exec():
            try:
                data = dialog.get_data()
                self.cliente_service.create_cliente(**data)
                self._trigger_data_load()
            except IntegrityError:
                self.db_session.rollback()
                QMessageBox.critical(self, "Erro de Integridade", "Não foi possível criar o cliente. Verifique se o CPF já está cadastrado.")
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Erro", f"Não foi possível criar o cliente: {e}")

    def _get_selected_cliente_info(self) -> Optional[tuple[int, str]]:
        """
        Obtém o ID e o nome do cliente da linha selecionada na tabela.
        Mostra um aviso se nenhuma linha for selecionada.
        Retorna (id, nome) ou None.
        """
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione um cliente na tabela.")
            return None
        
        id_item = self.table.item(selected_row, self._ClienteTableCols.ID)
        nome_item = self.table.item(selected_row, self._ClienteTableCols.NOME)

        if not id_item or not nome_item:
            QMessageBox.critical(self, "Erro de Dados", "Não foi possível ler os dados do cliente. Células da tabela estão faltando.")
            return None

        try:
            cliente_id = int(id_item.text())
            cliente_nome = nome_item.text()
            return cliente_id, cliente_nome
        except ValueError:
            QMessageBox.critical(self, "Erro de Dados", f"O ID do cliente na tabela ('{id_item.text()}') não é um número válido.")
            return None

    def edit_cliente(self):
        """Abre o diálogo para editar o cliente selecionado."""
        selected_info = self._get_selected_cliente_info()
        if not selected_info:
            return

        cliente_id, _ = selected_info
        cliente = self.cliente_service.get_cliente_by_id(cliente_id)
        if not cliente:
            QMessageBox.critical(self, "Erro", "Cliente não encontrado no banco de dados. A lista pode estar desatualizada.")
            self._trigger_data_load()
            return

        dialog = ClienteDialog(cliente=cliente, parent=self)
        if dialog.exec():
            try:
                self.cliente_service.update_cliente(cliente_id, **dialog.get_data())
                self._trigger_data_load()
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Erro", f"Não foi possível atualizar o cliente: {e}")

    def delete_cliente(self):
        """Exclui o cliente selecionado."""
        selected_info = self._get_selected_cliente_info()
        if not selected_info:
            return

        cliente_id, cliente_nome = selected_info
        reply = QMessageBox.question(self, "Confirmar Exclusão", f"Você tem certeza que deseja excluir o cliente '{cliente_nome}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.cliente_service.delete_cliente(cliente_id)
            self._trigger_data_load()
        except IntegrityError:
            self.db_session.rollback()
            QMessageBox.critical(self, "Operação Inválida", "Este cliente não pode ser excluído, pois possui um ou mais empréstimos ativos associados.")
        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro inesperado ao excluir o cliente: {e}")

    def _clear_thread_references(self):
        """Limpa as referências ao worker e à thread após a conclusão do trabalho."""
        self.worker = None
        self.loading_thread = None

    def stop_threads(self):
        """
        Garante que o thread de carregamento seja finalizado antes que o widget seja destruído.
        Este método é chamado pelo 'closeEvent' da janela principal para um encerramento seguro.
        """
        if self.loading_thread and self.loading_thread.isRunning():
            self.loading_thread.quit()
            # Espera até 2 segundos para o thread terminar de forma limpa.
            self.loading_thread.wait(2000)

    def refresh_data(self):
        """Método público para recarregar os dados da aba, limpando a busca."""
        self.search_timer.stop()
        # Bloqueia os sinais para evitar que clear() dispare o timer
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        # Dispara o carregamento imediatamente, agora com o campo de busca limpo
        self._trigger_data_load()