#!/usr/bin/env python3
"""
E-ITS Cyberplan Project Statistics Generator
Generates HTML statistics reports from git log data.

Usage:
    python3 stats_generator.py

Output:
    Creates stats_datetime_YYYYMMDD_HHMMSS.html and stats_datetime_YYYYMMDD_HHMMSS_et.html
"""
import subprocess
from collections import defaultdict
from datetime import datetime
import os

REPO_PATH = '/Users/kalle/proj/asiaat/eits_cyberplan'

def get_git_log():
    result = subprocess.run(
        ['git', 'log', '--format=%ai|%ae|%h|%s', '--numstat'],
        capture_output=True,
        text=True,
        cwd=REPO_PATH
    )
    return result.stdout

def parse_commits(content):
    commits = []
    current = None

    for line in content.split('\n'):
        line = line.rstrip()
        if not line:
            if current and current['lines']:
                commits.append(current)
                current = None
            continue

        parts = line.split('|')
        if len(parts) >= 4 and '+0300' in parts[0]:
            if current and current['lines']:
                commits.append(current)
            date_str = parts[0].split('+')[0].strip()
            author = parts[1].strip()
            hash_id = parts[2].strip()
            msg = '|'.join(parts[3:]).strip()
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                current = {'date': dt, 'author': author, 'hash': hash_id, 'msg': msg, 'lines': []}
            except:
                pass
        elif current and '\t' in line:
            parts = line.split('\t')
            if len(parts) == 3:
                try:
                    ins = int(parts[0]) if parts[0] != '-' else 0
                    dels = int(parts[1]) if parts[1] != '-' else 0
                    fn = parts[2].strip()
                    current['lines'].append((ins, dels, fn))
                except:
                    pass

    if current and current['lines']:
        commits.append(current)

    return commits

def aggregate_data(commits):
    daily = defaultdict(lambda: {'commits': 0, 'ins': 0, 'del': 0, 'modules': set()})
    module_data = defaultdict(lambda: {'ins': 0, 'del': 0, 'files': set()})
    action_counts = defaultdict(int)

    for c in commits:
        d = c['date'].strftime('%Y-%m-%d')
        daily[d]['commits'] += 1

        msg_lower = c['msg'].lower()
        if 'feat:' in msg_lower:
            action_counts['feat'] += 1
        elif 'fix:' in msg_lower:
            action_counts['fix'] += 1
        elif 'refactor:' in msg_lower:
            action_counts['refactor'] += 1
        elif 'merge' in msg_lower:
            action_counts['merge'] += 1
        elif 'docs:' in msg_lower:
            action_counts['docs'] += 1
        else:
            action_counts['other'] += 1

        for ins, dels, fn in c['lines']:
            daily[d]['ins'] += ins
            daily[d]['del'] += dels

            mod = 'other'
            if 'backend/app/api/v2' in fn:
                mod = 'backend/api'
            elif 'backend/app/services' in fn:
                mod = 'backend/services'
            elif 'backend/app/models' in fn:
                mod = 'backend/models'
            elif 'backend/alembic' in fn:
                mod = 'backend/alembic'
            elif 'backend/' in fn:
                mod = 'backend/other'
            elif 'frontend/src/pages' in fn:
                mod = 'frontend/pages'
            elif 'frontend/src/components' in fn:
                mod = 'frontend/components'
            elif 'frontend/src/lib' in fn:
                mod = 'frontend/lib'
            elif 'frontend/' in fn:
                mod = 'frontend/other'

            module_data[mod]['ins'] += ins
            module_data[mod]['del'] += dels
            module_data[mod]['files'].add(fn.split('/')[-1])
            daily[d]['modules'].add(mod)

    return daily, module_data, action_counts

def get_module_class(mod):
    mapping = {
        'backend/api': 'module-backend-api',
        'backend/services': 'module-backend-services',
        'backend/models': 'module-backend-models',
        'backend/alembic': 'module-backend-alembic',
        'backend/other': 'module-backend-other',
        'frontend/pages': 'module-frontend-pages',
        'frontend/components': 'module-frontend-components',
        'frontend/lib': 'module-frontend-lib',
        'frontend/other': 'module-frontend-other',
        'other': 'module-other',
    }
    return mapping.get(mod, 'module-other')

