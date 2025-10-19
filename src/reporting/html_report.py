import os

def save_html_report(df, stats, out_dir, filename):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)
    with open(path, "w") as f:
        f.write("<html><body><h1>Report</h1><pre>")
        f.write(stats.to_string())
        f.write("</pre></body></html>")
    return path
