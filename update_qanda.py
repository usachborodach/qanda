import os
import json
from myfirstvps.utilities.wekan import common as myfirstvps
from pymongo import MongoClient


base_path = os.path.dirname(__file__)
os.chdir(base_path)


ANDROID_JSON_PATH = '/home/user/repos/interview_asker_android/app/src/main/assets/qanda.json'


def main():
    qanda = parse_md()
    dump_to_android_project(qanda)
    push_to_mongo(qanda)


def push_to_mongo(qanda):
    ssh_process = myfirstvps.open_tunnel()
    client = MongoClient()
    db = client['interview_asker']
    collection = db['qanda']
    collection.delete_many({})
    collection.insert_many(qanda)
    client.close()
    myfirstvps.close_tunnel(ssh_process)


def parse_md():
    with open('qanda.md') as file:
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