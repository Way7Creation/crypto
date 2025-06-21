"""
News analysis модули для торгового бота
Файл: src/analysis/news/__init__.py

Анализ влияния новостей на криптовалютные рынки
"""

# Безопасный импорт компонентов
try:
    from .impact_scorer import NewsImpactScorer
except ImportError as e:
    print(f"⚠️ Не удалось импортировать NewsImpactScorer: {e}")
    NewsImpactScorer = None

# Экспортируем все доступные компоненты
__all__ = [
    'NewsImpactScorer'
]

# Создаем базовую заглушку для NewsImpactScorer если модуль недоступен
if NewsImpactScorer is None:
    class NewsImpactScorer:
        """Базовая заглушка для анализатора новостей"""
        def __init__(self):
            pass
        
        def score_news_impact(self, news_text: str, symbol: str = None) -> float:
            """Базовая оценка влияния новостей"""
            return 0.5  # Нейтральное влияние
        
        def analyze_sentiment(self, text: str) -> dict:
            """Базовый анализ настроений"""
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.5
            }