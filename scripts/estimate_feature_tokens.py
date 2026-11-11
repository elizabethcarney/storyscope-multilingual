"""Estimate token usage for feature application (stage 5).

Usage: python scripts/estimate_feature_tokens.py <stories.parquet> [taxonomy.json]
Requires pandas, pyarrow, tiktoken. Output is estimated by serializing a
plausible JSON answer (first allowed value per feature) for each dimension.
"""
import importlib, json, sys
import pandas as pd, tiktoken

sys.path.insert(0, ".")
af = importlib.import_module("storyscope.feature_application.apply_features")
enc = tiktoken.get_encoding("o200k_base")
n = lambda s: len(enc.encode(s))

parquet = sys.argv[1]
tax = af.Taxonomy.from_json(sys.argv[2] if len(sys.argv) > 2 else "data/taxonomy.json")
df = pd.read_parquet(parquet)
cols = [c for c in df.columns if c.startswith("story_")]

# Output: one JSON object per dimension; sample answer per feature.
out = {}
for d in tax.dimensions:
    ans = {f.id: (f.values[0] if f.values else "yes") for f in d.features}
    out[d.key] = n(json.dumps(ans, indent=2))
out_per_story = sum(out.values())
print(f"dimensions={len(tax.dimensions)} features={tax.total_features}")
print("est. output tokens/story (all dims):", out_per_story)

tot_in = 0
for c in cols:
    ins = []
    for s in df[c].dropna():
        ins.append(sum(n(af.build_dimension_prompt(d, s)) for d in tax.dimensions))
    s = pd.Series(ins)
    print(f"{c}: n={len(s)} input tokens/story mean={s.mean():.0f} median={s.median():.0f} max={s.max()}")
    tot_in += s.mean()
print(f"mean input tokens/story across sources: {tot_in/len(cols):.0f}")
