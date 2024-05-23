#!/usr/bin/env python

# Filename: gen_req.py
# Created on: May 23, 2024
# Author: Lucas Araújo <araujolucas@dcc.ufmg.br>

# This script generates a 'requirements.txt' file with the packages used in a Python project.


import os
import re
import subprocess
import argparse

# Some packages have different names when installed via pip
# This dictionary maps the package name used in the import statement to the name used in pip
PACKAGE_MAPPING = {
    'pil': 'pillow',
}

def get_installed_packages(project_path, venv_folder):
    """
    @brief:
        Get the installed packages in the virtual environment or globally
    """
    if venv_folder:  # Check if the virtual environment folder was provided
        venv = os.path.join(project_path, venv_folder)

        if os.path.isdir(venv):  # Check if the virtual environment exists
            pip_executable = os.path.join(venv, "bin", "pip")
            result = subprocess.run([pip_executable, "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Check if the virtual environment was activated successfully
            if result.returncode == 0:
                print("Getting packages from the virtual environment.")
                packages = result.stdout.decode("utf-8").split("\n")[2:]
                installed_packages = {}
                for package in packages:
                    if package:
                        parts = package.split()
                        name = parts[0].lower().replace("-", "_")
                        version = parts[1]
                        installed_packages[name] = version
                return installed_packages
            else:
                print("Failed to activate the virtual environment.")
                print("ERROR: ", result.stderr.decode("utf-8"))
                print("Getting global packages instead.")

        else:
            print("Virtual environment not found.")
            print("Getting global packages instead.")
    else:
        print("No virtual environment folder provided.")
        print("Getting global packages instead.")

    # If the virtual environment does not exist or was not activated, get the global packages
    result = subprocess.run(["pip", "list"], stdout=subprocess.PIPE)
    packages = result.stdout.decode("utf-8").split("\n")[2:]
    installed_packages = {}
    for package in packages:
        if package:
            parts = package.split()
            name = parts[0].lower().replace("-", "_")
            version = parts[1]
            installed_packages[name] = version
    return installed_packages


def get_imported_packages(path, ignore=[]):
    """
    @brief:
         Get a set with the imported packages in the project
    """
    imported_packages = set()

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in ignore]

        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), "r") as f:
                    content = f.read()
                    imports = re.findall(
                        r"^\s*(?:import|from)\s+(\S+)", content, re.MULTILINE
                    )

                    for imp in imports:
                        imp = imp.split(".")[0].lower()
                        # Check if the package has a mapping
                        if imp in PACKAGE_MAPPING:
                            imp = PACKAGE_MAPPING[imp]

                        imported_packages.add(imp)


    return imported_packages


def generate_requirements_txt(
    installed_packages, imported_packages, path, filename="requirements.txt"
):
    """
    @brief:
        Generate a 'requirements.txt' file with the packages used in the project
    """

    output_file = os.path.join(path, filename)

    with open(output_file, "w") as f:
        for package in imported_packages:
            for installed_package in installed_packages:
                # Check if the package is installed
                # pip list returns the package name with underscores
                # but the import statement uses hyphens
                # so we need to check both cases
                if package == installed_package or package.replace(
                    "_", "-"
                ) == installed_package.replace("_", "-"):
                    f.write(
                        f"{installed_package}=={installed_packages[installed_package]}\n"
                    )
                    break


def main():
    parser = argparse.ArgumentParser(
        description="Generate requirements.txt based on imported packages."
    )
    parser.add_argument("project_path", type=str, help="Path to the project directory")
    parser.add_argument(
        "--venv_folder", type=str, help="Path to the virtual environment directory"
    )
    args = parser.parse_args()

    # Folders to ignore when searching for imported packages
    ignore = ["__pycache__", ".git", ".vscode", ".venv"]

    installed_packages = get_installed_packages(args.project_path, args.venv_folder)
    imported_packages = get_imported_packages(args.project_path, ignore=ignore)
    generate_requirements_txt(installed_packages, imported_packages, args.project_path)
    print(f"'requirements.txt' foi gerado com os pacotes utilizados.")


if __name__ == "__main__":
    main()
