import re
import shutil
import json
import random
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from ebibletools.ebible_downloader import EBibleDownloader
from ebibletools.metrics import chrF_plus, normalized_edit_distance
import matplotlib.pyplot as plt

load_dotenv()

NUM_VERSES_PER_LANGUAGE = 10
AGENT_TIME_LIMIT = 300
AGENT_MODEL = "grok-code-fast-1"  # Set model here (e.g., "claude-3.5-sonnet", "gpt-4o", "o3-mini", "grok-code-fast") or leave empty for default

root_dir = Path(__file__).parent
corpus_dir = root_dir / "Corpus"
downloader = EBibleDownloader(output_dir=str(corpus_dir))
downloader.download_file("eng-engULB.txt")

for lang_code in ["mya", "bod", "mal", "suz"]:
    files = [f for f in downloader.list_files() if f["name"].startswith(f"{lang_code}-")]
    if files:
        largest = max(files, key=lambda x: int(x["size"]))
        downloader.download_file(largest["name"])

eng_file = corpus_dir / "eng-engULB.txt"
for file in corpus_dir.glob("*.txt"):
    match = re.match(r'^([a-z]{3})-', file.name)
    if match and match.group(1) != "eng":
        lang_dir = corpus_dir / match.group(1)
        lang_dir.mkdir(exist_ok=True)
        shutil.copy(eng_file, lang_dir / eng_file.name)
        shutil.copy(file, lang_dir / file.name)

def mask_target_line(file_path, line_index):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    original_line = lines[line_index]
    lines[line_index] = '\n'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    return original_line

def restore_target_line(file_path, line_index, original_line):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines[line_index] = original_line
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def extract_translation(text):
    pattern = r'<translation>(.*?)</translation>'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text.strip()

def find_valid_verses(lang_dir):
    eng_file = lang_dir / "eng-engULB.txt"
    target_files = [f for f in lang_dir.glob("*.txt") if f.name != "eng-engULB.txt"]
    if not target_files:
        return []
    
    target_file = target_files[0]
    with open(eng_file, 'r', encoding='utf-8') as f:
        eng_lines = f.readlines()
    with open(target_file, 'r', encoding='utf-8') as f:
        target_lines = f.readlines()
    
    valid_indices = [
        i for i in range(min(len(eng_lines), len(target_lines)))
        if len(eng_lines[i].strip()) > 10 and len(target_lines[i].strip()) > 10
    ]
    
    return valid_indices, eng_lines, target_lines, target_file

def select_verses(lang_dir, num_verses):
    result = find_valid_verses(lang_dir)
    if not result:
        return []
    valid_indices, eng_lines, target_lines, target_file = result
    if len(valid_indices) < num_verses:
        return []
    
    selected_indices = random.sample(valid_indices, num_verses)
    verses = []
    for idx in selected_indices:
        verses.append({
            'index': idx,
            'english': eng_lines[idx].strip(),
            'target': target_lines[idx].strip(),
            'target_file': target_file
        })
    return verses

GOAL_TEMPLATE = """
Two aligned Bible text files are in this project (line-by-line verse correspondence). 
Blank lines indicate untranslated verses.
Before translating, analyze relevant parts of both source and target texts to understand translation patterns.
Translate this text:
{translation_text}

Provide your answer in this format:
<translation>your translation here</translation>
"""

results = {}

