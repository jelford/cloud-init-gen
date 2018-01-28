#! /usr/bin/env ferret
'''
Generates a cloud-init based on configuration
from a richer TOML format

ferret:
- toml == 0.9.4
---
'''
import toml
import gzip
import io
import shutil
import base64
import os

config = None


from contextlib import contextmanager

@contextmanager
def indent(depth=4, char=' '):
    try:
        current_indent = indent._current_level
    except AttributeError:
        indent._current_level = 0
    indent._current_level += depth
    def prtr(*args, **kwargs):
        print(char * indent._current_level, *args, **kwargs)

    try:
        yield prtr
    finally:
        indent._current_level -= depth



def header():
    print('#cloud-config')


def packages():
    try:
        packages = config['packages']
    except KeyError:
        return

    print('packages:')
    with indent(depth=2) as p:
        for package_name in packages:
            p('-', package_name)

def users():
    try:
        users = config['users']
    except KeyError:
        return

    print('users:')
    with indent(depth=2) as p:
        for name, user in users.items():
            p(f'- name: {name}')
            with indent(depth=2) as p:
                groups, shell, key_file = [user.get(k) for k in ('groups', 'shell', 'key_file')]
                if groups:
                    p(f'groups: {", ".join(groups)}')
                if shell:
                    p(f'shell: {shell}')
                if key_file:
                    p('ssh-authorized-keys:')
                    with indent(depth=2):
                        key_path = os.path.expanduser(key_file)
                        with open(key_path, 'r') as f:
                            content = f.read()
                        p('-', content.strip())


def files():
    try:
        files = config['files']
    except KeyError:
        return

    print('write_files:')
    with indent(depth=2) as p:
        for _, f in files.items():
            p(f'- path: {f["remote"]}')
            with indent(depth=2) as p:
                p('encoding: "gz+b64"')
                data_buffer = io.BytesIO()
                local_path = os.path.expanduser(f['local'])
                
                with open(local_path, 'rb') as local_file:
                    with gzip.open(data_buffer, mode='wb') as gz:
                        shutil.copyfileobj(local_file, gz)
                encoded_file_content = base64.standard_b64encode(data_buffer.getbuffer())
                p('content: |')
                with indent(depth=2) as p:
                    p(encoded_file_content.decode('utf-8'))
            
        


def run():
    global config
    with open('cloud-init-config.toml', 'r', encoding='utf-8') as f:
        config = toml.load(f)
    header()
    packages()
    users()
    files()

if __name__ == '__main__':
    run()
