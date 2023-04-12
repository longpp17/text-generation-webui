'''todo: if conda is empty give user a option to reinstall'''
'''todo: if conda environment creation failed attempt to reinstall it for 3 times, if still can't gave user a option to 
suspend or reinstall, and gave a precise version of why it failed'''

import os
import sys
import subprocess
from pathlib import Path

# Based on the installer found here: https://github.com/Sygil-Dev/sygil-webui
# This script will install git and all dependencies
# using micromamba (an 8mb static-linked single-file binary, conda replacement).
# This enables a user to install this project without manually installing conda and git.

print("WARNING: This script relies on Micromamba which may have issues on some systems when installed under a path with spaces.")
print("         May also have issues with long paths.\n")

input("Press enter to continue...")

os.system("cls")

print("What is your GPU?")
print("\nA) NVIDIA")
print("B) None (I want to run in CPU mode)\n")
gpu_choice = input("Input> ").strip().upper()[0]

if gpu_choice == "A":
    packages_to_install = "python=3.10.9 pytorch[version=2,build=py3.10_cuda11.7*] torchvision torchaudio pytorch-cuda=11.7 cuda-toolkit ninja git"
    channel = "-c pytorch -c nvidia/label/cuda-11.7.0 -c nvidia -c conda-forge"
elif gpu_choice == "B":
    packages_to_install = "pytorch torchvision torchaudio cpuonly git"
    channel = "-c conda-forge -c pytorch"
else:
    print("Invalid choice. Exiting...")
    sys.exit()

script_dir = Path(__file__).resolve().parent

os.environ["PATH"] = f"{os.environ['PATH']};{os.environ['SystemRoot']}\\system32"

mamba_root_prefix = script_dir / "installer_files" / "mamba"
install_env_dir = script_dir / "installer_files" / "env"
micromamba_download_url = "https://github.com/mamba-org/micromamba-releases/releases/download/1.4.0-0/micromamba-win-64"
repo_url = "https://github.com/oobabooga/text-generation-webui.git"
umamba_exists = "F"

# Figure out whether git and conda need to be installed
try:
    subprocess.run([str(mamba_root_prefix / "micromamba.exe"), "--version"], check=True)
    umamba_exists = "T"
except subprocess.CalledProcessError:
    pass


# (if necessary) install git and conda into a contained environment
if packages_to_install:
    # Download micromamba
    if umamba_exists == "F":
        print(f"Downloading Micromamba from {micromamba_download_url} to {mamba_root_prefix}\\micromamba.exe")

        mamba_root_prefix.mkdir(parents=True, exist_ok=True)
        subprocess.run(f"curl -Lk {micromamba_download_url} > {mamba_root_prefix}\\micromamba.exe", shell=True, check=True)

        # Test the mamba binary
        print("Micromamba version:")
        subprocess.run([str(mamba_root_prefix / "micromamba.exe"), "--version"], check=True)

    # Create micromamba hook
    if not (mamba_root_prefix / "condabin" / "micromamba.bat").exists():
        subprocess.run([str(mamba_root_prefix / "micromamba.exe"), "shell", "hook"], check=True)

    # Create the installer env
    if not install_env_dir.exists():
        print(f"Packages to install: {packages_to_install}")
        subprocess.run([str(mamba_root_prefix / "micromamba.exe"), "create", "-y", "--prefix",     str(install_env_dir), channel, packages_to_install], check=True)


# Check if conda environment was actually created
if not (install_env_dir / "python.exe").exists():
    print("\nConda environment is empty.")
    sys.exit()

# Activate installer env
subprocess.run([str(mamba_root_prefix / "condabin" / "micromamba.bat"), "activate", str(install_env_dir)], check=True)

# Clone the repository and install the pip requirements
webui_dir = script_dir / "text-generation-webui"
if webui_dir.exists():
    os.chdir(webui_dir)
    subprocess.run(["git", "pull"], check=True)
else:
    subprocess.run(["git", "clone", repo_url], check=True)
    subprocess.run([str(install_env_dir / "python.exe"), "-m", "pip", "install", "https://github.com/jllllll/bitsandbytes-windows-webui/raw/main/bitsandbytes-0.37.2-py3-none-any.whl"], check=True)
    os.chdir(webui_dir)

subprocess.run([str(install_env_dir / "python.exe"), "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"], check=True)
subprocess.run([str(install_env_dir / "python.exe"), "-m", "pip", "install", "-r", "extensions/api/requirements.txt", "--upgrade"], check=True)
subprocess.run([str(install_env_dir / "python.exe"), "-m", "pip", "install", "-r", "extensions/elevenlabs_tts/requirements.txt", "--upgrade"], check=True)
subprocess.run([str(install_env_dir / "python.exe"), "-m", "pip", "install", "-r", "extensions/google_translate/requirements.txt", "--upgrade"], check=True)
subprocess.run([str(install_env_dir / "python.exe"), "-m", "pip", "install", "-r", "extensions/silero_tts/requirements.txt", "--upgrade"], check=True)
subprocess.run([str(install_env_dir / "python.exe"), "-m", "pip", "install", "-r", "extensions/whisper_stt/requirements.txt", "--upgrade"], check=True)

# Skip GPTQ install if CPU only
if gpu_choice != "A":
    sys.exit()

# Download GPTQ and compile locally; if compile fails, install from wheel
repositories_dir = script_dir / "repositories"
if not repositories_dir.exists():
    repositories_dir.mkdir(parents=True, exist_ok=True)

os.chdir(repositories_dir)

gptq_dir = repositories_dir / "GPTQ-for-LLaMa"
if not gptq_dir.exists():
    subprocess.run(["git", "clone", "https://github.com/oobabooga/GPTQ-for-LLaMa.git", "-b", "cuda"], check=True)
    os.chdir(gptq_dir)
    subprocess.run([str(install_env_dir / "python.exe"), "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    subprocess.run([str(install_env_dir / "python.exe"), "setup_cuda.py", "install"], check=True)

    if not (install_env_dir / "lib" / "site-packages" / "quant_cuda-0.0.0-py3.10-win-amd64.egg").exists():
        print("CUDA kernel compilation failed. Will try to install from wheel.")
        subprocess.run([str(install_env_dir / "python.exe"), "-m", "pip", "install", "https://github.com/jllllll/GPTQ-for-LLaMa-Wheels/raw/main/quant_cuda-0.0.0-cp310-cp310-win_amd64.whl"], check=True)

input("Press enter to continue...")

