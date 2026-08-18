import glob
import os
import platform
import shutil
import subprocess
from pathlib import Path

DRIVERS_DIR = Path(__file__).resolve().parent / ".drivers"

_BINARY_NAMES = {
    "chrome": "chromedriver",
    "firefox": "geckodriver",
}

_ENV_VARS = {
    "chrome": "CHROME_DRIVER",
    "firefox": "GECKO_DRIVER",
}


def _log(logger, level, message):
    if logger is None:
        print(f"[{level.upper()}] {message}")
        return
    log_fn = getattr(logger, level, None)
    if callable(log_fn):
        log_fn(message)
    else:
        print(message)


def _driver_filename(browser):
    name = _BINARY_NAMES[browser]
    if platform.system().lower() == "windows":
        return f"{name}.exe"
    return name


def _clean_path(value):
    if not value:
        return None
    cleaned = str(value).strip().strip("'").strip('"')
    return cleaned or None


def is_valid_driver_path(path):
    """True, если path — существующий исполняемый файл, а не строка версии."""
    cleaned = _clean_path(path)
    if not cleaned:
        return False
    if not os.path.isfile(cleaned):
        return False
    if platform.system().lower() == "windows":
        return True
    return os.access(cleaned, os.X_OK)


def get_chrome_version():
    try:
        system = platform.system().lower()
        if system == "windows":
            cmd = r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version'
            output = subprocess.check_output(cmd, shell=True).decode("utf-8")
            return output.strip().split()[-1]
        if system == "linux":
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/snap/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
            ]
            for path in chrome_paths:
                if os.path.exists(path):
                    try:
                        output = subprocess.check_output(
                            [path, "--version"], stderr=subprocess.STDOUT
                        ).decode("utf-8")
                        return output.strip().split()[-1]
                    except subprocess.CalledProcessError:
                        continue
            try:
                chrome_path = subprocess.check_output(["which", "google-chrome"]).decode("utf-8").strip()
                output = subprocess.check_output(
                    [chrome_path, "--version"], stderr=subprocess.STDOUT
                ).decode("utf-8")
                return output.strip().split()[-1]
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            return "Chrome не найден в системе"
        return f"Неподдерживаемая операционная система: {system}"
    except Exception as e:
        return f"Не удалось определить версию Chrome: {str(e)}"


def _is_notice_or_license(name):
    lowered = name.lower()
    return any(token in lowered for token in ("third_party", "license", "notice", "credits"))


def _looks_like_driver(path, binary_name):
    name = os.path.basename(path).lower()
    if _is_notice_or_license(name):
        return False
    expected = {binary_name, f"{binary_name}.exe"}
    return name in expected


def _pick_real_binary(path, binary_name):
    """webdriver-manager иногда возвращает THIRD_PARTY_NOTICES вместо бинарника."""
    cleaned = _clean_path(path)
    if cleaned and _looks_like_driver(cleaned, binary_name) and os.path.isfile(cleaned):
        return cleaned
    search_dir = os.path.dirname(cleaned) if cleaned else ""
    if search_dir and os.path.isdir(search_dir):
        for name in os.listdir(search_dir):
            candidate = os.path.join(search_dir, name)
            if os.path.isfile(candidate) and _looks_like_driver(candidate, binary_name):
                return candidate
    return cleaned


def _ensure_executable(path, logger=None):
    if platform.system().lower() != "linux":
        return
    try:
        os.chmod(path, 0o755)
    except Exception as e:
        _log(logger, "warning", f"Не удалось выставить права на выполнение для {path}: {e}")


def _copy_to_project_cache(src, browser, logger=None):
    DRIVERS_DIR.mkdir(parents=True, exist_ok=True)
    dest = DRIVERS_DIR / _driver_filename(browser)
    src_resolved = Path(src).resolve()
    dest_resolved = dest.resolve()
    if src_resolved == dest_resolved:
        _ensure_executable(str(dest_resolved), logger)
        return str(dest_resolved)
    shutil.copy2(src_resolved, dest_resolved)
    _ensure_executable(str(dest_resolved), logger)
    _log(logger, "info", f"Драйвер скопирован в кэш проекта: {dest_resolved}")
    return str(dest_resolved)


