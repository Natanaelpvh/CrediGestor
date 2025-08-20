# services/emprestimo_service.py
"""
Módulo de Serviço de Empréstimo.

Este módulo define a classe `EmprestimoService`, que encapsula toda a lógica de
negócio para as operações relacionadas a empréstimos e parcelas. Isso inclui
cálculos de juros, criação, atualização, exclusão de empréstimos, e geração
de relatórios e indicadores para o dashboard.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.cliente import Cliente
from models.emprestimo import Emprestimo, TipoJuros
from models.parcela import Parcela
from models.taxas_emprestimo import TaxaJuros


class EmprestimoService:
    """
    Serviço para gerenciar as operações de negócio de Empréstimos e Parcelas.

    Fornece uma interface de alto nível para interagir com os modelos de
    Emprestimo e Parcela, abstraindo a complexidade dos cálculos financeiros
    e das interações com o banco de dados.
    """
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_taxas_config(self) -> Optional[TaxaJuros]:
        """
        Busca a configuração global de taxas de juros do sistema.

        Returns:
            Optional[TaxaJuros]: O objeto com as taxas de juros, ou None se não configurado.
        """
        return self.db.query(TaxaJuros).first()

    def _calcular_e_criar_parcelas(self, emprestimo: Emprestimo):
        """
        Calcula o valor das parcelas e as cria no banco de dados para um dado empréstimo.
        Esta é uma função auxiliar para evitar duplicação de código.
        """
        valor_principal = emprestimo.valor
        num_parcelas = emprestimo.numero_parcelas

        if emprestimo.tipo_juros == TipoJuros.SIMPLES:
            taxa_juros = emprestimo.taxa_juros_simples / Decimal(100)
            valor_total_juros = valor_principal * taxa_juros * Decimal(num_parcelas)
            valor_parcela = (valor_principal + valor_total_juros) / Decimal(num_parcelas)
        else:  # Juros Composto
            taxa_juros_mensal = emprestimo.taxa_juros_composto / Decimal(100)
            if taxa_juros_mensal == 0:
                valor_parcela = valor_principal / Decimal(num_parcelas)
            else:
                fator = (1 + taxa_juros_mensal) ** num_parcelas
                valor_parcela = valor_principal * (taxa_juros_mensal * fator) / (fator - 1)

        valor_parcela = round(valor_parcela, 2)

        for i in range(1, num_parcelas + 1):
            data_vencimento = emprestimo.data_inicio + timedelta(days=30 * i)
            parcela = Parcela(emprestimo_id=emprestimo.id, numero=i, valor=valor_parcela,
                              data_vencimento=data_vencimento, pago=False)
            self.db.add(parcela)

    def create_emprestimo_com_parcelas(self, data: Dict[str, Any]):
        """Cria um novo empréstimo e suas respectivas parcelas."""
        taxas = self.get_taxas_config()
        if not taxas:
            raise ValueError("As taxas de juros não estão configuradas no sistema.")

        novo_emprestimo = Emprestimo(
            cliente_id=data['cliente_id'],
            valor=data['valor'],
            numero_parcelas=data['numero_parcelas'],
            data_inicio=data['data_inicio'],
            tipo_juros=data['tipo_juros'],
            taxa_juros_simples=taxas.taxa_juros_simples,
            taxa_juros_composto=taxas.taxa_juros_composto,
            taxa_juros_mora=taxas.taxa_juros_mora
        )
        self.db.add(novo_emprestimo)
        self.db.flush()  # Garante que o ID do empréstimo seja gerado

        # Chama o método auxiliar para calcular e criar as parcelas
        self._calcular_e_criar_parcelas(novo_emprestimo)

        self.db.commit()

   
    def get_proximos_vencimentos_detalhados(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca as próximas parcelas não pagas, incluindo detalhes do empréstimo e cliente.
        """
        today = date.today()
        vencimentos = (
            self.db.query(
                Cliente.nome.label('cliente_nome'),
                Emprestimo.id.label('emprestimo_id'),
                Parcela.numero.label('parcela_numero'),
                Parcela.data_vencimento
            )
            .join(Emprestimo, Parcela.emprestimo_id == Emprestimo.id)
            .join(Cliente, Emprestimo.cliente_id == Cliente.id)
            .filter(Parcela.pago == False)
            .filter(Parcela.data_vencimento >= today)
            .order_by(Parcela.data_vencimento.asc())
            .limit(limit)
            .all()
        )
        return [
            {'cliente_nome': v.cliente_nome, 'emprestimo_id': v.emprestimo_id,
             'parcela_numero': v.parcela_numero, 'data_vencimento': v.data_vencimento}
            for v in vencimentos
        ]

    def get_dashboard_indicators(self) -> Dict[str, Any]:
        """Busca os principais indicadores para o dashboard em uma única chamada."""
        today = date.today()

        # Empréstimos com pelo menos uma parcela não paga
        emprestimos_ativos = (
            self.db.query(func.count(func.distinct(Emprestimo.id)))
            .join(Parcela)
            .filter(Parcela.pago == False)
            .scalar() or 0
        )

        # Parcelas não pagas com vencimento no passado
        parcelas_atrasadas = (
            self.db.query(func.count(Parcela.id))
            .filter(Parcela.pago == False, Parcela.data_vencimento < today)
            .scalar() or 0
        )

        # Valor total a receber (soma de todas as parcelas não pagas)
        a_receber = self.db.query(func.sum(Parcela.valor)).filter(Parcela.pago == False).scalar() or Decimal('0.0')

        return {
            "emprestimos_ativos": emprestimos_ativos,
            "valor_total_emprestado": self.db.query(func.sum(Emprestimo.valor)).scalar() or Decimal('0.0'),
            "parcelas_atrasadas": parcelas_atrasadas,
            "a_receber": a_receber,
        }

    def get_financial_summary(self) -> Dict[str, Decimal]:
        """Calcula um resumo financeiro geral."""
        total_emprestado = self.db.query(func.sum(Emprestimo.valor)).scalar() or Decimal('0.0')
        total_recebido = self.db.query(func.sum(Parcela.valor)).filter(Parcela.pago == True).scalar() or Decimal('0.0')
        total_a_receber = self.db.query(func.sum(Parcela.valor)).filter(Parcela.pago == False).scalar() or Decimal('0.0')
        
        # Juros futuros é uma estimativa baseada no que falta receber vs o principal
        total_principal_a_receber = self.db.query(func.sum(Emprestimo.valor / Emprestimo.numero_parcelas)).join(Parcela).filter(Parcela.pago == False).scalar() or Decimal('0.0')
        juros_futuros = total_a_receber - total_principal_a_receber

        return {
            'total_emprestado': total_emprestado,
            'total_recebido': total_recebido,
            'total_a_receber': total_a_receber,
            'juros_futuros': max(juros_futuros, Decimal('0.0'))
        }

    def get_monthly_payment_summary(self) -> Dict[str, Decimal]:
        """Calcula um resumo de pagamentos para o mês corrente."""
        today = date.today()
        start_of_month = today.replace(day=1)
        
        pago_mes = self.db.query(func.sum(Parcela.valor)).filter(
            Parcela.pago == True,
            func.strftime('%Y-%m', Parcela.data_pagamento) == start_of_month.strftime('%Y-%m')
        ).scalar() or Decimal('0.0')

        pendente_mes = self.db.query(func.sum(Parcela.valor)).filter(
            Parcela.pago == False,
            func.strftime('%Y-%m', Parcela.data_vencimento) == start_of_month.strftime('%Y-%m')
        ).scalar() or Decimal('0.0')

        return {'pago_mes': pago_mes, 'pendente_mes': pendente_mes}

    # Adicione aqui os outros métodos que seu sistema precisa, como:
    def get_emprestimos_by_cliente_id(self, cliente_id: int) -> List[Emprestimo]:
        return self.db.query(Emprestimo).filter(Emprestimo.cliente_id == cliente_id).all()

    def get_parcelas_by_emprestimo_id(self, emprestimo_id: int) -> List[Parcela]:
        return self.db.query(Parcela).filter(Parcela.emprestimo_id == emprestimo_id).order_by(Parcela.numero).all()

    def get_emprestimo_by_id(self, emprestimo_id: int) -> Optional[Emprestimo]:
        return self.db.query(Emprestimo).get(emprestimo_id)

    def get_parcela_by_id(self, parcela_id: int) -> Optional[Parcela]:
        return self.db.query(Parcela).get(parcela_id)

    def registrar_pagamento_parcela(self, parcela_id: int) -> Optional[Parcela]:
        parcela = self.get_parcela_by_id(parcela_id)
        if parcela and not parcela.pago:
            parcela.pago = True
            parcela.data_pagamento = date.today()
            self.db.commit()
            return parcela
        return None

    def update_valor_parcela(self, parcela_id: int, novo_valor: Decimal):
        parcela = self.get_parcela_by_id(parcela_id)
        if parcela:
            parcela.valor = novo_valor
            self.db.commit()

    def delete_emprestimo(self, emprestimo_id: int):
        emprestimo = self.get_emprestimo_by_id(emprestimo_id)
        if emprestimo:
            self.db.query(Parcela).filter(Parcela.emprestimo_id == emprestimo_id).delete()
            self.db.delete(emprestimo)
            self.db.commit()

    def gerar_relatorio_html_emprestimo(self, emprestimo_id: int) -> str:
        """
        Gera uma string HTML contendo os detalhes de um empréstimo e suas parcelas.

        Args:
            emprestimo_id (int): O ID do empréstimo para o qual gerar o relatório.

        Returns:
            str: Uma string HTML formatada com os detalhes do relatório.
        """
        emprestimo = self.get_emprestimo_by_id(emprestimo_id)
        if not emprestimo:
            return ""

        cliente = emprestimo.cliente
        parcelas = sorted(emprestimo.parcelas, key=lambda p: p.numero)

        html = f"""
        <html><head><style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #2c3e50; }} h2 {{ color: #34495e; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }} .pago {{ color: green; font-weight: bold; }}
            .pendente {{ color: red; font-weight: bold; }} .resumo-item {{ margin-bottom: 10px; }}
            .resumo-label {{ font-weight: bold; }}
        </style></head><body>
            <h1>Relatório de Empréstimo</h1><h2>Detalhes do Cliente</h2>
            <div class="resumo-item"><span class="resumo-label">Nome:</span> {cliente.nome}</div>
            <div class="resumo-item"><span class="resumo-label">CPF:</span> {cliente.cpf}</div>
            <h2>Detalhes do Empréstimo</h2>
            <div class="resumo-item"><span class="resumo-label">ID:</span> {emprestimo.id}</div>
            <div class="resumo-item"><span class="resumo-label">Valor:</span> R$ {emprestimo.valor:,.2f}</div>
            <div class="resumo-item"><span class="resumo-label">Parcelas:</span> {emprestimo.numero_parcelas}</div>
            <div class="resumo-item"><span class="resumo-label">Tipo de Juros:</span> {emprestimo.tipo_juros.value.capitalize()}</div>
            <h2>Parcelas</h2><table><tr><th>Nº</th><th>Vencimento</th><th>Valor</th><th>Status</th><th>Data Pag.</th></tr>
        """

        for p in parcelas:
            status_class = "pago" if p.pago else "pendente"
            status_text = "Pago" if p.pago else "Pendente"
            data_pagamento = p.data_pagamento.strftime('%d/%m/%Y') if p.data_pagamento else "N/A"
            html += f"""
                <tr><td>{p.numero}</td><td>{p.data_vencimento.strftime('%d/%m/%Y')}</td>
                    <td>R$ {p.valor:,.2f}</td><td class="{status_class}">{status_text}</td><td>{data_pagamento}</td></tr>
            """

        html += "</table></body></html>"
        return html

    def update_emprestimo_com_parcelas(self, emprestimo_id: int, data: Dict[str, Any]):
        """Atualiza um empréstimo existente e recalcula todas as suas parcelas."""
        emprestimo = self.get_emprestimo_by_id(emprestimo_id)
        if not emprestimo:
            raise ValueError(f"Empréstimo com ID {emprestimo_id} não encontrado.")

        # Remove as parcelas antigas antes de recalcular
        self.db.query(Parcela).filter(Parcela.emprestimo_id == emprestimo_id).delete()

        # Atualiza os dados do empréstimo
        emprestimo.valor = data['valor']
        emprestimo.numero_parcelas = data['numero_parcelas']
        emprestimo.data_inicio = data['data_inicio']
        emprestimo.tipo_juros = data['tipo_juros']
        self.db.flush()

        # Chama o método auxiliar para recalcular e criar as novas parcelas
        self._calcular_e_criar_parcelas(emprestimo)
        self.db.commit()