def generate_html(daily, module_data, action_counts, lang='et'):
    is_et = lang == 'et'
    
    labels = {
        'title': 'E-ITS Cyberplan',
        'subtitle_et': 'Projekti Arengu Statistika | Mai 2026',
        'subtitle_en': 'Project Development Statistics | May 2026',
        'commits': 'Kommiteid' if is_et else 'Commits',
        'insertions': 'Lisatud ridu' if is_et else 'Lines Added',
        'deletions': 'Kustutatud ridu' if is_et else 'Lines Deleted',
        'net': 'Neto kasv' if is_et else 'Net Growth',
        'days': 'Aktiivset päeva' if is_et else 'Active Days',
        'daily_activity': 'Päevane tegevus' if is_et else 'Daily Activity',
        'module_dist': 'Moodulite jaotus' if is_et else 'Module Distribution',
        'commit_types': 'Kommittide tüübid' if is_et else 'Commit Actions',
        'module_breakdown': 'Moodulite jaotus' if is_et else 'Module Breakdown',
        'codebase_growth': 'Koodibaasi kasv' if is_et else 'Codebase Growth',
        'cumulative': 'Kumulatiivsed read' if is_et else 'Cumulative Lines',
        'daily_change': 'Päevane muutus' if is_et else 'Daily Change',
        'date': 'Kuupäev' if is_et else 'Date',
        'added': 'Lisatud' if is_et else 'Added',
        'deleted': 'Kustutatud' if is_et else 'Deleted',
        'net_change': 'Netomuutus' if is_et else 'Net Change',
        'modules': 'Moodulid' if is_et else 'Modules',
        'files': 'Faile' if is_et else 'Files',
    }
    
    dates = sorted(daily.keys(), reverse=True)
    cum = 0
    growth_data = []
    for d in sorted(dates):
        net = daily[d]['ins'] - daily[d]['del']
        cum += net
        growth_data.append({'date': d, 'cumulative': cum, 'net': net})
    
    total_ins = sum(daily[d]['ins'] for d in daily)
    total_del = sum(daily[d]['del'] for d in daily)
    total_commits = sum(daily[d]['commits'] for d in daily)
    net_total = total_ins - total_del
    
    date_labels = str([d[5:] for d in sorted(dates)])
    commit_values = str([daily[d]['commits'] for d in sorted(dates)])
    growth_values = str([g['cumulative'] for g in growth_data])
    
    sorted_mods = sorted(module_data.keys(), key=lambda x: module_data[x]['ins'], reverse=True)
    mod_labels = str(sorted_mods)
    mod_values = str([module_data[m]['ins'] - module_data[m]['del'] for m in sorted_mods])
    
    feat_pct = 100.0
    fix_pct = action_counts['fix'] / action_counts['feat'] * 100 if action_counts['feat'] > 0 else 0
    other_pct = action_counts['other'] / action_counts['feat'] * 100 if action_counts['feat'] > 0 else 0
    ref_pct = action_counts['refactor'] / action_counts['feat'] * 100 if action_counts['feat'] > 0 else 0
    
    subtitle = labels['subtitle_et'] if is_et else labels['subtitle_en']
    lang_attr = 'et' if is_et else 'en'
    cum_label = labels['cumulative']
    
    generated = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    
    # Build daily rows HTML
    daily_rows = ''
    for d in dates:
        net = daily[d]['ins'] - daily[d]['del']
        mods = ','.join(sorted(daily[d]['modules']))
        daily_rows += f'<tr><td>{d}</td><td><span class="commits-badge">{daily[d]["commits"]}</span></td><td>{daily[d]["ins"]:,}</td><td>{daily[d]["del"]:,}</td><td class="net-positive">+{net:,}</td><td>{mods}</td></tr>\n'
    
    # Build module rows HTML
    mod_rows = ''
    for mod in sorted_mods:
        ins = module_data[mod]['ins']
        dels = module_data[mod]['del']
        net = ins - dels
        files = len(module_data[mod]['files'])
        tag_class = get_module_class(mod)
        mod_rows += f'<tr><td><span class="module-tag {tag_class}">{mod}</span></td><td>{ins:,}</td><td>{dels:,}</td><td class="net-positive">+{net:,}</td><td>{files}</td></tr>\n'
    
    # Build growth rows HTML
    growth_rows = ''
    for g in growth_data:
        growth_rows += f'<tr><td>{g["date"]}</td><td>{g["cumulative"]:,}</td><td class="net-positive">+{g["net"]:,}</td></tr>\n'
    
    html = f'''<!DOCTYPE html>
<html lang="{lang_attr}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{labels['title']} {"Statistika" if is_et else "Statistics"}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {{ --bg-primary: #ffffff; --bg-secondary: #f8fafc; --bg-card: #f1f5f9; --text-primary: #0f172a; --text-secondary: #64748b; --accent-blue: #3b82f6; --accent-green: #16a34a; --accent-red: #dc2626; --accent-purple: #9333ea; --accent-yellow: #ca8a04; --accent-cyan: #0891b2; --accent-orange: #ea580c; --border-color: #e2e8f0; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg-primary); color: var(--text-primary); line-height: 1.6; padding: 2rem; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
        .subtitle {{ color: var(--text-secondary); margin-bottom: 2rem; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .stat-card {{ background: var(--bg-card); border-radius: 12px; padding: 1.5rem; text-align: center; border: 1px solid var(--border-color); transition: transform 0.2s; }}
        .stat-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .stat-card .value {{ font-size: 2.5rem; font-weight: 700; margin-bottom: 0.25rem; }}
        .stat-card .label {{ color: var(--text-secondary); font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        .stat-card.commits .value {{ color: var(--accent-blue); }}
        .stat-card.insertions .value {{ color: var(--accent-green); }}
        .stat-card.deletions .value {{ color: var(--accent-red); }}
        .stat-card.net .value {{ color: var(--accent-purple); }}
        .stat-card.days .value {{ color: var(--accent-yellow); }}
        .section {{ background: var(--bg-card); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid var(--border-color); }}
        .section-title {{ font-size: 1.25rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }}
        .section-title::before {{ content: ''; width: 4px; height: 1.25rem; background: var(--accent-blue); border-radius: 2px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
        th {{ text-align: left; padding: 0.75rem 1rem; background: var(--bg-secondary); color: var(--text-secondary); text-transform: uppercase; font-size: 0.75rem; border-bottom: 1px solid var(--border-color); }}
        td {{ padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-color); }}
        tr:hover {{ background: rgba(0,0,0,0.02); }}
        .commits-badge {{ background: var(--accent-blue); color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: 600; font-size: 0.75rem; }}
        .net-positive {{ color: var(--accent-green); }}
        .module-tag {{ display: inline-block; background: var(--bg-secondary); padding: 0.125rem 0.5rem; border-radius: 4px; margin: 0.125rem; font-size: 0.7rem; }}
        .module-backend-api {{ background: rgba(59, 130, 246, 0.1); color: var(--accent-blue); }}
        .module-backend-services {{ background: rgba(6, 182, 212, 0.1); color: var(--accent-cyan); }}
        .module-backend-models {{ background: rgba(22, 163, 74, 0.1); color: var(--accent-green); }}
        .module-backend-alembic {{ background: rgba(202, 138, 4, 0.1); color: var(--accent-yellow); }}
        .module-frontend-pages {{ background: rgba(147, 51, 234, 0.1); color: var(--accent-purple); }}
        .module-frontend-components {{ background: rgba(234, 88, 12, 0.1); color: var(--accent-orange); }}
        .module-frontend-lib {{ background: rgba(236, 72, 153, 0.1); color: #db2777; }}
        .module-other {{ background: rgba(100, 116, 139, 0.1); color: var(--text-secondary); }}
        .chart-container {{ position: relative; height: 300px; margin-bottom: 1rem; }}
        .chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }}
        @media (max-width: 1024px) {{ .chart-row {{ grid-template-columns: 1fr; }} }}
        .action-bar {{ display: flex; align-items: center; gap: 0.5rem; margin: 0.25rem 0; }}
        .action-label {{ min-width: 100px; font-weight: 600; }}
        .action-bar-fill {{ height: 24px; border-radius: 4px; display: flex; align-items: center; padding: 0 0.75rem; font-size: 0.75rem; font-weight: 600; min-width: 60px; color: white; }}
        .action-feat .action-bar-fill {{ background: var(--accent-blue); }}
        .action-fix .action-bar-fill {{ background: var(--accent-red); }}
        .action-other .action-bar-fill {{ background: var(--text-secondary); }}
        .action-refactor .action-bar-fill {{ background: var(--accent-purple); }}
        .progress-bar {{ height: 8px; background: var(--border-color); border-radius: 4px; overflow: hidden; margin: 0.5rem 0; }}
        .progress-bar-fill {{ height: 100%; border-radius: 4px; }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
        @media (max-width: 768px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
        .generated-at {{ text-align: center; color: var(--text-secondary); font-size: 0.75rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border-color); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{labels['title']}</h1>
        <p class="subtitle">{subtitle}</p>

        <div class="summary-grid">
            <div class="stat-card commits"><div class="value">{total_commits}</div><div class="label">{labels['commits']}</div></div>
            <div class="stat-card insertions"><div class="value">{total_ins:,}</div><div class="label">{labels['insertions']}</div></div>
            <div class="stat-card deletions"><div class="value">{total_del:,}</div><div class="label">{labels['deletions']}</div></div>
            <div class="stat-card net"><div class="value">+{net_total:,}</div><div class="label">{labels['net']}</div></div>
            <div class="stat-card days"><div class="value">{len(daily)}</div><div class="label">{labels['days']}</div></div>
        </div>

        <div class="chart-row">
            <div class="section">
                <div class="section-title">{labels['daily_activity']}</div>
                <div class="chart-container"><canvas id="commitsChart"></canvas></div>
            </div>
            <div class="section">
                <div class="section-title">{labels['codebase_growth']}</div>
                <div class="chart-container"><canvas id="growthChart"></canvas></div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">{labels['module_dist']}</div>
            <div class="chart-container" style="height: 250px;"><canvas id="moduleChart"></canvas></div>
        </div>

        <div class="section">
            <div class="section-title">{labels['commit_types']}</div>
            <div style="padding: 1rem 0;">
                <div class="action-bar action-feat">
                    <span class="action-label">feat:</span>
                    <div class="progress-bar" style="flex: 1;"><div class="progress-bar-fill" style="width: 100%; background: var(--accent-blue);"></div></div>
                    <span class="action-bar-fill">{action_counts['feat']}</span>
                </div>
                <div class="action-bar action-fix">
                    <span class="action-label">fix:</span>
                    <div class="progress-bar" style="flex: 1;"><div class="progress-bar-fill" style="width: {fix_pct:.1f}%; background: var(--accent-red);"></div></div>
                    <span class="action-bar-fill">{action_counts['fix']}</span>
                </div>
                <div class="action-bar action-other">
                    <span class="action-label">muu:</span>
                    <div class="progress-bar" style="flex: 1;"><div class="progress-bar-fill" style="width: {other_pct:.1f}%; background: var(--text-secondary);"></div></div>
                    <span class="action-bar-fill">{action_counts['other']}</span>
                </div>
                <div class="action-bar action-refactor">
                    <span class="action-label">refactor:</span>
                    <div class="progress-bar" style="flex: 1;"><div class="progress-bar-fill" style="width: {ref_pct:.1f}%; background: var(--accent-purple);"></div></div>
                    <span class="action-bar-fill">{action_counts['refactor']}</span>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">{labels['daily_activity']}</div>
            <table>
                <thead>
                    <tr>
                        <th>{labels['date']}</th>
                        <th>Commits</th>
                        <th>{labels['added']}</th>
                        <th>{labels['deleted']}</th>
                        <th>{labels['net_change']}</th>
                        <th>{labels['modules']}</th>
                    </tr>
                </thead>
                <tbody>
{daily_rows}                </tbody>
            </table>
        </div>

        <div class="grid-2">
            <div class="section">
                <div class="section-title">{labels['module_breakdown']}</div>
                <table>
                    <thead>
                        <tr>
                            <th>Moodul</th>
                            <th>{labels['added']}</th>
                            <th>{labels['deleted']}</th>
                            <th>{labels['net_change']}</th>
                            <th>{labels['files']}</th>
                        </tr>
                    </thead>
                    <tbody>
{mod_rows}                    </tbody>
                </table>
            </div>

            <div class="section">
                <div class="section-title">{labels['codebase_growth']}</div>
                <table>
                    <thead>
                        <tr>
                            <th>{labels['date']}</th>
                            <th>{labels['cumulative']}</th>
                            <th>{labels['daily_change']}</th>
                        </tr>
                    </thead>
                    <tbody>
{growth_rows}                    </tbody>
                </table>
            </div>
        </div>

        <div class="generated-at">
            Genereeritud {generated} | E-ITS Cyberplan Statistics
        </div>
    </div>

    <script>
        const commitsCtx = document.getElementById('commitsChart').getContext('2d');
        new Chart(commitsCtx, {{
            type: 'bar',
            data: {{
                labels: {date_labels},
                datasets: [{{
                    label: 'Commits',
                    data: {commit_values},
                    backgroundColor: 'rgba(59, 130, 246, 0.7)',
                    borderColor: '#3b82f6',
                    borderWidth: 1,
                    borderRadius: 4,
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{ beginAtZero: true, grid: {{ color: '#e2e8f0' }}, ticks: {{ color: '#64748b' }} }},
                    x: {{ grid: {{ display: false }}, ticks: {{ color: '#64748b' }} }}
                }}
            }}
        }});

        const growthCtx = document.getElementById('growthChart').getContext('2d');
        new Chart(growthCtx, {{
            type: 'line',
            data: {{
                labels: {date_labels},
                datasets: [{{
                    label: "{cum_label}",
                    data: {growth_values},
                    borderColor: '#16a34a',
                    backgroundColor: 'rgba(22, 163, 74, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: '#16a34a',
                    pointRadius: 4,
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{ grid: {{ color: '#e2e8f0' }}, ticks: {{ color: '#64748b' }} }},
                    x: {{ grid: {{ display: false }}, ticks: {{ color: '#64748b' }} }}
                }}
            }}
        }});

        const moduleCtx = document.getElementById('moduleChart').getContext('2d');
        new Chart(moduleCtx, {{
            type: 'doughnut',
            data: {{
                labels: {mod_labels},
                datasets: [{{
                    data: {mod_values},
                    backgroundColor: ['#64748b', '#9333ea', '#3b82f6', '#f97316', '#94a3b8', '#ea580c', '#db2777', '#ca8a04', '#16a34a', '#0891b2'],
                    borderWidth: 0,
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'right', labels: {{ color: '#0f172a', padding: 12, font: {{ size: 11 }} }} }}
                }}
            }}
        }});
    </script>
</body>
</html>'''
    
    return html

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Generating E-ITS Cyberplan statistics...")
    
    content = get_git_log()
    commits = parse_commits(content)
    daily, module_data, action_counts = aggregate_data(commits)
    
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Estonian version
    html_et = generate_html(daily, module_data, action_counts, 'et')
    filename_et = os.path.join(script_dir, f'stats_datetime_{now}_et.html')
    with open(filename_et, 'w', encoding='utf-8') as f:
        f.write(html_et)
    print(f"  Created: {filename_et}")
    
    # English version
    html_en = generate_html(daily, module_data, action_counts, 'en')
    filename_en = os.path.join(script_dir, f'stats_datetime_{now}.html')
    with open(filename_en, 'w', encoding='utf-8') as f:
        f.write(html_en)
    print(f"  Created: {filename_en}")
    
    print("\nDone!")
    print(f"  - {len(commits)} commits processed")
    print(f"  - {len(daily)} days")
    print(f"  - {len(module_data)} modules")

if __name__ == '__main__':
    main()