def _env_driver_path(browser):
    return _clean_path(os.getenv(_ENV_VARS[browser]))


def _system_driver_paths(browser):
    binary = _BINARY_NAMES[browser]
    filename = _driver_filename(browser)
    paths = [
        f"/usr/bin/{binary}",
        f"/usr/local/bin/{binary}",
        f"/opt/{binary}",
        f"/opt/{filename}",
        str(Path.cwd() / filename),
        str(Path.cwd() / binary),
    ]
    which_path = shutil.which(binary) or shutil.which(filename)
    if which_path:
        paths.insert(0, which_path)
    return paths


def _find_wdm_driver(browser):
    binary_name = _BINARY_NAMES[browser]
    wdm_root = Path.home() / ".wdm" / "drivers"
    if not wdm_root.exists():
        return None
    candidates = []
    for path in glob.glob(str(wdm_root / "**" / f"{binary_name}*"), recursive=True):
        if not os.path.isfile(path):
            continue
        if not _looks_like_driver(path, binary_name):
            continue
        candidates.append(path)
    if not candidates:
        return None
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]


def find_cached_driver(browser):
    """Ищет уже скачанный драйвер без обращения в сеть."""
    browser = browser.lower().strip()
    if browser not in _BINARY_NAMES:
        raise ValueError(f"Неподдерживаемый браузер: {browser}")

    env_path = _env_driver_path(browser)
    if is_valid_driver_path(env_path):
        return env_path

    project_path = DRIVERS_DIR / _driver_filename(browser)
    if is_valid_driver_path(project_path):
        return str(project_path)

    for path in _system_driver_paths(browser):
        if is_valid_driver_path(path):
            return path

    wdm_path = _find_wdm_driver(browser)
    if is_valid_driver_path(wdm_path):
        return wdm_path

    return None


def _install_via_wdm(browser, logger=None):
    binary_name = _BINARY_NAMES[browser]
    if browser == "chrome":
        from webdriver_manager.chrome import ChromeDriverManager

        _log(logger, "info", "Скачиваем ChromeDriver через webdriver-manager")
        raw = ChromeDriverManager().install()
    else:
        from webdriver_manager.firefox import GeckoDriverManager

        _log(logger, "info", "Скачиваем GeckoDriver через webdriver-manager")
        raw = GeckoDriverManager().install()

    picked = _pick_real_binary(raw, binary_name)
    if not picked or not os.path.isfile(picked):
        raise FileNotFoundError(f"webdriver-manager не вернул файл драйвера: {raw}")
    _log(logger, "info", f"webdriver-manager вернул: {picked}")
    return picked


def ensure_driver(browser, logger=None, refresh=False):
    """
    Возвращает путь к драйверу: кэш проекта / системы / ~/.wdm, иначе скачивает.

    refresh=True — при деплое пробует обновить драйвер через сеть и кладёт его в .drivers/.
    """
    browser = (browser or "").lower().strip()
    if browser not in _BINARY_NAMES:
        raise ValueError(f"Неподдерживаемый браузер: {browser}")

    cached = find_cached_driver(browser)
    if cached and not refresh:
        _log(logger, "info", f"Используем кэшированный драйвер {browser}: {cached}")
        return _copy_to_project_cache(cached, browser, logger)

    try:
        installed = _install_via_wdm(browser, logger)
        return _copy_to_project_cache(installed, browser, logger)
    except Exception as e:
        _log(logger, "warning", f"Не удалось скачать драйвер {browser}: {e}")
        if cached:
            _log(logger, "info", f"Переходим к локальному драйверу {browser}: {cached}")
            return _copy_to_project_cache(cached, browser, logger)
        binary = _BINARY_NAMES[browser]
        raise RuntimeError(
            f"Не удалось найти {binary}. Положите его в {DRIVERS_DIR} "
            f"или установите Chrome/Firefox и повторите обновление при доступе в интернет."
        ) from e
