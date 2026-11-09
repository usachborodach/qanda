import os
import yaml
import random
import subprocess
import pyperclip

pyperclip.set_clipboard('wl-clipboard')
base_path = os.path.dirname(__file__)
os.chdir(base_path)

with open('new_questions.yml') as file:
    new_questions = yaml.safe_load(file)

while True:
    question = random.choice(new_questions)
    print('\n' + question)
    answer = input('Берём этот вопрос? y/n: ')
    if answer != 'y':
        continue
    else:
        pyperclip.copy(f'# {question}')
        with open('qanda.md', 'a') as file:
            addition = f'\n\n---\n\n# {question}\n- '
            file.write(addition)
        new_questions.remove(question)
        with open('new_questions.yml', 'w') as file:
            yaml.safe_dump(new_questions, file, allow_unicode=True)
        subprocess.run(['code', 'qanda.md'])
        exit()