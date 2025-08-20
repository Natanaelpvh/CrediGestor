from models.taxas_emprestimo import TaxaJuros

class TaxaJurosService:
    def __init__(self, db_session):
        self.db_session = db_session

    def get_taxas(self):
        taxas = self.db_session.query(TaxaJuros).first()
        if not taxas:
            taxas = TaxaJuros()
            self.db_session.add(taxas)
            self.db_session.commit()
        return taxas

    def atualizar_taxas(self, simples, composto, mora):
        taxas = self.get_taxas()
        taxas.taxa_juros_simples = simples
        taxas.taxa_juros_composto = composto
        taxas.taxa_juros_mora = mora
        self.db_session.commit()
        return taxas
