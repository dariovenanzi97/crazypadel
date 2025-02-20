import os
from django.conf import settings

# Imposta l'ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crazypadel.settings')

OUTPUT_FILE = 'crazypadel_dump.txt'


def write_header(file, title):
    file.write(f"\n{'=' * 40}\n{title}\n{'=' * 40}\n\n")


def dump_settings(file):
    write_header(file, 'DJANGO SETTINGS')
    for attr in dir(settings):
        if attr.isupper():
            value = getattr(settings, attr)
            file.write(f"{attr}: {value}\n")


def dump_app_files(file, app_path, app_name):
    write_header(file, f"APP: {app_name}")
    for root, dirs, files in os.walk(app_path):
        for filename in files:
            if filename.endswith('.py'):
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, os.getcwd())
                file.write(f"\n-- {relative_path} --\n\n")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        file.write(content + "\n")
                except Exception as e:
                    file.write(f"[ERROR] Cannot read file {relative_path}: {e}\n")


def main():
    project_root = os.getcwd()
    apps = ['accounts', 'leagues', 'crazypadel']

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as file:
        file.write("Crazypadel Project Dump\n")
        file.write("=" * 40 + "\n\n")

        # Dump settings
        dump_settings(file)

        # Dump file contenuti di ogni app
        for app in apps:
            app_path = os.path.join(project_root, app)
            if os.path.isdir(app_path):
                dump_app_files(file, app_path, app)
            else:
                file.write(f"\n[WARNING] App directory not found: {app_path}\n")

    print(f"Dump completato in {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
