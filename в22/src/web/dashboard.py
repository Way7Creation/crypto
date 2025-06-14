"""
Улучшенный дашборд для торгового бота
Путь: src/web/dashboard.py
"""

def get_dashboard_html() -> str:
    """Возвращает HTML код улучшенного дашборда"""
    # Я разбил HTML на части для избежания проблем с экранированием
    
    # Стили
    styles = """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --bg-primary: #0a0e27;
            --bg-secondary: #1a1f36;
            --bg-card: rgba(255,255,255,0.05);
            --text-primary: #ffffff;
            --text-secondary: #9ca3af;
            --accent-primary: #667eea;
            --accent-secondary: #764ba2;
            --success: #4ade80;
            --danger: #f87171;
            --warning: #fbbf24;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header */
        .header {
            background: var(--bg-secondary);
            padding: 20px 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            font-size: 2rem;
            background: linear-gradient(45deg, var(--accent-primary), var(--accent-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Navigation Tabs */
        .nav-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            background: var(--bg-card);
            padding: 10px;
            border-radius: 10px;
        }
        
        .nav-tab {
            padding: 10px 20px;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.3s;
            font-size: 14px;
            font-weight: 500;
        }
        
        .nav-tab.active {
            background: linear-gradient(45deg, var(--accent-primary), var(--accent-secondary));
            color: white;
        }
        
        .nav-tab:hover:not(.active) {
            background: rgba(255,255,255,0.1);
        }
        
        /* Tab Content */
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        /* Grid System */
        .grid {
            display: grid;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .grid-2 {
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
        }
        
        .grid-3 {
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
        }
        
        .grid-4 {
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        }
        
        /* Cards */
        .card {
            background: var(--bg-card);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s, border-color 0.3s;
        }
        
        .card:hover {
            transform: translateY(-5px);
            border-color: rgba(102, 126, 234, 0.3);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .card h3 {
            font-size: 14px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 0;
        }
        
        /* Metrics */
        .metric {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 10px 0;
        }
        
        .metric-small {
            font-size: 1.5rem;
        }
        
        .metric.positive {
            color: var(--success);
        }
        
        .metric.negative {
            color: var(--danger);
        }
        
        .metric-label {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        /* Charts */
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }
        
        .chart-container-large {
            height: 500px;
        }
        
        /* Trading View Widget */
        #tradingview-widget {
            height: 600px;
            border-radius: 15px;
            overflow: hidden;
            margin-bottom: 30px;
        }
        
        /* Tables */
        .table-container {
            overflow-x: auto;
            margin-top: 20px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        th {
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 1px;
        }
        
        tr:hover {
            background: rgba(255,255,255,0.02);
        }
        
        /* Status Badge */
        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-badge.success {
            background: rgba(74, 222, 128, 0.2);
            color: var(--success);
        }
        
        .status-badge.danger {
            background: rgba(248, 113, 113, 0.2);
            color: var(--danger);
        }
        
        .status-badge.warning {
            background: rgba(251, 191, 36, 0.2);
            color: var(--warning);
        }
        
        /* Progress Bar */
        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
            transition: width 0.3s;
        }
        
        /* Recommendations */
        .recommendation {
            background: rgba(102, 126, 234, 0.1);
            border-left: 4px solid var(--accent-primary);
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        
        .recommendation h4 {
            margin-bottom: 5px;
            color: var(--accent-primary);
        }
        
        /* Loader */
        .loader {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: var(--accent-primary);
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .grid-2, .grid-3, .grid-4 {
                grid-template-columns: 1fr;
            }
            
            .header {
                flex-direction: column;
                gap: 20px;
            }
            
            .nav-tabs {
                overflow-x: auto;
                flex-wrap: nowrap;
            }
        }
    """
    
    # JavaScript
    javascript = """
        // Global variables
        let ws = null;
        let charts = {};
        let currentPair = 'BTCUSDT';
        const API_URL = window.location.origin;
        
        // Initialize on load
        window.onload = function() {
            initializeCharts();
            connectWebSocket();
            refreshAllData();
            initializeTradingView();
        };
        
        // Tab switching
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Remove active class from all nav tabs
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            
            // Add active class to clicked nav tab
            event.target.classList.add('active');
            
            // Load specific data for tab if needed
            if (tabName === 'analytics') {
                loadAnalyticsData();
            } else if (tabName === 'performance') {
                loadPerformanceReport();
            } else if (tabName === 'settings') {
                loadSettings();
            }
        }
        
        // WebSocket connection
        function connectWebSocket() {
            const wsUrl = `ws://${window.location.host}/ws/${generateClientId()}`;
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                document.getElementById('connection-status').innerHTML = '🟢 Connected';
                document.getElementById('connection-status').classList.add('success');
            };
            
            ws.onclose = () => {
                document.getElementById('connection-status').innerHTML = '🔴 Disconnected';
                document.getElementById('connection-status').classList.remove('success');
                document.getElementById('connection-status').classList.add('danger');
                // Reconnect after 5 seconds
                setTimeout(connectWebSocket, 5000);
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
        }
        
        function generateClientId() {
            return Math.random().toString(36).substr(2, 9);
        }
        
        // Initialize all charts
        function initializeCharts() {
            // Equity Curve Chart
            const equityCtx = document.getElementById('equity-chart').getContext('2d');
            charts.equity = new Chart(equityCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Equity',
                        data: [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 2,
                        tension: 0.1,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                unit: 'day'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: '#9ca3af'
                            }
                        },
                        y: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: '#9ca3af',
                                callback: function(value) {
                                    return '$' + value.toFixed(0);
                                }
                            }
                        }
                    }
                }
            });
            
            // Win/Loss Distribution Chart
            const winlossCtx = document.getElementById('winloss-chart').getContext('2d');
            charts.winloss = new Chart(winlossCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Wins', 'Losses'],
                    datasets: [{
                        data: [0, 0],
                        backgroundColor: ['#4ade80', '#f87171'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#9ca3af',
                                padding: 20
                            }
                        }
                    }
                }
            });
            
            // Hourly Performance Chart
            const hourlyCtx = document.getElementById('hourly-chart').getContext('2d');
            charts.hourly = new Chart(hourlyCtx, {
                type: 'bar',
                data: {
                    labels: Array.from({length: 24}, (_, i) => i + ':00'),
                    datasets: [{
                        label: 'Average P&L',
                        data: new Array(24).fill(0),
                        backgroundColor: function(context) {
                            const value = context.parsed.y;
                            return value >= 0 ? '#4ade80' : '#f87171';
                        }
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: '#9ca3af',
                                callback: function(value) {
                                    return '$' + value.toFixed(0);
                                }
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: '#9ca3af'
                            }
                        }
                    }
                }
            });
            
            // Pairs Performance Chart
            const pairsCtx = document.getElementById('pairs-chart').getContext('2d');
            charts.pairs = new Chart(pairsCtx, {
                type: 'horizontalBar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Total P&L',
                        data: [],
                        backgroundColor: []
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: '#9ca3af',
                                callback: function(value) {
                                    return '$' + value.toFixed(0);
                                }
                            }
                        },
                        y: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: '#9ca3af'
                            }
                        }
                    }
                }
            });
            
            // Strategy Performance Chart
            const strategyCtx = document.getElementById('strategy-chart').getContext('2d');
            charts.strategy = new Chart(strategyCtx, {
                type: 'radar',
                data: {
                    labels: ['Win Rate', 'Avg Profit', 'Total Trades', 'Profit Factor', 'Consistency'],
                    datasets: []
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            pointLabels: {
                                color: '#9ca3af'
                            },
                            ticks: {
                                color: '#9ca3af',
                                backdropColor: 'transparent'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: {
                                color: '#9ca3af'
                            }
                        }
                    }
                }
            });
        }
        
        // Initialize TradingView widget
        function initializeTradingView() {
            new TradingView.widget({
                "width": "100%",
                "height": 600,
                "symbol": "BINANCE:" + currentPair,
                "interval": "5",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "allow_symbol_change": true,
                "container_id": "tradingview-widget",
                "studies": [
                    "RSI@tv-basicstudies",
                    "BB@tv-basicstudies",
                    "MACD@tv-basicstudies"
                ]
            });
        }
        
        // Refresh all data
        async function refreshAllData() {
            try {
                // Get dashboard data
                const response = await fetch(`${API_URL}/api/dashboard`);
                if (response.ok) {
                    const data = await response.json();
                    updateFromApiData(data);
                }
                
                // Update other specific data
                await updateEquityCurve();
                
            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }
        
        // Update dashboard from API data
        function updateFromApiData(data) {
            // Update balance
            if (data.balance && data.balance.USDT) {
                document.getElementById('total-balance').textContent = `$${data.balance.USDT.total.toFixed(2)}`;
            }
            
            // Update statistics
            if (data.statistics) {
                const stats = data.statistics;
                document.getElementById('daily-pnl').textContent = `$${stats.total_profit.toFixed(2)}`;
                document.getElementById('daily-pnl').className = stats.total_profit >= 0 ? 'metric positive' : 'metric negative';
                
                document.getElementById('win-rate').textContent = `${stats.win_rate.toFixed(1)}%`;
                document.getElementById('win-rate-bar').style.width = `${stats.win_rate}%`;
                
                document.getElementById('trades-today').textContent = `${stats.total_trades} trades`;
                
                // Update win/loss chart
                if (charts.winloss) {
                    charts.winloss.data.datasets[0].data = [
                        stats.profitable_trades,
                        stats.total_trades - stats.profitable_trades
                    ];
                    charts.winloss.update();
                }
            }
            
            // Update recent trades
            if (data.recent_trades) {
                updateTradesTable(data.recent_trades);
            }
            
            // Update recent signals
            if (data.recent_signals) {
                updateSignalsTable(data.recent_signals);
            }
            
            // Update bot status
            if (data.bot_status) {
                updateBotStatus(data.bot_status);
            }
        }
        
        // Update trades table
        function updateTradesTable(trades) {
            const tbody = document.getElementById('recent-trades-tbody');
            
            if (trades.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No trades yet</td></tr>';
                return;
            }
            
            tbody.innerHTML = trades.map(trade => {
                const profitClass = trade.profit >= 0 ? 'positive' : 'negative';
                const statusClass = trade.status === 'CLOSED' ? 'success' : 'warning';
                
                return `
                    <tr>
                        <td>${new Date(trade.created_at).toLocaleString()}</td>
                        <td>${trade.symbol}</td>
                        <td>${trade.side}</td>
                        <td>$${trade.entry_price.toFixed(2)}</td>
                        <td>${trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : '-'}</td>
                        <td class="${profitClass}">
                            ${trade.profit !== null ? `$${trade.profit.toFixed(2)}` : '-'}
                        </td>
                        <td>${calculateDuration(trade.created_at, trade.closed_at)}</td>
                        <td><span class="status-badge ${statusClass}">${trade.status}</span></td>
                    </tr>
                `;
            }).join('');
        }
        
        // Update signals table
        function updateSignalsTable(signals) {
            const tbody = document.getElementById('signals-tbody');
            
            if (signals.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">No signals yet</td></tr>';
                return;
            }
            
            tbody.innerHTML = signals.map(signal => {
                const actionClass = signal.action === 'BUY' ? 'success' : 'danger';
                const confidencePercent = (signal.confidence * 100).toFixed(1);
                
                return `
                    <tr>
                        <td>${new Date(signal.created_at).toLocaleString()}</td>
                        <td>${signal.symbol}</td>
                        <td><span class="status-badge ${actionClass}">${signal.action}</span></td>
                        <td>${signal.strategy || 'N/A'}</td>
                        <td>${confidencePercent}%</td>
                        <td>${signal.reason}</td>
                        <td>${signal.executed ? '✅' : '❌'}</td>
                    </tr>
                `;
            }).join('');
        }
        
        // Update bot status
        function updateBotStatus(status) {
            const statusEl = document.getElementById('bot-status');
            
            if (status.is_running) {
                statusEl.textContent = 'Running';
                statusEl.className = 'status-badge success';
                document.getElementById('start-bot-btn').style.display = 'none';
                document.getElementById('stop-bot-btn').style.display = 'inline-block';
            } else {
                statusEl.textContent = 'Stopped';
                statusEl.className = 'status-badge danger';
                document.getElementById('start-bot-btn').style.display = 'inline-block';
                document.getElementById('stop-bot-btn').style.display = 'none';
            }
            
            document.getElementById('active-positions').textContent = status.open_positions || 0;
        }
        
        // Update equity curve
        async function updateEquityCurve() {
            const period = document.getElementById('equity-period').value;
            
            try {
                const response = await fetch(`${API_URL}/api/balance/history?period=${period}`);
                if (response.ok) {
                    const data = await response.json();
                    
                    if (charts.equity && data.length > 0) {
                        charts.equity.data.labels = data.map(d => new Date(d.timestamp));
                        charts.equity.data.datasets[0].data = data.map(d => d.total);
                        charts.equity.update();
                    }
                }
            } catch (error) {
                console.error('Error updating equity curve:', error);
            }
        }
        
        // Load analytics data
        async function loadAnalyticsData() {
            try {
                const response = await fetch(`${API_URL}/api/analytics/report?days=30`);
                if (response.ok) {
                    const report = await response.json();
                    
                    // Update hourly chart
                    if (report.time_analysis && charts.hourly) {
                        const hourlyData = new Array(24).fill(0);
                        for (let hour = 0; hour < 24; hour++) {
                            const hourData = report.time_analysis.by_hour[`hour_${hour}`];
                            if (hourData && hourData.trades > 0) {
                                hourlyData[hour] = hourData.profit / hourData.trades;
                            }
                        }
                        charts.hourly.data.datasets[0].data = hourlyData;
                        charts.hourly.update();
                    }
                    
                    // Update pairs chart
                    if (report.pairs_performance && charts.pairs) {
                        const pairs = Object.entries(report.pairs_performance.pairs);
                        charts.pairs.data.labels = pairs.map(p => p[0]);
                        charts.pairs.data.datasets[0].data = pairs.map(p => p[1].profit);
                        charts.pairs.data.datasets[0].backgroundColor = pairs.map(p => 
                            p[1].profit >= 0 ? '#4ade80' : '#f87171'
                        );
                        charts.pairs.update();
                    }
                    
                    // Update best/worst trades
                    if (report.best_trades) {
                        updateBestWorstTrades(report.best_trades, report.worst_trades);
                    }
                }
            } catch (error) {
                console.error('Error loading analytics:', error);
            }
        }
        
        // Load performance report
        async function loadPerformanceReport() {
            try {
                const response = await fetch(`${API_URL}/api/analytics/report?days=30`);
                if (response.ok) {
                    const report = await response.json();
                    
                    // Update performance metrics
                    if (report.summary) {
                        document.getElementById('monthly-return').textContent = 
                            `${((report.summary.total_profit / 10000) * 100).toFixed(2)}%`;
                        
                        document.getElementById('profit-factor').textContent = 
                            report.summary.profit_factor !== 'inf' ? report.summary.profit_factor : '∞';
                        
                        // Update detailed statistics
                        document.getElementById('stat-total-trades').textContent = report.summary.total_trades;
                        document.getElementById('stat-winning-trades').textContent = report.summary.profitable_trades;
                        document.getElementById('stat-losing-trades').textContent = report.summary.losing_trades;
                        document.getElementById('stat-avg-win').textContent = `$${report.summary.average_win.toFixed(2)}`;
                        document.getElementById('stat-avg-loss').textContent = `$${Math.abs(report.summary.average_loss).toFixed(2)}`;
                        document.getElementById('stat-expectancy').textContent = `$${report.summary.expectancy.toFixed(2)}`;
                    }
                    
                    // Update drawdown
                    if (report.drawdown) {
                        document.getElementById('max-drawdown').textContent = 
                            `-${report.drawdown.max_drawdown_percent.toFixed(2)}%`;
                    }
                    
                    // Update recommendations
                    if (report.recommendations) {
                        updateRecommendations(report.recommendations);
                    }
                    
                    // Update strategy comparison
                    if (report.strategy_performance) {
                        updateStrategyChart(report.strategy_performance);
                    }
                }
            } catch (error) {
                console.error('Error loading performance report:', error);
            }
        }
        
        // Update recommendations
        function updateRecommendations(recommendations) {
            const container = document.getElementById('recommendations-list');
            
            container.innerHTML = recommendations.map(rec => `
                <div class="recommendation">
                    <h4>📊 ${rec.split(':')[0]}</h4>
                    <p>${rec}</p>
                </div>
            `).join('');
        }
        
        // Update strategy comparison chart
        function updateStrategyChart(strategyData) {
            if (!charts.strategy) return;
            
            const datasets = [];
            const colors = ['#667eea', '#4ade80', '#f87171', '#fbbf24'];
            let colorIndex = 0;
            
            for (const [strategy, data] of Object.entries(strategyData)) {
                const maxTrades = Math.max(...Object.values(strategyData).map(s => s.trades));
                const maxProfit = Math.max(...Object.values(strategyData).map(s => Math.abs(s.avg_profit)));
                
                datasets.push({
                    label: strategy,
                    data: [
                        data.win_rate,
                        (data.avg_profit / maxProfit) * 100,
                        (data.trades / maxTrades) * 100,
                        Math.min(data.profit_factor || 0, 100),
                        data.win_rate * 0.8 + (data.trades / maxTrades) * 20
                    ],
                    borderColor: colors[colorIndex % colors.length],
                    backgroundColor: colors[colorIndex % colors.length] + '33',
                    borderWidth: 2
                });
                colorIndex++;
            }
            
            charts.strategy.data.datasets = datasets;
            charts.strategy.update();
        }
        
        // Load settings
        async function loadSettings() {
            try {
                // Load trading pairs
                const pairsResponse = await fetch(`${API_URL}/api/pairs`);
                if (pairsResponse.ok) {
                    const pairs = await pairsResponse.json();
                    displayPairsConfig(pairs);
                }
            } catch (error) {
                console.error('Error loading settings:', error);
            }
        }
        
        // Display pairs configuration
        function displayPairsConfig(pairs) {
            const container = document.getElementById('pairs-config');
            const allPairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT', 'DOTUSDT', 'DOGEUSDT'];
            
            container.innerHTML = allPairs.map(symbol => {
                const isActive = pairs.some(p => p.symbol === symbol && p.is_active);
                return `
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
                        <input type="checkbox" value="${symbol}" ${isActive ? 'checked' : ''}>
                        <span>${symbol}</span>
                    </label>
                `;
            }).join('');
        }
        
        // Bot control functions
        async function startBot() {
            try {
                const response = await fetch(`${API_URL}/api/bot/action`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ action: 'start' })
                });
                
                if (response.ok) {
                    alert('Bot started successfully');
                    refreshAllData();
                } else {
                    const error = await response.json();
                    alert(`Failed to start bot: ${error.detail}`);
                }
            } catch (error) {
                alert('Connection error');
            }
        }
        
        async function stopBot() {
            if (!confirm('Are you sure you want to stop the bot?')) return;
            
            try {
                const response = await fetch(`${API_URL}/api/bot/action`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ action: 'stop' })
                });
                
                if (response.ok) {
                    alert('Bot stopped successfully');
                    refreshAllData();
                } else {
                    alert('Failed to stop bot');
                }
            } catch (error) {
                alert('Connection error');
            }
        }
        
        // Update trading pairs
        async function updateTradingPairs() {
            const checkboxes = document.querySelectorAll('#pairs-config input[type="checkbox"]:checked');
            const pairs = Array.from(checkboxes).map(cb => cb.value);
            
            if (pairs.length === 0) {
                alert('Please select at least one trading pair');
                return;
            }
            
            try {
                const response = await fetch(`${API_URL}/api/pairs`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(pairs)
                });
                
                if (response.ok) {
                    alert('Trading pairs updated successfully');
                } else {
                    alert('Failed to update pairs');
                }
            } catch (error) {
                alert('Connection error');
            }
        }
        
        // Utility functions
        function calculateDuration(start, end) {
            if (!start || !end) return '-';
            
            const duration = new Date(end) - new Date(start);
            const hours = Math.floor(duration / (1000 * 60 * 60));
            const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60));
            
            return `${hours}h ${minutes}m`;
        }
        
        function updateBestWorstTrades(bestTrades, worstTrades) {
            // Update best trades
            const bestTbody = document.getElementById('best-trades-tbody');
            if (bestTrades && bestTrades.length > 0) {
                bestTbody.innerHTML = bestTrades.map(trade => `
                    <tr>
                        <td>${new Date(trade.date).toLocaleDateString()}</td>
                        <td>${trade.symbol}</td>
                        <td class="positive">$${trade.profit.toFixed(2)}</td>
                        <td>${trade.strategy}</td>
                    </tr>
                `).join('');
            }
            
            // Update worst trades
            const worstTbody = document.getElementById('worst-trades-tbody');
            if (worstTrades && worstTrades.length > 0) {
                worstTbody.innerHTML = worstTrades.map(trade => `
                    <tr>
                        <td>${new Date(trade.date).toLocaleDateString()}</td>
                        <td>${trade.symbol}</td>
                        <td class="negative">$${trade.profit.toFixed(2)}</td>
                        <td>${trade.strategy}</td>
                    </tr>
                `).join('');
            }
        }
        
        // Update dashboard from WebSocket
        function updateDashboard(data) {
            if (data.type === 'update' && data.data) {
                updateFromApiData(data.data);
            }
        }
        
        // Test connection
        async function testConnection() {
            try {
                const response = await fetch(`${API_URL}/api/bot/status`);
                if (response.ok) {
                    alert('Connection successful!');
                } else {
                    alert('Connection failed!');
                }
            } catch (error) {
                alert('Connection error: ' + error.message);
            }
        }
        
        // Auto refresh every 30 seconds
        setInterval(refreshAllData, 30000);
    """
    
    # HTML структура (вынесена в отдельную переменную для удобства)
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Trading Bot - Advanced Dashboard</title>
    
    <!-- Chart.js для графиков -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <!-- Date adapter для Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
    <!-- TradingView widget -->
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    
    <style>{styles}</style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🤖 Crypto Trading Bot - Advanced Analytics</h1>
            <div class="header-controls">
                <span id="connection-status" class="status-badge">
                    <span class="loader"></span> Connecting...
                </span>
                <button id="refresh-btn" class="nav-tab" onclick="refreshAllData()">
                    🔄 Refresh
                </button>
            </div>
        </div>
        
        <!-- Navigation Tabs -->
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('overview')">📊 Overview</button>
            <button class="nav-tab" onclick="showTab('trading')">💹 Live Trading</button>
            <button class="nav-tab" onclick="showTab('analytics')">📈 Analytics</button>
            <button class="nav-tab" onclick="showTab('performance')">🎯 Performance</button>
            <button class="nav-tab" onclick="showTab('settings')">⚙️ Settings</button>
        </div>
        
        <!-- Tab: Overview -->
        <div id="overview-tab" class="tab-content active">
            <!-- Key Metrics -->
            <div class="grid grid-4">
                <div class="card">
                    <h3>Total Balance</h3>
                    <div id="total-balance" class="metric">$0.00</div>
                    <div class="metric-label">
                        <span id="balance-change">+0.00%</span> today
                    </div>
                </div>
                
                <div class="card">
                    <h3>Today's P&L</h3>
                    <div id="daily-pnl" class="metric">$0.00</div>
                    <div class="metric-label">
                        <span id="trades-today">0 trades</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3>Win Rate</h3>
                    <div id="win-rate" class="metric">0%</div>
                    <div class="progress-bar">
                        <div id="win-rate-bar" class="progress-fill" style="width: 0%"></div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>Active Positions</h3>
                    <div id="active-positions" class="metric">0</div>
                    <div class="metric-label">
                        Risk: <span id="total-risk">$0.00</span>
                    </div>
                </div>
            </div>
            
            <!-- Charts Row -->
            <div class="grid grid-2">
                <!-- Equity Curve -->
                <div class="card">
                    <div class="card-header">
                        <h3>Equity Curve</h3>
                        <select id="equity-period" onchange="updateEquityCurve()">
                            <option value="day">1 Day</option>
                            <option value="week" selected>1 Week</option>
                            <option value="month">1 Month</option>
                            <option value="all">All Time</option>
                        </select>
                    </div>
                    <div class="chart-container">
                        <canvas id="equity-chart"></canvas>
                    </div>
                </div>
                
                <!-- Win/Loss Distribution -->
                <div class="card">
                    <h3>Win/Loss Distribution</h3>
                    <div class="chart-container">
                        <canvas id="winloss-chart"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- Recent Trades -->
            <div class="card">
                <h3>Recent Trades</h3>
                <div class="table-container">
                    <table id="recent-trades-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Pair</th>
                                <th>Side</th>
                                <th>Entry</th>
                                <th>Exit</th>
                                <th>Profit</th>
                                <th>Duration</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="recent-trades-tbody">
                            <tr><td colspan="8" style="text-align: center;">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Tab: Live Trading -->
        <div id="trading-tab" class="tab-content">
            <!-- TradingView Widget -->
            <div id="tradingview-widget"></div>
            
            <!-- Active Positions -->
            <div class="card">
                <h3>Active Positions</h3>
                <div class="table-container">
                    <table id="positions-table">
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Side</th>
                                <th>Entry Price</th>
                                <th>Current Price</th>
                                <th>Quantity</th>
                                <th>Unrealized P&L</th>
                                <th>Stop Loss</th>
                                <th>Take Profit</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="positions-tbody">
                            <tr><td colspan="9" style="text-align: center;">No active positions</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Recent Signals -->
            <div class="card">
                <h3>Recent Trading Signals</h3>
                <div class="table-container">
                    <table id="signals-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Symbol</th>
                                <th>Action</th>
                                <th>Strategy</th>
                                <th>Confidence</th>
                                <th>Reason</th>
                                <th>Executed</th>
                            </tr>
                        </thead>
                        <tbody id="signals-tbody">
                            <tr><td colspan="7" style="text-align: center;">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Tab: Analytics -->
        <div id="analytics-tab" class="tab-content">
            <div class="grid grid-2">
                <!-- Performance by Hour -->
                <div class="card">
                    <h3>Performance by Hour</h3>
                    <div class="chart-container">
                        <canvas id="hourly-chart"></canvas>
                    </div>
                </div>
                
                <!-- Performance by Pair -->
                <div class="card">
                    <h3>Performance by Trading Pair</h3>
                    <div class="chart-container">
                        <canvas id="pairs-chart"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- Strategy Performance -->
            <div class="card">
                <h3>Strategy Performance Comparison</h3>
                <div class="chart-container">
                    <canvas id="strategy-chart"></canvas>
                </div>
            </div>
            
            <!-- Trade Analysis -->
            <div class="grid grid-2">
                <div class="card">
                    <h3>Best Trades</h3>
                    <div class="table-container">
                        <table id="best-trades-table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Symbol</th>
                                    <th>Profit</th>
                                    <th>Strategy</th>
                                </tr>
                            </thead>
                            <tbody id="best-trades-tbody">
                                <tr><td colspan="4">Loading...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="card">
                    <h3>Worst Trades</h3>
                    <div class="table-container">
                        <table id="worst-trades-table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Symbol</th>
                                    <th>Loss</th>
                                    <th>Strategy</th>
                                </tr>
                            </thead>
                            <tbody id="worst-trades-tbody">
                                <tr><td colspan="4">Loading...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Tab: Performance -->
        <div id="performance-tab" class="tab-content">
            <!-- Performance Summary -->
            <div class="grid grid-3">
                <div class="card">
                    <h3>Monthly Performance</h3>
                    <div id="monthly-return" class="metric metric-small">0%</div>
                    <div class="metric-label">This month</div>
                </div>
                
                <div class="card">
                    <h3>Max Drawdown</h3>
                    <div id="max-drawdown" class="metric metric-small negative">0%</div>
                    <div class="metric-label">Historical maximum</div>
                </div>
                
                <div class="card">
                    <h3>Profit Factor</h3>
                    <div id="profit-factor" class="metric metric-small">0.0</div>
                    <div class="metric-label">Win/Loss ratio</div>
                </div>
            </div>
            
            <!-- Detailed Statistics -->
            <div class="card">
                <h3>Detailed Trading Statistics</h3>
                <div class="grid grid-2">
                    <div>
                        <table>
                            <tr>
                                <td>Total Trades</td>
                                <td><strong id="stat-total-trades">0</strong></td>
                            </tr>
                            <tr>
                                <td>Winning Trades</td>
                                <td><strong id="stat-winning-trades" class="positive">0</strong></td>
                            </tr>
                            <tr>
                                <td>Losing Trades</td>
                                <td><strong id="stat-losing-trades" class="negative">0</strong></td>
                            </tr>
                            <tr>
                                <td>Average Win</td>
                                <td><strong id="stat-avg-win" class="positive">$0.00</strong></td>
                            </tr>
                            <tr>
                                <td>Average Loss</td>
                                <td><strong id="stat-avg-loss" class="negative">$0.00</strong></td>
                            </tr>
                        </table>
                    </div>
                    <div>
                        <table>
                            <tr>
                                <td>Largest Win</td>
                                <td><strong id="stat-largest-win" class="positive">$0.00</strong></td>
                            </tr>
                            <tr>
                                <td>Largest Loss</td>
                                <td><strong id="stat-largest-loss" class="negative">$0.00</strong></td>
                            </tr>
                            <tr>
                                <td>Average Trade Duration</td>
                                <td><strong id="stat-avg-duration">0h 0m</strong></td>
                            </tr>
                            <tr>
                                <td>Expectancy</td>
                                <td><strong id="stat-expectancy">$0.00</strong></td>
                            </tr>
                            <tr>
                                <td>System Quality Number</td>
                                <td><strong id="stat-sqn">0.0</strong></td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            
            <!-- Recommendations -->
            <div class="card">
                <h3>AI Recommendations</h3>
                <div id="recommendations-list">
                    <div class="recommendation">
                        <h4>Loading recommendations...</h4>
                        <p>Analyzing your trading patterns...</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Tab: Settings -->
        <div id="settings-tab" class="tab-content">
            <!-- Bot Control -->
            <div class="card">
                <h3>Bot Control</h3>
                <div style="display: flex; gap: 20px; margin-top: 20px;">
                    <button id="start-bot-btn" class="nav-tab" onclick="startBot()">▶️ Start Bot</button>
                    <button id="stop-bot-btn" class="nav-tab" onclick="stopBot()">⏹️ Stop Bot</button>
                    <button class="nav-tab" onclick="testConnection()">🔌 Test Connection</button>
                </div>
                <div id="bot-status-info" style="margin-top: 20px;">
                    <p>Status: <span id="bot-status" class="status-badge">Unknown</span></p>
                </div>
            </div>
            
            <!-- Trading Pairs Configuration -->
            <div class="card">
                <h3>Active Trading Pairs</h3>
                <div id="pairs-config" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; margin-top: 20px;">
                    <!-- Pairs checkboxes will be loaded here -->
                </div>
                <button class="nav-tab" style="margin-top: 20px;" onclick="updateTradingPairs()">
                    💾 Save Configuration
                </button>
            </div>
            
            <!-- Risk Management -->
            <div class="card">
                <h3>Risk Management Settings</h3>
                <div style="display: grid; gap: 15px; margin-top: 20px;">
                    <div>
                        <label>Max Position Size (%)</label>
                        <input type="number" id="max-position-size" value="5" min="1" max="100" step="0.5">
                    </div>
                    <div>
                        <label>Stop Loss (%)</label>
                        <input type="number" id="stop-loss-percent" value="2" min="0.5" max="10" step="0.5">
                    </div>
                    <div>
                        <label>Take Profit (%)</label>
                        <input type="number" id="take-profit-percent" value="4" min="1" max="20" step="0.5">
                    </div>
                    <div>
                        <label>Max Daily Trades</label>
                        <input type="number" id="max-daily-trades" value="10" min="1" max="50" step="1">
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>{javascript}</script>
</body>
</html>'''
    
    return html_content


# Заменяем старую функцию в dashboard.py
def update_dashboard_file():
    """Обновляем файл dashboard.py с новым кодом"""
    dashboard_file = 'src/web/dashboard.py'
    
    new_content = '''"""
Улучшенный дашборд для торгового бота
Путь: src/web/dashboard.py
"""

def get_dashboard_html() -> str:
    """Возвращает HTML код улучшенного дашборда"""
''' + '''
    # Код функции get_dashboard_html вставлен выше
    return get_dashboard_html()
'''
    
    # Записываем новый файл
    with open(dashboard_file, 'w', encoding='utf-8') as f:
        # Импортируем функцию из этого файла
        f.write('"""')
        f.write('\nУлучшенный дашборд для торгового бота')
        f.write('\nПуть: src/web/dashboard.py')
        f.write('\n"""')
        f.write('\n\n')
        f.write('def get_dashboard_html() -> str:')
        f.write('\n    """Возвращает HTML код улучшенного дашборда"""')
        f.write('\n    ')
        f.write(get_dashboard_html().__doc__)
        f.write('\n    return ')
        f.write(repr(get_dashboard_html()))
    
    print(f"✅ Обновлен файл {dashboard_file}")