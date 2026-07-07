import os
import glob
import statistics
import re
from datetime import datetime

WORKFLOW_DIR = os.path.expanduser("~/blueprint-workflows/claude-commands")
GROK_SKILLS_DIR = os.path.expanduser("~/.grok/bundled/skills")
OUTPUT_HTML = os.path.expanduser("~/blueprint-workflows/docs/workflow_length_analysis.html")

def count_syllables(word):
    word = word.lower()
    if len(word) <= 3:
        return 1
    word = re.sub(r'[^a-z]', '', word)
    if not word:
        return 1
    count = len(re.findall(r'[aeiouy]+', word))
    if word.endswith('e') and not word.endswith('le') and count > 1:
        count -= 1
    return max(1, count)

def compute_readability(text):
    words = text.split()
    if not words: return 0
    # Simple sentence splitting
    sentences = len(re.split(r'[.!?]+', text))
    if sentences == 0: sentences = 1
    syllables = sum(count_syllables(w) for w in words)
    grade = 0.39 * (len(words) / sentences) + 11.8 * (syllables / len(words)) - 15.59
    return max(0, min(grade, 25))

def compute_execution_density(text):
    code_blocks = re.findall(r'```.*?```', text, re.DOTALL)
    code_text = " ".join(code_blocks)
    code_words = len(code_text.split())
    total_words = len(text.split())
    return (code_words / total_words * 100) if total_words > 0 else 0

def count_keywords(text, pattern):
    return len(re.findall(pattern, text, re.IGNORECASE))

def normalize_header(name):
    if name == 'Frontmatter / Preamble':
        return 'frontmatter'
    raw_name = name.replace('#', '').strip().lower()
    if 'anti-hallucination' in raw_name or 'tool-call discipline' in raw_name:
        return 'tool-call discipline'
    if 'strict rules' in raw_name:
        return 'strict rules'
    if 'change log' in raw_name:
        return 'change log'
    if 'glossary' in raw_name:
        return 'glossary'
    if 'setup' in raw_name and 'cleanup' not in raw_name:
        return 'setup'
    if 'invocation' in raw_name:
        return 'invocation'
    if 'todo scaffold' in raw_name:
        return 'todo scaffold'
    if 'persona injection' in raw_name:
        return 'persona injection'
    
    clean_name = re.sub(r'^(step|phase)\s*[\d\w]+\s*[:\—-]\s*', '', raw_name)
    clean_name = re.sub(r'^\d+\.\s*', '', clean_name)
    return clean_name.strip()

def parse_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    total_lines = len(lines)
    
    in_frontmatter = False
    frontmatter_lines = 0
    if total_lines > 0 and lines[0].strip() == '---':
        in_frontmatter = True
        frontmatter_lines += 1
        for line in lines[1:]:
            frontmatter_lines += 1
            if line.strip() == '---':
                in_frontmatter = False
                break
    
    if in_frontmatter:
        frontmatter_lines = 0
        
    body_lines = total_lines - frontmatter_lines
    content = "".join(lines)
    words = len(content.split())
    
    readability = compute_readability(content)
    exec_density = compute_execution_density(content)
    
    # Logic density / 1000 words
    branching_hits = count_keywords(content, r'\b(if|elif|else|fallback|degrade|degradation|cascade|skip|conditional|retry|catch|error)\b')
    subagent_hits = count_keywords(content, r'\b(launch|subagent|agent|manifest|\.json|state|payload|orchestrator|implementer|reviewer)\b')
    
    branching_density = (branching_hits / (words / 1000)) if words > 0 else 0
    subagent_density = (subagent_hits / (words / 1000)) if words > 0 else 0

    sections = []
    current_section_name = "Frontmatter / Preamble"
    current_section_lines = 0
    current_section_words = 0
    header_pattern = re.compile(r'^(#{1,6})\s+(.*)')
    
    for line in lines:
        match = header_pattern.match(line)
        if match:
            if current_section_lines > 0 or current_section_words > 0:
                sections.append({
                    'name': current_section_name,
                    'lines': current_section_lines,
                    'words': current_section_words
                })
            current_section_name = match.group(0).strip()
            current_section_lines = 0
            current_section_words = 0
            
        current_section_lines += 1
        current_section_words += len(line.split())
        
    if current_section_lines > 0 or current_section_words > 0:
        sections.append({
            'name': current_section_name,
            'lines': current_section_lines,
            'words': current_section_words
        })
    
    return {
        'name': os.path.basename(filepath),
        'filepath': filepath,
        'total_lines': total_lines,
        'body_lines': body_lines,
        'words': words,
        'readability': readability,
        'exec_density': exec_density,
        'branching_density': branching_density,
        'subagent_density': subagent_density,
        'sections': sections
    }

