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
    '河道計画・河道設計': '#1a5276',
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
        case 'market':
            await loadMarketTab();
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

// === マーケット分析タブ ===
async function loadMarketTab() {
    await Promise.all([
        loadMarketSummary(),
        loadKadouCategories(),
        loadNeedsAnalysis(),
        loadTechDemand(),
        loadMarketRegional(),
        loadMarketProjects(1),
    ]);
}

function formatAmount(yen) {
    if (!yen || yen === 0) return '-';
    if (yen >= 100000000) return (yen / 100000000).toFixed(1) + '億円';
    if (yen >= 10000) return (yen / 10000).toFixed(0) + '万円';
    return yen.toLocaleString() + '円';
}

async function loadMarketSummary() {
    try {
        const data = await fetchAPI(`/api/market/summary?period=${currentPeriod}`);

        document.getElementById('market-total-projects').textContent =
            data.total_projects.toLocaleString();
        document.getElementById('market-total-amount').textContent =
            formatAmount(data.total_amount);
        document.getElementById('market-avg-amount').textContent =
            formatAmount(data.avg_amount);
        document.getElementById('market-with-amount').textContent =
            data.projects_with_amount.toLocaleString();

        // 業務種別内訳
        const typeContainer = document.getElementById('market-type-breakdown');
        if (typeContainer) {
            if (data.by_business_type.length === 0) {
                typeContainer.innerHTML = '<div class="loading">業務種別データがありません</div>';
            } else {
                typeContainer.innerHTML = `
                    <table class="log-table">
                        <thead>
                            <tr>
                                <th>業務種別</th>
                                <th>件数</th>
                                <th>合計金額</th>
                                <th>平均金額</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.by_business_type.map(t => `
                                <tr>
                                    <td><strong>${escapeHtml(t.type)}</strong></td>
                                    <td>${t.count}</td>
                                    <td>${formatAmount(t.total_amount)}</td>
                                    <td>${formatAmount(t.avg_amount)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            }
        }
    } catch (e) {
        console.error('マーケットサマリーエラー:', e);
    }
}

async function loadKadouCategories() {
    try {
        const data = await fetchAPI(`/api/market/kadou-categories?period=${currentPeriod}`);
        const ctx = document.getElementById('kadou-category-chart');
        if (!ctx) return;

        destroyChart('kadou-category');

        if (data.length === 0) {
            ctx.parentElement.innerHTML = '<div class="loading">カテゴリデータがありません</div>';
            return;
        }

        charts['kadou-category'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.category),
                datasets: [
                    {
                        label: '件数',
                        data: data.map(d => d.count),
                        backgroundColor: COLORS.slice(0, data.length),
                        borderRadius: 4,
                        yAxisID: 'y',
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '河道業務サブカテゴリ別件数',
                        font: { size: 15, weight: 'bold' },
                    },
                    legend: { display: false },
                },
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: '件数' } },
                },
            },
        });
    } catch (e) {
        console.error('河道カテゴリエラー:', e);
    }
}

async function loadNeedsAnalysis() {
    try {
        const data = await fetchAPI(`/api/market/needs?period=${currentPeriod}`);

        // 河道キーワード横棒グラフ
        const ctx = document.getElementById('kadou-needs-chart');
        if (ctx && data.kadou_keywords && data.kadou_keywords.length > 0) {
            destroyChart('kadou-needs');
            const keywords = data.kadou_keywords.slice(0, 15);
            charts['kadou-needs'] = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: keywords.map(k => k.keyword),
                    datasets: [{
                        label: '出現頻度',
                        data: keywords.map(k => k.frequency),
                        backgroundColor: '#1a5276',
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
                            text: '河道計画・設計キーワード頻度ランキング',
                            font: { size: 15, weight: 'bold' },
                        },
                    },
                    scales: { x: { beginAtZero: true } },
                },
            });
        }

        // 共起キーワードリスト
        const coContainer = document.getElementById('co-keywords-list');
        if (coContainer) {
            const coKw = data.co_occurring_keywords || [];
            if (coKw.length === 0) {
                coContainer.innerHTML = '<div class="loading">共起キーワードデータがありません</div>';
            } else {
                const maxCount = coKw[0].article_count;
                coContainer.innerHTML = `<ul class="keyword-list">${
                    coKw.slice(0, 20).map((item, i) => `
                        <li class="keyword-item">
                            <span class="keyword-rank ${i < 3 ? 'top3' : ''}">${i + 1}</span>
                            <div class="keyword-info">
                                <div class="keyword-name">${escapeHtml(item.keyword)}</div>
                                <div class="keyword-category">${escapeHtml(item.category || '')}</div>
                            </div>
                            <div class="keyword-bar">
                                <div class="keyword-bar-fill" style="width: ${(item.article_count / maxCount * 100).toFixed(1)}%"></div>
                            </div>
                            <span class="keyword-count">${item.article_count}件</span>
                        </li>
                    `).join('')
                }</ul>`;
            }
        }
    } catch (e) {
        console.error('ニーズ分析エラー:', e);
    }
}

