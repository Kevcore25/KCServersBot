with open("main.py", encoding='utf-8') as f:
    main = f.readlines()

cmds = []
tmp = []
for ln in main:
    if ln.startswith("@bot.command"):
        cmds.append(tmp)
        tmp = []
    elif ln.startswith('    ') or ln == "" or ln.isspace():
        tmp.append(ln)

import time

for cmd in cmds:
    print("".join(cmd))
    time.sleep(1)