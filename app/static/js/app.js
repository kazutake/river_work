/**
 * 河川事業トレンド分析ダッシュボード - フロントエンドアプリケーション
 */

const COLORS = [
    '#1a5276', '#2980b9', '#148f77', '#27ae60', '#e67e22',
    '#c0392b', '#8e44ad', '#2c3e50', '#f39c12', '#16a085',
    '#d35400', '#7f8c8d', '#34495e', '#1abc9c', '#e74c3c',
];

const CATEGORY_COLORS = {
    '事業課題': '#c0392b',
    '数値解析・シミュレーション': '#2980b9',
    '先端技術': '#27ae60',
    '政策・制度': '#8e44ad',
    '発注・調達': '#e67e22',
};

let currentPeriod = '30d';
let currentTab = 'overview';
let charts = {};

// === 初期化 ===
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initFilters();
    loadDashboard();
});

function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            switchTab(tab);
        });
    });
}

function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    document.getElementById(`tab-${tab}`).classList.add('active');

    loadTabData(tab);
}

function initFilters() {
    document.getElementById('period-select')?.addEventListener('change', (e) => {
        currentPeriod = e.target.value;
        loadTabData(currentTab);
    });
}

// === データ読み込み ===
async function loadDashboard() {
    await loadSummary();
    await loadTabData('overview');
}

async function loadSummary() {
    try {
        const data = await fetchAPI('/api/summary');
        document.getElementById('total-articles').textContent = data.total_articles.toLocaleString();
        document.getElementById('today-articles').textContent = data.today_articles.toLocaleString();
        document.getElementById('total-sources').textContent = data.total_sources.toLocaleString();

        // トップキーワード数
        document.getElementById('top-keyword-count').textContent =
            data.top_keywords.length > 0 ? data.top_keywords[0].keyword : '-';
    } catch (e) {
        console.error('サマリー読み込みエラー:', e);
    }
}

async function loadTabData(tab) {
    switch (tab) {
        case 'overview':
            await Promise.all([
                loadCategoryChart(),
                loadTopKeywords(),
            ]);
            break;
        case 'simulation':
            await loadSimulationTrends();
            break;
        case 'timeseries':
            await loadTimeSeries();
            break;
        case 'regional':
            await loadRegionalAnalysis();
            break;
        case 'articles':
            await loadArticles(1);
            break;
        case 'logs':
            await loadCollectionLogs();
            break;
    }
}

// === 概要タブ ===
async function loadCategoryChart() {
    try {
        const data = await fetchAPI(`/api/trends/categories?period=${currentPeriod}`);
        const ctx = document.getElementById('category-chart');
        if (!ctx) return;

        destroyChart('category');
        charts['category'] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.category),
                datasets: [{
                    data: data.map(d => d.total_frequency),
                    backgroundColor: data.map(d => CATEGORY_COLORS[d.category] || '#95a5a6'),
                    borderWidth: 2,
                    borderColor: '#fff',
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { font: { size: 12 } },
                    },
                    title: {
                        display: true,
                        text: 'カテゴリ別キーワード分布',
                        font: { size: 15, weight: 'bold' },
                    },
                },
            },
        });
    } catch (e) {
        console.error('カテゴリチャートエラー:', e);
    }
}

async function loadTopKeywords() {
    try {
        const data = await fetchAPI(`/api/trends/keywords?period=${currentPeriod}&limit=15`);
        const container = document.getElementById('keyword-ranking');
        if (!container) return;

        if (data.length === 0) {
            container.innerHTML = '<div class="loading">データがありません。「データ収集」ボタンで収集を開始してください。</div>';
            return;
        }

        const maxCount = data[0].total_frequency;
        container.innerHTML = `<ul class="keyword-list">${
            data.map((item, i) => `
                <li class="keyword-item">
                    <span class="keyword-rank ${i < 3 ? 'top3' : ''}">${i + 1}</span>
                    <div class="keyword-info">
                        <div class="keyword-name">${escapeHtml(item.keyword)}</div>
                        <div class="keyword-category">${escapeHtml(item.category)}</div>
                    </div>
                    <div class="keyword-bar">
                        <div class="keyword-bar-fill" style="width: ${(item.total_frequency / maxCount * 100).toFixed(1)}%"></div>
                    </div>
                    <span class="keyword-count">${item.total_frequency}</span>
                </li>
            `).join('')
        }</ul>`;
    } catch (e) {
        console.error('キーワードランキングエラー:', e);
    }
}

