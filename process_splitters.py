import os
import glob
import pandas as pd
import json
import math

BASE_DIR = '/Users/bbae/GPTCodex'
LOCATION_DIR = '/Users/bbae/GPTCodex/OLT-Location'
PROV_DIR = os.path.join(LOCATION_DIR, 'provinces_data')
OLT_JSON = os.path.join(LOCATION_DIR, 'GIT-LOCATION', 'olt_location_data.json')

os.makedirs(PROV_DIR, exist_ok=True)

def main():
    olt_vendors = {}
    prov_features = {}
    
    vendors_list = []
    types_list = ["OLT", "L1", "L2"]
    olts_list = []
    
    def get_vendor_idx(v):
        v = str(v).strip().upper()
        if v not in vendors_list:
            vendors_list.append(v)
        return vendors_list.index(v)
        
    def get_type_idx(t):
        return types_list.index(t)
        
    def get_olt_idx(o):
        if o not in olts_list:
            olts_list.append(o)
        return olts_list.index(o)
        
    # --- LOAD DEVICE MAPPING (For Vendor) ---
    device_vendors = {}
    device_files = sorted(glob.glob(os.path.join(BASE_DIR, '**', 'Device*.xlsx'), recursive=True), key=os.path.getmtime, reverse=True)
    if device_files:
        latest_device = device_files[0]
        print(f"Loading vendors from {latest_device} ...")
        try:
            df_dev = pd.read_excel(latest_device, usecols=['Device Name', 'Vendor'])
            for _, row in df_dev.iterrows():
                dev_name = str(row.get('Device Name', '')).strip().replace('GO', 'G0').upper()
                vendor = str(row.get('Vendor', '')).strip().upper()
                if dev_name and dev_name != 'NAN' and vendor and vendor != 'NAN':
                    device_vendors[dev_name] = vendor
        except Exception as e:
            print(f"Error reading {latest_device}: {e}")
    else:
        print("No Device*.xlsx file found for vendor mapping!")

    # --- LOAD ODN MAPPING (For Linkage) ---
    odn_mapping = {}
    odn_files = sorted(glob.glob(os.path.join(BASE_DIR, '**', 'ODN*.xlsx'), recursive=True), key=os.path.getmtime, reverse=True)
    if odn_files:
        latest_odn = odn_files[0]
        print(f"Loading linkage from {latest_odn} ...")
        df_odn = pd.read_excel(latest_odn, usecols=['Device', 'L1 Name', 'L2 Name'])
        for _, row in df_odn.iterrows():
            dev = str(row.get('Device', '')).strip().replace('GO', 'G0').upper()
            if not dev or pd.isna(dev) or dev == 'NAN': continue
            
            l1 = str(row.get('L1 Name', '')).strip()
            l2 = str(row.get('L2 Name', '')).strip()
            
            if l1 and l1 != 'nan':
                odn_mapping[l1] = dev
            if l2 and l2 != 'nan':
                odn_mapping[l2] = dev
    else:
        print("No ODN*.xlsx file found for linkage!")

    # --- GATHER DYNAMIC PREFIX MAPPING FROM L1 & L2 ---
    prefix_to_prov = {}
    print("Building prefix-to-province mapping from L1/L2 files...")
    for ftype, ptn in [('L1', 'FTTH_L1*.xlsx'), ('L2', 'FTTH_L2*.xlsx')]:
        files = sorted(glob.glob(os.path.join(BASE_DIR, ptn)), key=os.path.getmtime, reverse=True)
        if not files:
            files = sorted(glob.glob(os.path.join(BASE_DIR, 'SPL', 'TOL_Network_*', ptn)), key=os.path.getmtime, reverse=True)
        if files:
            df = pd.read_excel(files[0], usecols=['SPTL1' if ftype == 'L1' else 'SPTL2', 'PROVINCE'])
            id_col = 'SPTL1' if ftype == 'L1' else 'SPTL2'
            df_sp = df[id_col].astype(str).str.strip()
            df_pfx = df_sp.str[:3].str.upper()
            valid_mask = df_pfx.str.isalpha() & df['PROVINCE'].notna() & (df['PROVINCE'].astype(str).str.strip().str.upper() != 'NAN')
            df_valid = df[valid_mask].copy()
            df_valid['PREFIX'] = df_pfx[valid_mask]
            df_valid['PROV_UPPER'] = df_valid['PROVINCE'].astype(str).str.strip().str.upper()
            if not df_valid.empty:
                mode_df = df_valid.groupby('PREFIX')['PROV_UPPER'].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None)
                for k, v in mode_df.dropna().to_dict().items():
                    if k not in prefix_to_prov:
                        prefix_to_prov[k] = v

    # --- PROCESS OLT MASTER JSON ---
    if os.path.exists(OLT_JSON):
        with open(OLT_JSON, 'r', encoding='utf-8') as f:
            olt_data = json.load(f)
            for k, v in olt_data.items():
                # Get vendor from Device mapping first, fallback to JSON
                vendor = device_vendors.get(k, v.get('vendor', 'UNKNOWN'))
                
                # OLT uses province from JSON directly (NOT prefix mapping)
                # Prefix mapping is only for Splitters
                prov = str(v.get('prov', '')).strip().upper()
                    
                if not prov or prov.lower() == 'nan':
                    prov = 'UNKNOWN'
                if prov in ["BANGKOK", "NONTHABURI", "PATHUM THANI", "SAMUT PRAKAN"]:
                    prov = 'BMA'
                elif prov in ['CHACHOENGSAO', 'CHON BURI', 'RAYONG']:
                    prov = 'EEC'
                olt_vendors[k] = vendor
                
                if prov not in prov_features:
                    prov_features[prov] = []
                    
                prov_features[prov].append([
                    round(v["long"], 5), 
                    round(v['lat'], 5), 
                    get_type_idx("OLT"), 
                    k, 
                    get_olt_idx(k), 
                    get_vendor_idx(vendor),
                    int(v.get("ports_use", 0)),
                    int(v.get("ports", 0))
                ])

    # --- PROCESS SPLITTER L1 & L2 ---
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
        
        # --- DYNAMIC PREFIX MAPPING (Fix Outliers) ---
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
                
            # 1. Try to get OLT linkage from ODN file
            olt = odn_mapping.get(sp_id)
            # 2. Fallback to FTTH Excel file if not found in ODN
            if not olt:
                olt = str(row.get('OLT', '')).strip().replace('GO', 'G0').upper()
            
            # Handle exception for SMPPRI which stands for Si Maha Phot, Prachin Buri (not Samut Prakan)
            if sp_id.upper().startswith('SMPPRI'):
                prov = 'PRACHIN BURI'
            else:
                # Use dynamic prefix mapping first, then fallback to original column
                prefix = sp_id[:3].upper()
                if len(prefix) == 3 and prefix.isalpha() and prefix in prefix_to_prov:
                    prov = prefix_to_prov[prefix]
                else:
                    prov = str(row.get('PROVINCE', '')).strip().upper()
                
            if not prov or prov.lower() == 'nan':
                prov = 'UNKNOWN'
                
            if prov in ["BANGKOK", "NONTHABURI", "PATHUM THANI", "SAMUT PRAKAN"]:
                prov = 'BMA'
            elif prov in ['CHACHOENGSAO', 'CHON BURI', 'RAYONG']:
                prov = 'EEC'
                
            # Vendor lookup falls back to UNKNOWN if OLT is not in olt_vendors mapping
            vendor = olt_vendors.get(olt, device_vendors.get(olt, 'UNKNOWN'))
            
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

    # --- SAVE TO JS FILES ---
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
            
    print(f"Saved {len(prov_features)} province JS files to {PROV_DIR}.")

if __name__ == '__main__':
    main()
