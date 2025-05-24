with open("dicts/categories/long.txt", "r") as f:
    lines = f.readlines()
    lines = [line for line in lines if len(line) >= 11]
    
with open("dicts/categories/long-revised.txt", "w") as f:
    f.writelines(lines)