for lang_dir in sorted(corpus_dir.iterdir()):
    if not lang_dir.is_dir():
        continue
    
    lang_code = lang_dir.name
    if lang_code == "eng":
        continue
    
    print(f"\n{'='*60}")
    print(f"Processing language: {lang_code}")
    print(f"{'='*60}")
    
    verses = select_verses(lang_dir, NUM_VERSES_PER_LANGUAGE)
    if not verses:
        print(f"⚠️  Skipping {lang_code} - insufficient valid verses")
        continue
    
    lang_results = {'verses': []}
    
    for i, verse in enumerate(verses, 1):
        print(f"\n[{i}/{len(verses)}] Translating verse {verse['index']}...")
        
        target_file = verse['target_file']
        line_index = verse['index']
        english_text = verse['english']
        reference_text = verse['target']
        
        original_line = mask_target_line(target_file, line_index)
        
        goal = GOAL_TEMPLATE.format(translation_text=english_text)
        
        predicted_text = ""
        try:
            cmd = ["cursor-agent", "-p"]
            if AGENT_MODEL:
                cmd.extend(["--model", AGENT_MODEL])
            cmd.append(goal)
            
            result = subprocess.run(
                cmd,
                cwd=str(lang_dir),
                capture_output=True,
                text=True,
                timeout=AGENT_TIME_LIMIT
            )
            
            if result.returncode == 0:
                predicted_text = extract_translation(result.stdout)
            else:
                print(f"  ⚠️  Cursor agent returned error: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print(f"  ⚠️  Agent timed out after {AGENT_TIME_LIMIT} seconds")
        except FileNotFoundError:
            print(f"  ⚠️  cursor-agent not found. Install with: curl https://cursor.com/install -fsS | bash")
        except Exception as e:
            print(f"  ⚠️  Agent error: {e}")
        
        restore_target_line(target_file, line_index, original_line)
        
        if predicted_text:
            chrf_score = chrF_plus(predicted_text, reference_text)
            edit_sim = 1.0 - normalized_edit_distance(predicted_text, reference_text)
            
            verse_result = {
                'index': line_index,
                'english': english_text,
                'predicted': predicted_text,
                'reference': reference_text,
                'chrf': chrf_score,
                'edit_similarity': edit_sim
            }
            lang_results['verses'].append(verse_result)
            
            print(f"  chrF+: {chrf_score:.4f}, Edit Similarity: {edit_sim:.4f}")
        else:
            print(f"  ⚠️  No translation collected")
    
    if lang_results['verses']:
        avg_chrf = sum(v['chrf'] for v in lang_results['verses']) / len(lang_results['verses'])
        avg_edit = sum(v['edit_similarity'] for v in lang_results['verses']) / len(lang_results['verses'])
        lang_results['avg_chrf'] = avg_chrf
        lang_results['avg_edit'] = avg_edit
        results[lang_code] = lang_results
        print(f"\n{lang_code} - Avg chrF+: {avg_chrf:.4f}, Avg Edit: {avg_edit:.4f}")

with open(root_dir / "benchmark_results.json", 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print("Generating visualizations...")
print(f"{'='*60}")

languages = list(results.keys())
avg_chrfs = [results[lang]['avg_chrf'] for lang in languages]
avg_edits = [results[lang]['avg_edit'] for lang in languages]

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.bar(languages, avg_chrfs)
plt.title('Average chrF+ Score by Language')
plt.ylabel('chrF+ Score')
plt.xlabel('Language')
plt.ylim(0, 1)

plt.subplot(1, 2, 2)
plt.bar(languages, avg_edits)
plt.title('Average Edit Distance Similarity by Language')
plt.ylabel('Edit Similarity')
plt.xlabel('Language')
plt.ylim(0, 1)

plt.tight_layout()
plt.savefig(root_dir / "benchmark_metrics.png", dpi=150)
print("Saved: benchmark_metrics.png")

all_chrfs = []
all_edits = []
for lang in languages:
    for verse in results[lang]['verses']:
        all_chrfs.append(verse['chrf'])
        all_edits.append(verse['edit_similarity'])

plt.figure(figsize=(8, 6))
plt.scatter(all_chrfs, all_edits, alpha=0.6)
plt.xlabel('chrF+ Score')
plt.ylabel('Edit Distance Similarity')
plt.title('Translation Quality: chrF+ vs Edit Similarity')
plt.xlim(0, 1)
plt.ylim(0, 1)
plt.grid(True, alpha=0.3)
plt.savefig(root_dir / "benchmark_scatter.png", dpi=150)
print("Saved: benchmark_scatter.png")

print(f"\n✅ Benchmark complete! Results saved to benchmark_results.json")