async function loadTechDemand() {
    try {
        const data = await fetchAPI(`/api/market/technology?period=${currentPeriod}`);

        // 技術キーワードチャート
        const ctx = document.getElementById('tech-demand-chart');
        if (ctx) {
            destroyChart('tech-demand');
            const techKw = data.technology_keywords || [];

            if (techKw.length === 0) {
                ctx.parentElement.innerHTML = '<div class="loading">技術データがありません</div>';
            } else {
                // カテゴリ別に色分け
                const bgColors = techKw.map(k =>
                    k.category === '数値解析・シミュレーション' ? '#2980b9' : '#27ae60'
                );
                charts['tech-demand'] = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: techKw.slice(0, 20).map(k => k.keyword),
                        datasets: [{
                            label: '関連案件数',
                            data: techKw.slice(0, 20).map(k => k.article_count),
                            backgroundColor: bgColors.slice(0, 20),
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
                                text: '河道計画・設計で求められる技術キーワード（青=数値解析 / 緑=先端技術）',
                                font: { size: 14, weight: 'bold' },
                            },
                        },
                        scales: { x: { beginAtZero: true, title: { display: true, text: '関連案件数' } } },
                    },
                });
            }
        }

        // 入札方式
        const methodContainer = document.getElementById('procurement-methods-list');
        if (methodContainer) {
            const methods = data.procurement_methods || [];
            if (methods.length === 0) {
                methodContainer.innerHTML = '<div class="loading">入札方式データがありません</div>';
            } else {
                methodContainer.innerHTML = `
                    <table class="log-table">
                        <thead>
                            <tr><th>入札方式</th><th>件数</th></tr>
                        </thead>
                        <tbody>
                            ${methods.map(m => `
                                <tr>
                                    <td>${escapeHtml(m.method)}</td>
                                    <td>${m.count}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            }
        }
    } catch (e) {
        console.error('技術需要分析エラー:', e);
    }
}

async function loadMarketRegional() {
    try {
        const data = await fetchAPI(`/api/market/regional?period=${currentPeriod}`);
        const ctx = document.getElementById('market-regional-chart');
        if (!ctx) return;

        destroyChart('market-regional');

        if (data.length === 0) {
            ctx.parentElement.innerHTML = '<div class="loading">地域別データがありません</div>';
            return;
        }

        charts['market-regional'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.region),
                datasets: [{
                    label: '案件数',
                    data: data.map(d => d.project_count),
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
                        text: '地域別 河道関連案件数',
                        font: { size: 15, weight: 'bold' },
                    },
                    legend: { display: false },
                },
                scales: { y: { beginAtZero: true } },
            },
        });
    } catch (e) {
        console.error('地域別マーケットエラー:', e);
    }
}

async function loadMarketProjects(page) {
    try {
        const data = await fetchAPI(`/api/market/projects?period=${currentPeriod}&page=${page}&per_page=20`);
        const container = document.getElementById('market-projects-list');
        if (!container) return;

        if (!data.projects || data.projects.length === 0) {
            container.innerHTML = '<div class="loading">河道関連の発注案件がありません</div>';
            return;
        }

        container.innerHTML = `
            <table class="log-table">
                <thead>
                    <tr>
                        <th>案件名</th>
                        <th>地域</th>
                        <th>河道カテゴリ</th>
                        <th>業務種別</th>
                        <th>予定価格</th>
                        <th>落札金額</th>
                        <th>収集日</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.projects.map(p => `
                        <tr>
                            <td><a href="${escapeHtml(p.url)}" target="_blank" rel="noopener" style="color:var(--primary);text-decoration:none;">${escapeHtml(p.title)}</a></td>
                            <td>${escapeHtml(p.region || '-')}</td>
                            <td>${escapeHtml(p.kadou_category || '-')}</td>
                            <td>${escapeHtml(p.business_type || '-')}</td>
                            <td>${formatAmount(p.estimated_amount)}</td>
                            <td style="color:${p.contract_amount ? 'var(--accent)' : 'inherit'};font-weight:${p.contract_amount ? '600' : 'normal'};">${formatAmount(p.contract_amount)}</td>
                            <td>${p.collected_date || '-'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        // ページネーション
        const pagDiv = document.getElementById('market-projects-pagination');
        if (pagDiv && data.pages > 1) {
            let btns = '';
            const start = Math.max(1, page - 3);
            const end = Math.min(data.pages, page + 3);

            if (page > 1) btns += `<button onclick="loadMarketProjects(${page - 1})">前</button>`;
            for (let i = start; i <= end; i++) {
                btns += `<button class="${i === page ? 'active' : ''}" onclick="loadMarketProjects(${i})">${i}</button>`;
            }
            if (page < data.pages) btns += `<button onclick="loadMarketProjects(${page + 1})">次</button>`;
            pagDiv.innerHTML = btns;
        } else if (pagDiv) {
            pagDiv.innerHTML = '';
        }
    } catch (e) {
        console.error('マーケット案件一覧エラー:', e);
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
