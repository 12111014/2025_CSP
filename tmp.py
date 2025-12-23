import os

files = os.listdir("./scripts")
txt_files = [file for file in files if file.endswith(".txt")]
txt_files.sort()

for idx, file in enumerate(txt_files):
    os.rename(f"./scripts/{file}", f"./scripts/节次{idx+1}_课堂语音转文字记录.txt")