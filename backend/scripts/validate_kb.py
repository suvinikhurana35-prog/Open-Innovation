"""Quality validation for the structured Markdown KB. Scores each scheme /100
on presence of required sections + metadata, flags gaps."""
import os, re, glob, json
MD_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base_md")
REQUIRED = ["Overview", "Key Benefits", "Eligibility Criteria", "Required Documents",
            "Application Process", "Generated FAQs", "Full Official Text"]
def score(raw):
    pts, gaps = 0, []
    for sec in REQUIRED:
        if re.search(rf"##\s+{re.escape(sec)}", raw):
            body = raw.split(sec,1)[-1][:400]
            if "_See full official text below._" in body and sec not in ("Overview","Full Official Text","Generated FAQs"):
                pts += 7; gaps.append(f"{sec} (thin)")
            else:
                pts += 14
        else:
            gaps.append(f"{sec} (missing)")
    has_fm = raw.startswith("---") and "scheme_name:" in raw
    pts += 2 if has_fm else 0
    return min(pts,100), gaps
def main():
    files = sorted(glob.glob(os.path.join(MD_DIR,"*.md")))
    report, total = [], 0
    for fp in files:
        raw = open(fp,encoding="utf-8").read(); sc, gaps = score(raw); total += sc
        report.append({"scheme": os.path.basename(fp), "score": sc, "gaps": gaps})
        print(f"  {sc:3}/100  {os.path.basename(fp):55} {'· '+', '.join(gaps) if gaps else 'OK'}")
    avg = round(total/len(files),1) if files else 0
    print(f"\nAverage quality score: {avg}/100 across {len(files)} schemes")
    json.dump({"average": avg, "schemes": report}, open(os.path.join(MD_DIR,"quality_report.json"),"w"), indent=2)
if __name__=="__main__": main()
