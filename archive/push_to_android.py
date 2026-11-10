import os
import json

ANDROID_JSON_PATH = '/home/user/repos/interview_asker_android/app/src/main/assets/qanda.json'

base_path = os.path.dirname(__file__)
os.chdir(base_path)

def main():
    qanda = parse_md()
    dump_to_android_project(qanda)

def parse_md():
    with open('../qanda/main.md') as file:
        content = file.read()
    items = content.split('\n\n---\n\n')
    qanda = list()
    for item in items:
        splitted_item = item.split('\n', 1)
        qanda.append({
            'question': splitted_item[0][2:],
            'answer': splitted_item[1]
        })
    return qanda

def dump_to_android_project(qanda):
    with open(ANDROID_JSON_PATH, 'w') as file:
        json.dump(qanda, file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    main()