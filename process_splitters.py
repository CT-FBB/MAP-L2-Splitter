import os
import glob
import pandas as pd
import json
import math

BASE_DIR = '/Users/bbae/GPTCodex'
LOCATION_DIR = '/Users/bbae/GPTCodex/OLT-Location'
PROV_DIR = os.path.join(LOCATION_DIR, 'L2Location')
OLT_JSON = os.path.join(LOCATION_DIR, 'GIT-LOCATION', 'olt_location_data.json')

os.makedirs(PROV_DIR, exist_ok=True)

def main():
    olt_vendors = {}
    prov_features = {}
    
    vendors_list = []
    types_list = ["OLT", "L1", "L2"]
    olts_list = []
    
    def get_vendor_idx(v):
        if v not in vendors_list:
            vendors_list.append(v)
        return vendors_list.index(v)
        
    def get_type_idx(t):
        return types_list.index(t)
        
    def get_olt_idx(o):
        if o not in olts_list:
            olts_list.append(o)
        return olts_list.index(o)
    
    if os.path.exists(OLT_JSON):
        with open(OLT_JSON, 'r', encoding='utf-8') as f:
            olt_data = json.load(f)
            for k, v in olt_data.items():
                vendor = v.get('vendor', 'UNKNOWN')
                prov = str(v.get('prov', '')).strip().upper()
                if not prov or prov.lower() == 'nan':
                    prov = 'UNKNOWN'
                if prov in ["BANGKOK", "NONTHABURI", "PATHUM THANI", "SAMUT PRAKAN"]:
                    prov = 'BMA'
                olt_vendors[k] = vendor
                
                if prov not in prov_features:
                    prov_features[prov] = []
                    
                prov_features[prov].append([
                    round(v["long"], 5), 
                    round(v['lat'], 5), 
                    get_type_idx("OLT"), 
                    k, 
                    get_olt_idx(k), 
                    get_vendor_idx(vendor)
                ])

    for ftype, ptn in [('L1', 'FTTH_L1*.xlsx'), ('L2', 'FTTH_L2*.xlsx')]:
        files = sorted(glob.glob(os.path.join(BASE_DIR, ptn)), key=os.path.getmtime, reverse=True)
        if not files:
            files = sorted(glob.glob(os.path.join(BASE_DIR, 'SPL', 'TOL_Network_*', ptn)), key=os.path.getmtime, reverse=True)
        
        if not files:
            print(f"No {ftype} file found.")
            continue
            
        file_path = files[0]
        print(f"Reading {file_path} ...")
        df = pd.read_excel(file_path)
        
        id_col = 'SPTL1' if ftype == 'L1' else 'SPTL2'
        
        records = df.to_dict('records')
        for row in records:
            lat = row.get('LATITUDE')
            lon = row.get('LONGITUDE')
            
            try:
                lat = float(lat)
                lon = float(lon)
            except:
                continue
                
            if pd.isna(lat) or pd.isna(lon) or lat == 0 or lon == 0 or math.isnan(lat):
                continue
                
            sp_id = str(row.get(id_col, '')).strip()
            if not sp_id or pd.isna(sp_id) or sp_id == 'nan':
                continue
                
            olt = str(row.get('OLT', '')).strip().replace('GO', 'G0').upper()
            prov = str(row.get('PROVINCE', '')).strip().upper()
            if not prov or prov.lower() == 'nan':
                prov = 'UNKNOWN'
            if prov in ["BANGKOK", "NONTHABURI", "PATHUM THANI", "SAMUT PRAKAN"]:
                prov = 'BMA'
                
            vendor = olt_vendors.get(olt, 'UNKNOWN')
            
            if prov not in prov_features:
                prov_features[prov] = []
                
            prov_features[prov].append([
                round(lon, 5), 
                round(lat, 5), 
                get_type_idx(ftype), 
                sp_id, 
                get_olt_idx(olt), 
                get_vendor_idx(vendor)
            ])

    for prov, features in prov_features.items():
        out_file = os.path.join(PROV_DIR, f"{prov}.js")
        out_data = {
            "vendors": vendors_list,
            "types": types_list,
            "olts": olts_list,
            "data": features
        }
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write("window.provinceData = ")
            json.dump(out_data, f, ensure_ascii=False, separators=(',', ':'))
            f.write(";")
            
    print(f"Saved {len(prov_features)} province JS files.")

if __name__ == '__main__':
    main()
