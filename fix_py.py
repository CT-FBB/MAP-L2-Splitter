with open("process_splitters.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if "elif prov in ['CHACHOENGSAO'" in line:
        continue
    if "prov = 'EEC'" in line:
        continue
    new_lines.append(line)
    if 'prov = \'BMA\'' in line or 'prov = "BMA"' in line:
        # Determine indentation
        indent = len(line) - len(line.lstrip())
        new_lines.append(" " * indent + "elif prov in ['CHACHOENGSAO', 'CHON BURI', 'RAYONG']:\n")
        new_lines.append(" " * (indent + 4) + "prov = 'EEC'\n")

with open("process_splitters.py", "w") as f:
    f.writelines(new_lines)
print("Fixed process_splitters.py")