def compute_stats(data_list):
    total_files = len(data_list)
    if total_files == 0:
        return None
    
    metrics = ['total_lines', 'body_lines', 'words', 'readability', 'exec_density', 'branching_density', 'subagent_density']
    stats = {'total_files': total_files}
    
    for m in metrics:
        vals = [d[m] for d in data_list]
        stats[m] = {
            'avg': statistics.mean(vals),
            'median': statistics.median(vals),
            'stdev': statistics.stdev(vals) if total_files > 1 else 0,
            'max': max(vals),
            'min': min(vals)
        }
    return stats

def analyze_patterns(data_list):
    header_freq = {}
    total_files = len(data_list)
    
    for row in data_list:
        seen_in_file = set()
        for sec in row['sections']:
            norm_name = normalize_header(sec['name'])
            seen_in_file.add(norm_name)
            
        for h in seen_in_file:
            header_freq[h] = header_freq.get(h, 0) + 1
            
    core_outline = {h: f for h, f in header_freq.items() if f >= (total_files * 0.4) and f > 1}
    sorted_core = sorted(core_outline.items(), key=lambda x: x[1], reverse=True)
    
    imbalance_scores = []
    
    for row in data_list:
        file_headers = set()
        for sec in row['sections']:
            file_headers.add(normalize_header(sec['name']))
            
        if core_outline:
            conformity = len(file_headers.intersection(set(core_outline.keys()))) / len(core_outline) * 100
        else:
            conformity = 0
        row['conformity_score'] = conformity
        
        pcts = [(sec['words'] / row['words'] * 100) if row['words'] > 0 else 0 for sec in row['sections']]
        row['imbalance_score'] = statistics.stdev(pcts) if len(pcts) > 1 else 0
        row['max_section_pct'] = max(pcts) if pcts else 0
        imbalance_scores.append(row['imbalance_score'])

    return sorted_core, statistics.mean(imbalance_scores) if imbalance_scores else 0

def render_behemoth(b):
    html = f"""
    <div class="summary-card">
        <h4>{b['name']} <span class="note">({b['words']} words | Flesch-Kincaid: {b['readability']:.1f})</span></h4>
        <table>
            <tr><th>Section Header</th><th>Lines</th><th>Words</th><th>% of Total Words</th></tr>
"""
    for sec in b['sections']:
        pct = (sec['words'] / b['words']) * 100 if b['words'] > 0 else 0
        highlight_class = 'highlight' if pct > 15 else ''
        safe_name = sec['name'].replace('<', '&lt;').replace('>', '&gt;')
        html += f"""<tr class="{highlight_class}">
            <td>{safe_name}</td><td>{sec['lines']}</td><td>{sec['words']}</td><td>{pct:.1f}%</td>
        </tr>"""
    html += "</table></div>"
    return html

