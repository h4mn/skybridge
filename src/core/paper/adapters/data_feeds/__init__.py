"""
Data Feeds Adapters - Paper Trading

Implementações concretas de DataFeedPort para diferentes fontes de dados.

Adapters planejados:
- YahooFinanceFeed: Dados do Yahoo Finance (gratuito)
- AlphaVantageFeed: Dados do Alpha Vantage (API key)
- BinanceFeed: Dados de cripto da Binance
- MockDataFeed: Dados simulados para testes

Exemplo de uso:
    from src.core.paper.adapters.data_feeds import YahooFinanceFeed

    feed = YahooFinanceFeed()
    cotacao = await feed.obter_cotacao("PETR4.SA")
    print(f"Preço: {cotacao.preco}")
"""

# TODO: Implementar adapters de data feed
# from .yahoo_finance_feed import YahooFinanceFeed
# from .alpha_vantage_feed import AlphaVantageFeed
# from .mock_data_feed import MockDataFeed

__all__ = []
