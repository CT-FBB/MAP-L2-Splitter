import json, pandas as pd

with open('olt_location_data.json') as f:
    olt_data = json.load(f)

olt_vendors = {}
for olt_id, p in olt_data.items():
    v = str(p.get('vendor', '')).strip().upper()
    if v not in olt_vendors:
        olt_vendors[v] = 0
    olt_vendors[v] += 1

print("--- OLT Vendors (from JSON) ---")
for k, v in sorted(olt_vendors.items(), key=lambda x: -x[1]):
    print(f"{k}: {v}")

print("\n--- OLT Column from L1 (Not Vendor) ---")
l1 = pd.read_excel('/Users/bbae/GPTCodex/FTTH_L1_20260601.xlsx')
l1_unmatched = 0
for olt in l1['OLT'].astype(str):
    olt_clean = olt.strip()
    if olt_clean not in olt_data:
        l1_unmatched += 1
print(f"Total L1 Splitters: {len(l1)}, Unmatched OLTs in L1: {l1_unmatched}")

print("\n--- OLT Column from L2 (Not Vendor) ---")
l2 = pd.read_excel('/Users/bbae/GPTCodex/FTTH_L2_20260601.xlsx')
l2_unmatched = 0
for olt in l2['OLT'].astype(str):
    olt_clean = olt.strip()
    if olt_clean not in olt_data:
        l2_unmatched += 1
print(f"Total L2 Splitters: {len(l2)}, Unmatched OLTs in L2: {l2_unmatched}")
