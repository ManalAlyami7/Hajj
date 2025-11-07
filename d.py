import os

def print_tree(path, prefix=""):
    items = sorted(os.listdir(path))
    for i, item in enumerate(items):
        full_path = os.path.join(path, item)
        connector = "└── " if i == len(items)-1 else "├── "
        print(prefix + connector + item)
        if os.path.isdir(full_path):
            print_tree(full_path, prefix + ("    " if i == len(items)-1 else "│   "))

print_tree(".")  # start from current folder