// === シミュレーションタブ ===
async function loadSimulationTrends() {
    try {
        const data = await fetchAPI(`/api/trends/simulation?period=${currentPeriod}`);
        const ctx = document.getElementById('simulation-chart');
        if (!ctx) return;

        const keywords = data.keywords || [];

        destroyChart('simulation');

        if (keywords.length === 0) {
            document.getElementById('simulation-detail').innerHTML =
                '<div class="loading">データがありません</div>';
            return;
        }

        // 横棒グラフ
        charts['simulation'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: keywords.slice(0, 15).map(k => k.keyword),
                datasets: [{
                    label: '出現頻度',
                    data: keywords.slice(0, 15).map(k => k.total_frequency),
                    backgroundColor: COLORS.slice(0, 15),
                    borderWidth: 0,
                    borderRadius: 4,
                }],
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: '数値解析・シミュレーション関連キーワードランキング',
                        font: { size: 15, weight: 'bold' },
                    },
                },
                scales: {
                    x: { beginAtZero: true },
                },
            },
        });

        // 詳細テーブル
        const detail = document.getElementById('simulation-detail');
        if (detail) {
            detail.innerHTML = `
                <table class="log-table">
                    <thead>
                        <tr>
                            <th>キーワード</th>
                            <th>出現頻度</th>
                            <th>関連記事数</th>
                            <th>情報ソース数</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${keywords.map(k => `
                            <tr>
                                <td><strong>${escapeHtml(k.keyword)}</strong></td>
                                <td>${k.total_frequency}</td>
                                <td>${k.article_count}</td>
                                <td>${k.source_count}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }
    } catch (e) {
        console.error('シミュレーショントレンドエラー:', e);
    }
}

// === 時系列タブ ===
async function loadTimeSeries() {
    try {
        const data = await fetchAPI(`/api/trends/timeseries?period=${currentPeriod}`);
        const ctx = document.getElementById('timeseries-chart');
        if (!ctx) return;

        destroyChart('timeseries');

        const datasets = Object.entries(data.series || {}).map(([keyword, values], i) => ({
            label: keyword,
            data: values.map(v => ({ x: v.date, y: v.count })),
            borderColor: COLORS[i % COLORS.length],
            backgroundColor: COLORS[i % COLORS.length] + '20',
            fill: false,
            tension: 0.3,
            pointRadius: 3,
        }));

        if (datasets.length === 0) {
            ctx.parentElement.innerHTML = '<div class="loading">データがありません</div>';
            return;
        }

        charts['timeseries'] = new Chart(ctx, {
            type: 'line',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'キーワード出現頻度の時系列推移',
                        font: { size: 15, weight: 'bold' },
                    },
                    legend: {
                        position: 'bottom',
                        labels: { font: { size: 11 } },
                    },
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            displayFormats: { day: 'MM/dd' },
                        },
                    },
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: '出現頻度' },
                    },
                },
            },
        });
    } catch (e) {
        console.error('時系列エラー:', e);
    }
}

// === 地域別タブ ===
async function loadRegionalAnalysis() {
    try {
        const data = await fetchAPI(`/api/trends/regional?period=${currentPeriod}`);
        const container = document.getElementById('regional-grid');
        if (!container) return;

        if (data.length === 0) {
            container.innerHTML = '<div class="loading">データがありません</div>';
            return;
        }

        container.innerHTML = data.map(r => {
            const topCategory = Object.entries(r.categories || {})
                .sort((a, b) => b[1] - a[1])[0];
            return `
                <div class="region-card">
                    <div class="region-name">${escapeHtml(r.region)}</div>
                    <div class="region-count">${r.article_count}</div>
                    <div class="region-detail">記事数</div>
                    ${topCategory ? `<div class="region-detail" style="margin-top:4px;">注目: ${escapeHtml(topCategory[0])}</div>` : ''}
                </div>
            `;
        }).join('');

        // 地域別チャート
        const ctx = document.getElementById('regional-chart');
        if (ctx) {
            destroyChart('regional');
            charts['regional'] = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(r => r.region),
                    datasets: [{
                        label: '記事数',
                        data: data.map(r => r.article_count),
                        backgroundColor: COLORS.slice(0, data.length),
                        borderRadius: 4,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: '地域別記事収集数',
                            font: { size: 15, weight: 'bold' },
                        },
                        legend: { display: false },
                    },
                    scales: { y: { beginAtZero: true } },
                },
            });
        }
    } catch (e) {
        console.error('地域別分析エラー:', e);
    }
}

