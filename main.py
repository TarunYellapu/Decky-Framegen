import decky  # Old-style Decky import
import os
import subprocess
import json
from pathlib import Path
from vdf import binary_load

class Plugin:
    async def _main(self):
        decky.logger.info("Framegen plugin loaded")

    async def _unload(self):
        decky.logger.info("Framegen plugin unloaded.")

    async def run_uninstall_fgmod(self) -> dict:
        try:
            result = subprocess.run(
                ["/bin/bash", Path.home() / "homebrew" / "plugins" / "Decky-Framegen" / "assets" / "fgmod-remover.sh"],
                capture_output=True,
                text=True,
                check=True
            )
            return {"status": "success", "output": result.stdout}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": str(e), "output": e.output}

    async def run_install_fgmod(self) -> dict:
        try:
            assets_dir = Path.home() / "homebrew" / "plugins" / "Decky-Framegen" / "assets"
            downloads_dir = Path.home() / "Downloads"

            if not assets_dir.exists():
                decky.logger.error(f"Assets directory not found: {assets_dir}")
                return {
                    "status": "error",
                    "message": f"Assets directory not found: {assets_dir}"
                }

            downloads_dir.mkdir(parents=True, exist_ok=True)

            files_to_copy = ["prepare.sh", "fgmod.sh", "fgmod-uninstaller.sh"]
            for file_name in files_to_copy:
                src = assets_dir / file_name
                if not src.exists():
                    decky.logger.error(f"Required file missing: {src}")
                    return {
                        "status": "error",
                        "message": f"Required file missing: {file_name}"
                    }

                dest = downloads_dir / file_name
                dest.write_bytes(src.read_bytes())
                dest.chmod(0o755)

            prepare_script = downloads_dir / "prepare.sh"
            process = subprocess.run(
                ["/bin/bash", str(prepare_script)],
                capture_output=True,
                text=True,
                timeout=300
            )

            fgmod_path = Path.home() / "fgmod"
            fgmod_path.mkdir(parents=True, exist_ok=True)

            decky.logger.info(f"Script output:\n{process.stdout}")
            decky.logger.error(f"Script errors:\n{process.stderr}")

            if "All done!" not in process.stdout:
                decky.logger.error("Installation did not complete successfully")
                return {
                    "status": "error",
                    "message": process.stdout + process.stderr
                }

            return {
                "status": "success",
                "output": "You can now replace DLSS with FSR Frame Gen!"
            }

        except subprocess.TimeoutExpired:
            decky.logger.error("Installation script timed out")
            return {
                "status": "error",
                "message": "Installation timed out"
            }
        except subprocess.CalledProcessError as e:
            decky.logger.error(f"Script error: {e.stderr}")
            return {
                "status": "error",
                "message": e.stderr
            }
        except Exception as e:
            decky.logger.error(f"Unexpected error:  {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def check_fgmod_path(self) -> dict:
        path = Path.home() / "fgmod"
        required_files = [
            "amd_fidelityfx_dx12.dll", "dlssg_to_fsr3_amd_is_better.dll", "libxess.dll",
            "amd_fidelityfx_vk.dll", "dlssg_to_fsr3.ini", "licenses",
            "d3dcompiler_47.dll", "dxgi.dll", "nvapi64.dll",
            "DisableNvidiaSignatureChecks.reg", "dxvk.conf", "_nvngx.dll",
            "dlss-enabler.dll", "fakenvapi.ini", "nvngx.ini",
            "dlss-enabler-upscaler.dll", "fgmod", "nvngx-wrapper.dll",
            "dlssg_to_fsr3_amd_is_better-3.0.dll", "fgmod-uninstaller.sh", "RestoreNvidiaSignatureChecks.reg"
        ]

        if os.path.exists(path):
            for file_name in required_files:
                if not os.path.exists(os.path.join(path, file_name)):
                    return {"exists": False}
            return {"exists": True}
        else:
            return {"exists": False}

    # New method to list installed Steam games
    async def list_installed_games(self) -> dict:
        try:
            steam_root = Path.home() / ".steam" / "steam"
            library_file = Path(steam_root) / "steamapps" / "libraryfolders.vdf"

            if not library_file.exists():
                return {"status": "error", "message": "libraryfolders.vdf not found"}

            library_paths = []
            with open(library_file, "r", encoding="utf-8") as file:
                for line in file:
                    if '"path"' in line:
                        path = line.split('"path"')[1].strip().strip('"').replace("\\\\", "/")
                        library_paths.append(path)

            games = []
            for library_path in library_paths:
                steamapps_path = Path(library_path) / "steamapps"
                if not steamapps_path.exists():
                    continue

                for appmanifest in steamapps_path.glob("appmanifest_*.acf"):
                    with open(appmanifest, "r", encoding="utf-8") as file:
                        game_info = {"appid": None, "name": None}
                        for line in file:
                            if '"appid"' in line:
                                game_info["appid"] = line.split('"appid"')[1].strip().strip('"')
                            if '"name"' in line:
                                game_info["name"] = line.split('"name"')[1].strip().strip('"')

                        if game_info["appid"] and game_info["name"]:
                            games.append(game_info)

            # Filter out games whose name contains "Proton" or "Steam Linux Runtime"
            filtered_games = [g for g in games if "Proton" not in g["name"] and "Steam Linux Runtime" not in g["name"]]

            return {"status": "success", "games": filtered_games}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def list_installed_non_steam_games(self) -> dict:
        try:
            non_steam = []

            steam_root = Path.home() / ".steam" / "steam"
            users_directory = Path(steam_root)/'userdata'

            for userd in os.listdir(users_directory):
                user_dir = Path(users_directory)/userd
                if not os.path.isdir(user_dir):
                    continue

                shortcuts_file = os.path.join(user_dir, 'config/shortcuts.vdf')

                if not os.path.exists(shortcuts_file):
                    continue

                shortcuts_vdf = binary_load(open(shortcuts_file, 'rb'))

                for sid, sval in shortcuts_vdf.get('shortcuts').items():
                    game_info = {}
                    appid = sval.get('appid')
                    if appid < 0:
                        appid = appid + (1 << 32)
                    game_info['appid'] = str(appid)
                    game_info['name'] = sval.get('AppName') or sval.get('appname')

                    if game_info["appid"] and game_info["name"]:
                        non_steam.append(game_info)

            filtered_non_steam_games = [g for g in non_steam if "Proton" not in g["name"] and "Steam Linux Runtime" not in g["name"]]

            return {"status": "success", "games": filtered_non_steam_games}

        except Exception as e:
            return {"status": "error", "message": str(e)}