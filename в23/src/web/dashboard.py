"""
Полный дашборд для управления криптотрейдинг ботом
Файл: src/web/dashboard.py
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio

def get_dashboard_html() -> str:
    """Возвращает HTML код полного дашборда для управления ботом"""
    
    css = """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff;
            min-height: 100vh;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: 280px 1fr;
            min-height: 100vh;
        }
        
        .sidebar {
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px;
        }
        
        .logo {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .logo h1 {
            font-size: 24px;
            color: #4CAF50;
            margin-bottom: 5px;
        }
        
        .logo p {
            font-size: 12px;
            opacity: 0.7;
        }
        
        .nav-menu {
            list-style: none;
        }
        
        .nav-item {
            margin-bottom: 10px;
        }
        
        .nav-link {
            display: flex;
            align-items: center;
            padding: 12px 15px;
            color: #fff;
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .nav-link:hover, .nav-link.active {
            background: rgba(76, 175, 80, 0.2);
            color: #4CAF50;
        }
        
        .nav-icon {
            margin-right: 10px;
            width: 20px;
        }
        
        .main-content {
            padding: 20px;
            overflow-y: auto;
        }
        
        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 15px 20px;
            border-radius: 12px;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .status-active {
            background: #4CAF50;
        }
        
        .status-inactive {
            background: #f44336;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .content-section {
            display: none;
        }
        
        .content-section.active {
            display: block;
        }
        
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .card h3 {
            margin-bottom: 15px;
            color: #4CAF50;
            font-size: 18px;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 14px;
            opacity: 0.7;
        }
        
        .button {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            transition: all 0.3s ease;
            margin: 5px;
        }
        
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
        }
        
        .button.danger {
            background: linear-gradient(45deg, #f44336, #d32f2f);
        }
        
        .button.warning {
            background: linear-gradient(45deg, #ff9800, #f57c00);
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
        }
        
        .form-control {
            width: 100%;
            padding: 12px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            font-size: 14px;
        }
        
        .form-control::placeholder {
            color: rgba(255, 255, 255, 0.5);
        }
        
        .trades-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .trades-table th,
        .trades-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .trades-table th {
            background: rgba(255, 255, 255, 0.1);
            font-weight: bold;
        }
        
        .profit {
            color: #4CAF50;
        }
        
        .loss {
            color: #f44336;
        }
        
        .log-container {
            height: 400px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
        
        .log-entry {
            margin-bottom: 5px;
            padding: 5px;
            border-radius: 4px;
        }
        
        .log-info {
            color: #4CAF50;
        }
        
        .log-warning {
            color: #ff9800;
            background: rgba(255, 152, 0, 0.1);
        }
        
        .log-error {
            color: #f44336;
            background: rgba(244, 67, 54, 0.1);
        }
        
        .strategy-card {
            border: 2px solid transparent;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .strategy-card:hover {
            border-color: #4CAF50;
            transform: translateY(-2px);
        }
        
        .strategy-card.selected {
            border-color: #4CAF50;
            background: rgba(76, 175, 80, 0.1);
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        }
        
        .notification.success {
            background: #4CAF50;
        }
        
        .notification.error {
            background: #f44336;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    </style>
    """
    
    javascript = """
    // Глобальные переменные
    let botStatus = 'inactive';
    let selectedStrategy = 'momentum';
    let ws = null;
    
    // Инициализация при загрузке страницы
    document.addEventListener('DOMContentLoaded', function() {
        initializeWebSocket();
        showSection('dashboard');
        updateStatus();
        loadTrades();
        setInterval(updateStats, 5000);
    });
    
    // WebSocket подключение
    function initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        ws = new WebSocket(wsUrl);
        
        ws.onopen = function() {
            showNotification('WebSocket подключен', 'success');
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        ws.onclose = function() {
            showNotification('WebSocket отключен', 'error');
            setTimeout(initializeWebSocket, 5000);
        };
    }
    
    // Обработка WebSocket сообщений
    function handleWebSocketMessage(data) {
        switch(data.type) {
            case 'bot_status':
                botStatus = data.status;
                updateStatus();
                break;
            case 'new_trade':
                addTradeToTable(data.trade);
                updateStats();
                break;
            case 'log':
                addLogEntry(data.message, data.level);
                break;
        }
    }
    
    // Показать секцию
    function showSection(sectionName) {
        // Скрыть все секции
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Показать выбранную секцию
        document.getElementById(sectionName + '-section').classList.add('active');
        
        // Обновить навигацию
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[onclick="showSection('${sectionName}')"]`).classList.add('active');
    }
    
    // Управление ботом
    async function startBot() {
        try {
            const response = await fetch('/api/bot/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({strategy: selectedStrategy})
            });
            
            if (response.ok) {
                showNotification('Бот запущен успешно', 'success');
                botStatus = 'active';
                updateStatus();
            } else {
                throw new Error('Ошибка запуска бота');
            }
        } catch (error) {
            showNotification('Ошибка запуска бота: ' + error.message, 'error');
        }
    }
    
    async function stopBot() {
        try {
            const response = await fetch('/api/bot/stop', {method: 'POST'});
            
            if (response.ok) {
                showNotification('Бот остановлен', 'success');
                botStatus = 'inactive';
                updateStatus();
            } else {
                throw new Error('Ошибка остановки бота');
            }
        } catch (error) {
            showNotification('Ошибка остановки бота: ' + error.message, 'error');
        }
    }
    
    async function restartBot() {
        await stopBot();
        setTimeout(startBot, 2000);
    }
    
    // Обновление статуса
    function updateStatus() {
        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');
        
        if (botStatus === 'active') {
            statusDot.className = 'status-dot status-active';
            statusText.textContent = 'Бот активен';
        } else {
            statusDot.className = 'status-dot status-inactive';
            statusText.textContent = 'Бот неактивен';
        }
    }
    
    // Выбор стратегии
    function selectStrategy(strategyName) {
        selectedStrategy = strategyName;
        
        document.querySelectorAll('.strategy-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        event.target.closest('.strategy-card').classList.add('selected');
        showNotification(`Выбрана стратегия: ${strategyName}`, 'success');
    }
    
    // Обновление статистики
    async function updateStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            document.getElementById('total-trades').textContent = stats.totalTrades || 0;
            document.getElementById('profit-loss').textContent = (stats.totalProfit || 0).toFixed(2) + ' USDT';
            document.getElementById('success-rate').textContent = (stats.successRate || 0).toFixed(1) + '%';
            document.getElementById('active-positions').textContent = stats.activePositions || 0;
            
            // Цвет для прибыли/убытка
            const profitElement = document.getElementById('profit-loss');
            if (stats.totalProfit > 0) {
                profitElement.className = 'stat-value profit';
            } else if (stats.totalProfit < 0) {
                profitElement.className = 'stat-value loss';
            } else {
                profitElement.className = 'stat-value';
            }
        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
        }
    }
    
    // Загрузка сделок
    async function loadTrades() {
        try {
            const response = await fetch('/api/trades');
            const trades = await response.json();
            
            const tbody = document.getElementById('trades-tbody');
            tbody.innerHTML = '';
            
            trades.forEach(trade => {
                addTradeToTable(trade);
            });
        } catch (error) {
            console.error('Ошибка загрузки сделок:', error);
        }
    }
    
    // Добавление сделки в таблицу
    function addTradeToTable(trade) {
        const tbody = document.getElementById('trades-tbody');
        const row = document.createElement('tr');
        
        const profitClass = trade.profit > 0 ? 'profit' : trade.profit < 0 ? 'loss' : '';
        
        row.innerHTML = `
            <td>${new Date(trade.timestamp).toLocaleString('ru-RU')}</td>
            <td>${trade.symbol}</td>
            <td>${trade.side}</td>
            <td>${trade.amount}</td>
            <td>${trade.price}</td>
            <td class="${profitClass}">${trade.profit.toFixed(2)} USDT</td>
            <td>${trade.strategy}</td>
        `;
        
        tbody.insertBefore(row, tbody.firstChild);
        
        // Ограничиваем количество строк
        if (tbody.children.length > 50) {
            tbody.removeChild(tbody.lastChild);
        }
    }
    
    // Добавление записи в лог
    function addLogEntry(message, level) {
        const logContainer = document.getElementById('log-container');
        const entry = document.createElement('div');
        entry.className = `log-entry log-${level}`;
        entry.textContent = `[${new Date().toLocaleTimeString('ru-RU')}] ${message}`;
        
        logContainer.insertBefore(entry, logContainer.firstChild);
        
        // Ограничиваем количество записей
        if (logContainer.children.length > 100) {
            logContainer.removeChild(logContainer.lastChild);
        }
    }
    
    // Очистка логов
    function clearLogs() {
        document.getElementById('log-container').innerHTML = '';
        showNotification('Логи очищены', 'success');
    }
    
    // Сохранение настроек
    async function saveSettings() {
        const settings = {
            maxPositionSize: document.getElementById('max-position-size').value,
            stopLoss: document.getElementById('stop-loss').value,
            takeProfit: document.getElementById('take-profit').value,
            maxDailyTrades: document.getElementById('max-daily-trades').value,
            tradingPairs: document.getElementById('trading-pairs').value.split(',').map(s => s.trim())
        };
        
        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(settings)
            });
            
            if (response.ok) {
                showNotification('Настройки сохранены', 'success');
            } else {
                throw new Error('Ошибка сохранения настроек');
            }
        } catch (error) {
            showNotification('Ошибка: ' + error.message, 'error');
        }
    }
    
    // Показать уведомление
    function showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    // Экспорт данных
    async function exportData() {
        try {
            const response = await fetch('/api/export');
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `crypto_bot_data_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            
            showNotification('Данные экспортированы', 'success');
        } catch (error) {
            showNotification('Ошибка экспорта: ' + error.message, 'error');
        }
    }
    """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Криптотрейдинг Бот - Панель управления</title>
        {css}
    </head>
    <body>
        <div class="dashboard">
            <!-- Боковая панель -->
            <div class="sidebar">
                <div class="logo">
                    <h1>🚀 CryptoBot</h1>
                    <p>Панель управления v3.0</p>
                </div>
                
                <ul class="nav-menu">
                    <li class="nav-item">
                        <a class="nav-link active" onclick="showSection('dashboard')">
                            <span class="nav-icon">📊</span>
                            Главная панель
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" onclick="showSection('trading')">
                            <span class="nav-icon">💹</span>
                            Торговля
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" onclick="showSection('strategies')">
                            <span class="nav-icon">🎯</span>
                            Стратегии
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" onclick="showSection('analytics')">
                            <span class="nav-icon">📈</span>
                            Аналитика
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" onclick="showSection('settings')">
                            <span class="nav-icon">⚙️</span>
                            Настройки
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" onclick="showSection('logs')">
                            <span class="nav-icon">📝</span>
                            Логи
                        </a>
                    </li>
                </ul>
            </div>
            
            <!-- Основной контент -->
            <div class="main-content">
                <!-- Верхняя панель -->
                <div class="top-bar">
                    <div class="status-indicator">
                        <div id="status-dot" class="status-dot status-inactive"></div>
                        <span id="status-text">Бот неактивен</span>
                    </div>
                    
                    <div>
                        <button class="button" onclick="startBot()">▶️ Запустить</button>
                        <button class="button warning" onclick="restartBot()">🔄 Перезапуск</button>
                        <button class="button danger" onclick="stopBot()">⏹️ Остановить</button>
                    </div>
                </div>
                
                <!-- Главная панель -->
                <div id="dashboard-section" class="content-section active">
                    <div class="cards-grid">
                        <div class="card">
                            <h3>📊 Всего сделок</h3>
                            <div id="total-trades" class="stat-value">0</div>
                            <div class="stat-label">За всё время</div>
                        </div>
                        
                        <div class="card">
                            <h3>💰 Прибыль/Убыток</h3>
                            <div id="profit-loss" class="stat-value">0.00 USDT</div>
                            <div class="stat-label">Общий результат</div>
                        </div>
                        
                        <div class="card">
                            <h3>🎯 Процент успеха</h3>
                            <div id="success-rate" class="stat-value">0.0%</div>
                            <div class="stat-label">Прибыльные сделки</div>
                        </div>
                        
                        <div class="card">
                            <h3>📈 Активные позиции</h3>
                            <div id="active-positions" class="stat-value">0</div>
                            <div class="stat-label">Текущие</div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>📋 Последние сделки</h3>
                        <table class="trades-table">
                            <thead>
                                <tr>
                                    <th>Время</th>
                                    <th>Пара</th>
                                    <th>Сторона</th>
                                    <th>Объём</th>
                                    <th>Цена</th>
                                    <th>Прибыль</th>
                                    <th>Стратегия</th>
                                </tr>
                            </thead>
                            <tbody id="trades-tbody">
                                <!-- Сделки добавляются динамически -->
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <!-- Торговля -->
                <div id="trading-section" class="content-section">
                    <div class="cards-grid">
                        <div class="card">
                            <h3>💹 Управление торговлей</h3>
                            <div class="form-group">
                                <label>Торговая пара</label>
                                <select class="form-control" id="trading-pair">
                                    <option value="BTCUSDT">BTC/USDT</option>
                                    <option value="ETHUSDT">ETH/USDT</option>
                                    <option value="ADAUSDT">ADA/USDT</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label>Размер позиции (%)</label>
                                <input type="number" class="form-control" id="position-size" value="5" min="1" max="100">
                            </div>
                            
                            <button class="button" onclick="openPosition('buy')">📈 Купить</button>
                            <button class="button danger" onclick="openPosition('sell')">📉 Продать</button>
                        </div>
                        
                        <div class="card">
                            <h3>🎯 Быстрые действия</h3>
                            <button class="button" onclick="closeAllPositions()">🚪 Закрыть все позиции</button>
                            <button class="button warning" onclick="pauseTrading()">⏸️ Приостановить торговлю</button>
                            <button class="button" onclick="resumeTrading()">▶️ Возобновить торговлю</button>
                        </div>
                    </div>
                </div>
                
                <!-- Стратегии -->
                <div id="strategies-section" class="content-section">
                    <div class="cards-grid">
                        <div class="card strategy-card" onclick="selectStrategy('momentum')">
                            <h3>🚀 Momentum</h3>
                            <p>Торговля по трендам и импульсам цены</p>
                            <div class="stat-label">Агрессивная стратегия</div>
                        </div>
                        
                        <div class="card strategy-card" onclick="selectStrategy('multi_indicator')">
                            <h3>📊 Multi Indicator</h3>
                            <p>Комплексный анализ множества индикаторов</p>
                            <div class="stat-label">Сбалансированная стратегия</div>
                        </div>
                        
                        <div class="card strategy-card" onclick="selectStrategy('scalping')">
                            <h3>⚡ Scalping</h3>
                            <p>Быстрые сделки на малых движениях</p>
                            <div class="stat-label">Высокочастотная торговля</div>
                        </div>
                        
                        <div class="card strategy-card" onclick="selectStrategy('safe_multi_indicator')">
                            <h3>🛡️ Safe Multi Indicator</h3>
                            <p>Безопасная версия мульти-индикаторной стратегии</p>
                            <div class="stat-label">Консервативная стратегия</div>
                        </div>
                        
                        <div class="card strategy-card" onclick="selectStrategy('conservative')">
                            <h3>🐢 Conservative</h3>
                            <p>Максимально безопасная торговля</p>
                            <div class="stat-label">Минимальный риск</div>
                        </div>
                    </div>
                </div>
                
                <!-- Аналитика -->
                <div id="analytics-section" class="content-section">
                    <div class="cards-grid">
                        <div class="card">
                            <h3>📈 Производительность</h3>
                            <canvas id="performance-chart" width="400" height="200"></canvas>
                        </div>
                        
                        <div class="card">
                            <h3>💹 Распределение прибыли</h3>
                            <canvas id="profit-chart" width="400" height="200"></canvas>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>📊 Детальная статистика</h3>
                        <button class="button" onclick="exportData()">📥 Экспорт данных</button>
                    </div>
                </div>
                
                <!-- Настройки -->
                <div id="settings-section" class="content-section">
                    <div class="cards-grid">
                        <div class="card">
                            <h3>⚙️ Основные настройки</h3>
                            
                            <div class="form-group">
                                <label>Максимальный размер позиции (%)</label>
                                <input type="number" class="form-control" id="max-position-size" value="5" min="1" max="100" step="0.5">
                            </div>
                            
                            <div class="form-group">
                                <label>Стоп-лосс (%)</label>
                                <input type="number" class="form-control" id="stop-loss" value="2" min="0.5" max="10" step="0.5">
                            </div>
                            
                            <div class="form-group">
                                <label>Тейк-профит (%)</label>
                                <input type="number" class="form-control" id="take-profit" value="4" min="1" max="20" step="0.5">
                            </div>
                            
                            <div class="form-group">
                                <label>Максимум сделок в день</label>
                                <input type="number" class="form-control" id="max-daily-trades" value="10" min="1" max="50">
                            </div>
                            
                            <div class="form-group">
                                <label>Торговые пары (через запятую)</label>
                                <input type="text" class="form-control" id="trading-pairs" value="BTCUSDT,ETHUSDT,ADAUSDT" placeholder="BTCUSDT,ETHUSDT">
                            </div>
                            
                            <button class="button" onclick="saveSettings()">💾 Сохранить настройки</button>
                        </div>
                        
                        <div class="card">
                            <h3>🔔 Уведомления</h3>
                            
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="email-notifications" checked>
                                    Email уведомления
                                </label>
                            </div>
                            
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="telegram-notifications" checked>
                                    Telegram уведомления
                                </label>
                            </div>
                            
                            <div class="form-group">
                                <label>Telegram Bot Token</label>
                                <input type="text" class="form-control" id="telegram-token" placeholder="Введите токен бота">
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Логи -->
                <div id="logs-section" class="content-section">
                    <div class="card">
                        <h3>📝 Системные логи</h3>
                        <button class="button warning" onclick="clearLogs()">🗑️ Очистить логи</button>
                        
                        <div id="log-container" class="log-container">
                            <!-- Логи добавляются динамически -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            {javascript}
        </script>
    </body>
    </html>
    """
    
    return html


# Дополнительные функции для API

class DashboardAPI:
    """API класс для работы с дашбордом"""
    
    @staticmethod
    async def get_bot_status():
        """Получить статус бота"""
        # Здесь должна быть логика получения статуса бота
        return {"status": "inactive", "strategy": None}
    
    @staticmethod
    async def start_bot(strategy: str):
        """Запустить бота с выбранной стратегией"""
        # Здесь должна быть логика запуска бота
        return {"success": True, "message": f"Бот запущен со стратегией {strategy}"}
    
    @staticmethod
    async def stop_bot():
        """Остановить бота"""
        # Здесь должна быть логика остановки бота
        return {"success": True, "message": "Бот остановлен"}
    
    @staticmethod
    async def get_stats():
        """Получить статистику торговли"""
        # Здесь должна быть логика получения статистики
        return {
            "totalTrades": 0,
            "totalProfit": 0.0,
            "successRate": 0.0,
            "activePositions": 0
        }
    
    @staticmethod
    async def get_trades():
        """Получить список сделок"""
        # Здесь должна быть логика получения сделок
        return []
    
    @staticmethod
    async def save_settings(settings: dict):
        """Сохранить настройки"""
        # Здесь должна быть логика сохранения настроек
        return {"success": True, "message": "Настройки сохранены"}


def setup_dashboard_routes(app):
    """Настройка маршрутов для дашборда"""
    
    @app.get("/")
    async def dashboard():
        return HTMLResponse(get_dashboard_html())
    
    @app.get("/api/status")
    async def get_status():
        return await DashboardAPI.get_bot_status()
    
    @app.post("/api/bot/start")
    async def start_bot(data: dict):
        strategy = data.get("strategy", "momentum")
        return await DashboardAPI.start_bot(strategy)
    
    @app.post("/api/bot/stop")
    async def stop_bot():
        return await DashboardAPI.stop_bot()
    
    @app.get("/api/stats")
    async def get_stats():
        return await DashboardAPI.get_stats()
    
    @app.get("/api/trades")
    async def get_trades():
        return await DashboardAPI.get_trades()
    
    @app.post("/api/settings")
    async def save_settings(settings: dict):
        return await DashboardAPI.save_settings(settings)


if __name__ == "__main__":
    print("Дашборд готов к использованию!")
    print("Основные функции:")
    print("- Управление ботом (запуск/остановка)")
    print("- Мониторинг сделок в реальном времени")
    print("- Выбор и настройка стратегий")
    print("- Аналитика и статистика")
    print("- Настройки рисков и уведомлений")
    print("- Чистые логи только важных событий")
    print("- Полностью на русском языке")