// === 記事一覧タブ ===
async function loadArticles(page) {
    try {
        const category = document.getElementById('article-category')?.value || '';
        const region = document.getElementById('article-region')?.value || '';
        let url = `/api/articles?period=${currentPeriod}&page=${page}&per_page=20`;
        if (category) url += `&category=${encodeURIComponent(category)}`;
        if (region) url += `&region=${encodeURIComponent(region)}`;

        const data = await fetchAPI(url);
        const container = document.getElementById('article-list');
        if (!container) return;

        if (data.articles.length === 0) {
            container.innerHTML = '<div class="loading">記事がありません</div>';
            return;
        }

        container.innerHTML = `
            <ul class="article-list">
                ${data.articles.map(a => `
                    <li class="article-item">
                        <div class="article-title">
                            <a href="${escapeHtml(a.url)}" target="_blank" rel="noopener">${escapeHtml(a.title)}</a>
                        </div>
                        <div class="article-meta">
                            <span class="article-tag">${escapeHtml(a.source)}</span>
                            ${a.category ? `<span class="article-tag">${escapeHtml(a.category)}</span>` : ''}
                            ${a.region ? `<span>${escapeHtml(a.region)}</span>` : ''}
                            <span>${a.collected_date || ''}</span>
                        </div>
                    </li>
                `).join('')}
            </ul>
        `;

        // ページネーション
        const pagDiv = document.getElementById('article-pagination');
        if (pagDiv && data.pages > 1) {
            let btns = '';
            const start = Math.max(1, page - 3);
            const end = Math.min(data.pages, page + 3);

            if (page > 1) btns += `<button onclick="loadArticles(${page - 1})">前</button>`;
            for (let i = start; i <= end; i++) {
                btns += `<button class="${i === page ? 'active' : ''}" onclick="loadArticles(${i})">${i}</button>`;
            }
            if (page < data.pages) btns += `<button onclick="loadArticles(${page + 1})">次</button>`;
            pagDiv.innerHTML = btns;
        }
    } catch (e) {
        console.error('記事一覧エラー:', e);
    }
}

// === 収集ログタブ ===
async function loadCollectionLogs() {
    try {
        const data = await fetchAPI('/api/collection/logs?limit=50');
        const container = document.getElementById('log-list');
        if (!container) return;

        if (data.length === 0) {
            container.innerHTML = '<div class="loading">収集ログがありません</div>';
            return;
        }

        container.innerHTML = `
            <table class="log-table">
                <thead>
                    <tr>
                        <th>ソース</th>
                        <th>開始日時</th>
                        <th>完了日時</th>
                        <th>収集数</th>
                        <th>状態</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(log => `
                        <tr>
                            <td>${escapeHtml(log.source)}</td>
                            <td>${log.started_at || ''}</td>
                            <td>${log.finished_at || '-'}</td>
                            <td>${log.articles_collected}</td>
                            <td>
                                <span class="status-badge status-${log.status}">
                                    ${statusLabel(log.status)}
                                </span>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (e) {
        console.error('収集ログエラー:', e);
    }
}

// === データ収集トリガー ===
async function triggerCollection() {
    const btn = document.getElementById('collect-btn');
    if (btn) {
        btn.disabled = true;
        btn.textContent = '収集中...';
    }

    try {
        await fetchAPI('/api/collect', { method: 'POST' });
        alert('データ収集を開始しました。完了までしばらくお待ちください。');
        // 30秒後にダッシュボードを再読み込み
        setTimeout(() => {
            loadDashboard();
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'データ収集';
            }
        }, 30000);
    } catch (e) {
        console.error('収集トリガーエラー:', e);
        alert('データ収集の開始に失敗しました。');
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'データ収集';
        }
    }
}

// === ユーティリティ ===
async function fetchAPI(url, options = {}) {
    const response = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    return response.json();
}

function destroyChart(key) {
    if (charts[key]) {
        charts[key].destroy();
        delete charts[key];
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function statusLabel(status) {
    const labels = {
        'completed': '完了',
        'running': '実行中',
        'error': 'エラー',
    };
    return labels[status] || status;
}