def generate_html(sov_data, grok_data):
    sov_stats = compute_stats(sov_data)
    grok_stats = compute_stats(grok_data)

    sov_core, sov_avg_imb = analyze_patterns(sov_data)
    grok_core, grok_avg_imb = analyze_patterns(grok_data)

    sov_data.sort(key=lambda x: x['words'], reverse=True)
    grok_data.sort(key=lambda x: x['words'], reverse=True)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sovereign vs Grok: Architectural Analysis</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; color: #e0e0e0; background-color: #121212; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1, h2 {{ color: #ffffff; border-bottom: 2px solid #333; padding-bottom: 5px; margin-top: 40px; }}
        h3 {{ color: #cccccc; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; box-shadow: 0 1px 3px rgba(0,0,0,0.5); background: #1e1e1e; }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #333; }}
        th {{ background-color: #2c2c2c; font-weight: 600; color: #ffffff; position: sticky; top: 0; }}
        tr:hover {{ background-color: #2a2a2a; }}
        .summary-card {{ background: #1e1e1e; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #333; }}
        .timestamp {{ color: #888; font-size: 0.9em; margin-top: -10px; margin-bottom: 30px; }}
        .highlight {{ background-color: #3b2a00; }}
        .highlight td:first-child {{ font-weight: bold; color: #ffcc00; }}
        .note {{ font-size: 0.9em; color: #aaa; font-style: italic; }}
        .flex-container {{ display: flex; gap: 20px; flex-wrap: wrap; }}
        .flex-child {{ flex: 1; min-width: 300px; }}
    </style>
</head>
<body>
    <h1>Sovereign vs Grok: Architectural Analysis</h1>
    <p class="timestamp">Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
"""

    # --- SECTION 1: HIGH LEVEL SUMMARY ---
    html += """
    <h2 id="summary">Section 1: High-Level Summary Statistics</h2>
    <div class="summary-card">
        <table>
            <tr>
                <th>Metric (Averages)</th>
                <th>Sovereign Suite (N={sov})</th>
                <th>Grok Build (N={grok})</th>
            </tr>
            <tr>
                <td><strong>Word Count</strong></td>
                <td>{sov_w:.0f} words</td>
                <td>{grok_w:.0f} words</td>
            </tr>
            <tr>
                <td><strong>Total Lines</strong></td>
                <td>{sov_l:.0f} lines</td>
                <td>{grok_l:.0f} lines</td>
            </tr>
            <tr>
                <td><strong>Avg. Structural Imbalance Score</strong><br><span class="note">Lower is more balanced/flat</span></td>
                <td>{sov_imb:.2f}</td>
                <td>{grok_imb:.2f}</td>
            </tr>
        </table>
    </div>
    """.format(
        sov=sov_stats['total_files'], grok=grok_stats['total_files'] if grok_stats else 0,
        sov_w=sov_stats['words']['avg'], grok_w=grok_stats['words']['avg'] if grok_stats else 0,
        sov_l=sov_stats['total_lines']['avg'], grok_l=grok_stats['total_lines']['avg'] if grok_stats else 0,
        sov_imb=sov_avg_imb, grok_imb=grok_avg_imb
    )

    # --- SECTION 2: BEHAVIORAL MECHANICS ---
    html += """
    <h2 id="behavior">Section 2: Behavioral Mechanics & Logic</h2>
    <div class="summary-card">
        <p>Analyzing the raw executable nature of the text, cognitive load, and logical structures.</p>
        <table>
            <tr>
                <th>Behavioral Metric (Averages)</th>
                <th>Sovereign</th>
                <th>Grok Build</th>
            </tr>
            <tr>
                <td><strong>Readability (Flesch-Kincaid Grade Level)</strong><br><span class="note">Higher = denser, more complex sentence structure. Lower = declarative, direct.</span></td>
                <td>{sov_r:.1f}</td>
                <td>{grok_r:.1f}</td>
            </tr>
            <tr>
                <td><strong>Execution Density</strong><br><span class="note">% of words existing inside code blocks (commands, JSON, Python, etc.)</span></td>
                <td>{sov_e:.1f}%</td>
                <td>{grok_e:.1f}%</td>
            </tr>
            <tr>
                <td><strong>Branching Logic Density</strong><br><span class="note">Mentions of if/else/fallback/error per 1000 words.</span></td>
                <td>{sov_b:.1f}</td>
                <td>{grok_b:.1f}</td>
            </tr>
            <tr>
                <td><strong>Subagent / State Density</strong><br><span class="note">Mentions of payload, state, launch, JSON, implementer per 1000 words.</span></td>
                <td>{sov_s:.1f}</td>
                <td>{grok_s:.1f}</td>
            </tr>
        </table>
    </div>
    """.format(
        sov_r=sov_stats['readability']['avg'], grok_r=grok_stats['readability']['avg'] if grok_stats else 0,
        sov_e=sov_stats['exec_density']['avg'], grok_e=grok_stats['exec_density']['avg'] if grok_stats else 0,
        sov_b=sov_stats['branching_density']['avg'], grok_b=grok_stats['branching_density']['avg'] if grok_stats else 0,
        sov_s=sov_stats['subagent_density']['avg'], grok_s=grok_stats['subagent_density']['avg'] if grok_stats else 0
    )

    # --- SECTION 3: PATTERNS ---
    html += """
    <h2 id="patterns">Section 3: Core Templating Patterns</h2>
    <p>Headers appearing in >40% of workflows, defining the implicit "Charter" vs "API" structure.</p>
    <div class="flex-container">
        <div class="flex-child summary-card">
            <h3>Sovereign Core Pattern</h3>
            <ul>
"""
    for header, count in sov_core:
        html += f"<li><strong>{header}</strong> ({count} files)</li>"
    html += """
            </ul>
        </div>
        <div class="flex-child summary-card">
            <h3>Grok Build Core Pattern</h3>
            <ul>
"""
    if grok_core:
        for header, count in grok_core:
            html += f"<li><strong>{header}</strong> ({count} files)</li>"
    html += """
            </ul>
        </div>
    </div>
"""

    # --- SECTION 4: DEEP DIVES ---
    html += """
    <h2 id="behemoths">Section 4: The Behemoths Deep Dive</h2>
    <p class="note">Highlighting applied to any single section that consumes > 15% of the total document word count.</p>
    """
    
    if grok_data:
        html += "<h3>Top Grok Files</h3>"
        for b in grok_data[:2]:
            html += render_behemoth(b)
            
    html += "<h3>Top Sovereign Files</h3>"
    for b in sov_data[:4]:
        html += render_behemoth(b)

    # --- SECTION 5: TABLES ---
    html += """
    <h2 id="tables">Section 5: Full Suite Data Tables</h2>
    """
    
    def render_table(title, data):
        data_sorted = sorted(data, key=lambda x: x['words'], reverse=True)
        res = f"<h3>{title}</h3><table><tr><th>File</th><th>Words</th><th>Readability Grade</th><th>Imbalance Score</th><th>Conformity</th></tr>"
        for row in data_sorted:
            name = row['name'] if 'blueprint-workflows' in row['filepath'] else row['filepath'].split('.grok/bundled/skills/')[-1]
            res += f"<tr><td><strong>{name}</strong></td><td>{row['words']}</td><td>{row['readability']:.1f}</td><td>{row['imbalance_score']:.2f}</td><td>{row['conformity_score']:.0f}%</td></tr>"
        res += "</table>"
        return res

    html += render_table("Sovereign Workflows (All)", sov_data)
    if grok_data:
        html += render_table("Grok Build Skills (All)", grok_data)

    html += """
</body>
</html>"""
    
    return html

def main():
    sov_data = []
    if os.path.exists(WORKFLOW_DIR):
        md_files = glob.glob(os.path.join(WORKFLOW_DIR, "*.md"))
        for f in md_files:
            if os.path.basename(f).lower() == 'readme.md':
                continue
            sov_data.append(parse_file(f))

    grok_data = []
    if os.path.exists(GROK_SKILLS_DIR):
        skill_files = glob.glob(os.path.join(GROK_SKILLS_DIR, "*/SKILL.md"))
        for f in skill_files:
            grok_data.append(parse_file(f))
        
    html_content = generate_html(sov_data, grok_data)
    
    docs_dir = os.path.dirname(OUTPUT_HTML)
    os.makedirs(docs_dir, exist_ok=True)
    
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Analysis complete. Generated reorganized HTML report at: {OUTPUT_HTML}")

if __name__ == "__main__":
    main()
