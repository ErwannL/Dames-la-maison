
import subprocess
import os
import glob
import shutil
import time

IMAGE_NAME = "dames_buildozer"
CONTAINER_NAME = "dames_buildozer_container"
APP_NAME = "dames_maison"
APP_VERSION = "0.1"  # <-- Version globale
APK_OUTPUT = f"./{APP_NAME}-{APP_VERSION}-debug.apk"

# Pour la barre de progression
def print_progress(prefix, i, total):
    percent = int((i/total)*100)
    bar = "█" * (percent // 2) + "-" * (50 - percent // 2)
    print(f"{prefix}: |{bar}| {percent}%", end="\r")

def run(cmd, check=True, capture_output=False):
    """Exécute une commande shell et affiche la ligne exécutée."""
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, text=True, capture_output=capture_output, shell=False)

def main():
    steps = [
        "Nettoyage Docker",
        "Construction de l'image",
        "Lancement du conteneur",
        "Init Buildozer",
        "Création buildozer.spec",
        "Nettoyage ancien build",
        "Compilation APK",
        "Copie APK"
    ]
    total_steps = len(steps)

    for step_idx, step_name in enumerate(steps, 1):
        print(f"\n🔹 Step {step_idx}/{total_steps}: {step_name}")
        print_progress("Progress global", step_idx-1, total_steps)

        if step_name == "Nettoyage Docker":
            run(["docker", "stop", "$(docker ps -aq)"], check=False, capture_output=True)
            run(["docker", "rm", "$(docker ps -aq)"], check=False, capture_output=True)
            run(["docker", "rmi", IMAGE_NAME], check=False, capture_output=True)

        elif step_name == "Construction de l'image":
            run(["docker", "build", "-t", IMAGE_NAME, "."])

        elif step_name == "Lancement du conteneur":
            run([
                "docker", "run", "--name", CONTAINER_NAME, "-d", "-v",
                f"{os.getcwd()}:/app", IMAGE_NAME, "tail", "-f", "/dev/null"
            ])

        elif step_name == "Init Buildozer":
            spec_path = os.path.join(os.getcwd(), "buildozer.spec")
            if not os.path.exists(spec_path):
                try:
                    run([
                        "docker", "exec", CONTAINER_NAME, "bash", "-c",
                        "cd /app && buildozer init"
                    ], capture_output=True)
                except subprocess.CalledProcessError as e:
                    stderr = e.stderr or ""
                    print(f"⚠️ Erreur Init Buildozer (peut être ignorée si buildozer.spec existe déjà):\n{stderr}")

        elif step_name == "Création buildozer.spec":
            spec_content = f"""[app]
title = Dames a la maison
package.name = {APP_NAME}
package.domain = org.papy
source.dir = .
source.main = main.py
requirements = python3,kivy,pyjnius==1.4.0
orientation = landscape
version = {APP_VERSION}
android.api = 33
android.minapi = 21

[buildozer]
log_level = 2
warn_on_root = 0
android.sdk_path = /home/buildozeruser/android-sdk
android.ndk_path = /home/buildozeruser/android-ndk
"""
            with open("buildozer.spec", "w", encoding="utf-8") as f:
                f.write(spec_content)

        elif step_name == "Nettoyage ancien build":
            try:
                run([
                    "docker", "exec", CONTAINER_NAME, "bash", "-c",
                    "cd /app && buildozer android clean"
                ], capture_output=True)
            except subprocess.CalledProcessError as e:
                print("⚠️ Ignoré lors du nettoyage ancien build")

        elif step_name == "Compilation APK":
            try:
                run([
                    "docker", "exec", CONTAINER_NAME, "bash", "-c",
                    "cd /app && yes | buildozer -v android debug"
                ])
            except subprocess.CalledProcessError as e:
                stderr = e.stderr or ""
                print(f"❌ Erreur compilation APK:\n{stderr}")
                raise RuntimeError("Buildozer APK build failed") from e

        elif step_name == "Copie APK":
            apk_files = glob.glob("bin/*.apk")
            if not apk_files:
                raise FileNotFoundError("❌ Aucun fichier APK trouvé dans ./bin/")
            latest_apk = max(apk_files, key=os.path.getctime)
            shutil.copy(latest_apk, APK_OUTPUT)
            print(f"✅ Copie de {latest_apk} vers {APK_OUTPUT} terminée !")

        # Update barre de progression interne (simulée)
        for i in range(1, 51):
            print_progress("Step progress", i, 50)
            time.sleep(0.01)  # simule progression interne
        print()  # newline après chaque step

    # Nettoyage final du conteneur
    print("\n🔹 Nettoyage du conteneur Docker...")
    run(["docker", "stop", CONTAINER_NAME], check=False)
    run(["docker", "rm", CONTAINER_NAME], check=False)

    print("\n✅ Build terminé ! APK copiée avec succès.")

if __name__ == "__main__":
    main()
