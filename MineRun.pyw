"""
MineRun.py  —  v6.0
Gerenciador de servidor Minecraft.
"""

# ══════════════════════════════════════════════════════════════════════════════
#  BOOTSTRAP — verificação e instalação de dependências com splash screen
#  Roda antes de qualquer import pesado. Usa apenas stdlib.
# ══════════════════════════════════════════════════════════════════════════════
import importlib
import sys
import subprocess
import tkinter as tk
import tkinter.ttk as ttk

# Dependências gerenciadas automaticamente
# chave = nome do módulo para import  |  valor = nome do pacote para pip
_REQUIRED = {
    "psutil": "psutil",   # métricas de RAM/CPU do processo do servidor
    "nbtlib": "nbtlib",   # leitura de arquivos NBT (.dat) do Minecraft
}


def _check_missing() -> list[str]:
    """Retorna lista de nomes de pacotes pip que ainda não estão importáveis."""
    missing = []
    for mod, pkg in _REQUIRED.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(pkg)
    return missing


def _pip_install(pkg: str) -> "str | None":
    """Tenta instalar *pkg* via pip com três estratégias.

    Retorna None em caso de sucesso ou a mensagem de erro final.
    """
    base = [sys.executable, "-m", "pip", "install", "--quiet", pkg]
    strategies = [
        base,                                    # normal
        base + ["--break-system-packages"],      # ambientes externamente gerenciados (PEP 668)
        base + ["--user"],                       # fallback sem privilégios
    ]
    last_err = ""
    for cmd in strategies:
        try:
            subprocess.check_call(cmd,
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.PIPE)
            return None          # instalou com sucesso
        except subprocess.CalledProcessError as e:
            last_err = (e.stderr or b"").decode(errors="replace").strip()
        except Exception as e:
            last_err = str(e)
    return last_err or f"falha ao instalar {pkg}"


def _run_splash(missing: list[str]) -> list[str]:
    """Mostra splash screen enquanto instala dependências ausentes.

    Sempre exibe a janela (mesmo quando não há nada para instalar) para
    dar feedback visual de que o programa iniciou.

    Retorna lista de pacotes que falharam.
    """
    # ── Paleta inline (constantes ainda não foram definidas neste ponto) ──
    _BG       = "#0d0f18"
    _BG_HDR   = "#111522"
    _BG_CARD  = "#1c1f2e"
    _GREEN    = "#22c55e"
    _FG       = "#e2e5f0"
    _MUTED    = "#64748b"
    _RED      = "#ef4444"
    _BORDER   = "#252840"

    splash = tk.Tk()
    splash.overrideredirect(True)          # sem barra de título
    splash.configure(bg=_BORDER)          # borda de 1 px via bg externo
    splash.attributes("-topmost", True)

    W, H = 420, 190
    sw, sh = splash.winfo_screenwidth(), splash.winfo_screenheight()
    splash.geometry(f"{W}x{H}+{(sw - W)//2}+{(sh - H)//2}")

    # Frame interno (recuo de 1 px = borda visível)
    inner = tk.Frame(splash, bg=_BG)
    inner.pack(fill="both", expand=True, padx=1, pady=1)

    # ── Cabeçalho ──
    hdr = tk.Frame(inner, bg=_BG_HDR, pady=14)
    hdr.pack(fill="x")

    tk.Label(hdr, text="⛏  MineRun",
             bg=_BG_HDR, fg=_GREEN,
             font=("Segoe UI", 14, "bold")).pack()
    tk.Label(hdr, text="Gerenciador de Servidor Minecraft",
             bg=_BG_HDR, fg=_MUTED,
             font=("Segoe UI", 9)).pack(pady=(2, 0))

    # ── Separador ──
    tk.Frame(inner, bg=_BORDER, height=1).pack(fill="x")

    # ── Body ──
    body = tk.Frame(inner, bg=_BG, pady=14)
    body.pack(fill="both", expand=True)

    status_var = tk.StringVar(value="Verificando dependências…")
    status_lbl = tk.Label(body, textvariable=status_var,
                          bg=_BG, fg=_MUTED,
                          font=("Segoe UI", 9))
    status_lbl.pack(pady=(0, 10))

    # Barra de progresso estilizada
    style = ttk.Style(splash)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("S.Horizontal.TProgressbar",
                    background=_GREEN, troughcolor=_BG_CARD,
                    bordercolor=_BG, lightcolor=_GREEN, darkcolor=_GREEN,
                    thickness=4)
    pb = ttk.Progressbar(body, mode="indeterminate", length=320,
                         style="S.Horizontal.TProgressbar")
    pb.pack(pady=(0, 4))
    pb.start(10)

    # ── Rodapé ──
    tk.Frame(inner, bg=_BORDER, height=1).pack(fill="x")
    tk.Label(inner, text="v6.0  ·  Keven Castilho © 2026",
             bg=_BG_HDR, fg=_MUTED,
             font=("Segoe UI", 8)).pack(fill="x", pady=6)

    splash.update_idletasks()
    splash.update()

    failed: list[str] = []

    if not missing:
        status_var.set("Todas as dependências estão disponíveis.")
        splash.update()
        splash.after(700, splash.destroy)
        splash.mainloop()
        return failed

    total = len(missing)
    for i, pkg in enumerate(missing, 1):
        status_var.set(f"Instalando dependência {i}/{total}:  {pkg}…")
        status_lbl.config(fg=_MUTED)
        splash.update()

        err = _pip_install(pkg)

        if err:
            failed.append(pkg)
            status_var.set(f"Falha ao instalar  {pkg}.")
            status_lbl.config(fg=_RED)
        else:
            status_var.set(f"{pkg}  instalado com sucesso.")
            status_lbl.config(fg=_GREEN)
        splash.update()
        splash.after(300)
        splash.update()

    pb.stop()
    if failed:
        status_var.set(f"Atenção: {', '.join(failed)} não pôde ser instalado.")
        status_lbl.config(fg=_RED)
        splash.after(2200, splash.destroy)
    else:
        status_var.set("Tudo pronto!")
        status_lbl.config(fg=_GREEN)
        splash.after(500, splash.destroy)

    splash.mainloop()
    return failed


def _bootstrap_dependencies():
    """Ponto de entrada do bootstrap: verifica e instala, sempre com splash."""
    missing = _check_missing()
    failed  = _run_splash(missing)
    if failed:
        # Avisa no terminal mas não impede a execução — recursos serão desabilitados
        for pkg in failed:
            print(f"[MineRun] AVISO: não foi possível instalar '{pkg}'. "
                  f"Instale manualmente:  pip install {pkg}")


_bootstrap_dependencies()

# ══════════════════════════════════════════════════════════════════════════════
#  IMPORTS COMPLETOS  (dependências opcionais já foram tentadas acima)
# ══════════════════════════════════════════════════════════════════════════════
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
import base64
import json
import os
import re
import subprocess
import threading
import time
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox, simpledialog, ttk

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import nbtlib  # noqa — usado em _show_inventory_dialog
    HAS_NBTLIB = True
except ImportError:
    HAS_NBTLIB = False


# ══════════════════════════════════════════════════════════════════════════════
#  PALETA
# ══════════════════════════════════════════════════════════════════════════════
BG        = "#0d0f18"
BG_SIDEBAR= "#111320"
BG_HEADER = "#111522"
BG_CARD   = "#1c1f2e"
BG_INPUT  = "#0a0c14"
BORDER    = "#252840"

GREEN    = "#22c55e"
AMBER    = "#f59e0b"
ORANGE   = "#f97316"
RED      = "#ef4444"
RED_DARK = "#991b1b"
BLUE     = "#3b82f6"
PURPLE   = "#8b5cf6"

FG       = "#e2e5f0"
FG_MUTED = "#64748b"
FG_DIM   = "#2a2f45"

F_UI    = ("Segoe UI", 10)
F_BOLD  = ("Segoe UI", 10, "bold")
F_SM    = ("Segoe UI", 9)
F_XSM   = ("Segoe UI", 8)
F_TITLE = ("Segoe UI", 12, "bold")
F_MONO  = ("Consolas", 9)
F_MONO_B= ("Consolas", 9, "bold")
def _metric_color(pct: float, blink_on: bool = False) -> str:
    """Retorna a cor correta para RAM/CPU baseada em porcentagem (0‒100).

    0–25 %  → verde
    25–50 % → amarelo (AMBER)
    50–75 % → laranja
    75–90 % → vermelho
    90–99 % → vermelho escuro
    100 %   → pisca entre branco e vermelho escuro
    """
    if pct >= 100:
        return "#ffffff" if blink_on else RED_DARK
    if pct >= 90:
        return RED_DARK
    if pct >= 75:
        return RED
    if pct >= 50:
        return ORANGE
    if pct >= 25:
        return AMBER
    return GREEN


SCROLL_W  = 10
WIN_W, WIN_H = 1200, 740
MIN_W, MIN_H = 1060, 660
SIDEBAR_W    = 220
BTN_SLOT_W   = 130   # largura uniforme de todos os botões da toolbar


# ══════════════════════════════════════════════════════════════════════════════
#  GC OPTIONS  (nome exibido → flag JVM)
# ══════════════════════════════════════════════════════════════════════════════
GC_OPTIONS: dict[str, str] = {
    "Padrão (JVM decide)": "",
    "G1GC":               "-XX:+UseG1GC",
    "ZGC":                "-XX:+UseZGC",
    "Shenandoah":         "-XX:+UseShenandoahGC",
    "Serial":             "-XX:+UseSerialGC",
    "Parallel":           "-XX:+UseParallelGC",
}


# ═══════════════════════════════════════════════════════════════════════════════
#  SISTEMA DE EVENTOS UNIFICADO (v6.0)
# ══════════════════════════════════════════════════════════════════════════════
from collections import defaultdict
import re

@dataclass
class ServerEvent:
    """Evento unificado do servidor — um tipo, dados dinâmicos por tipo."""
    type: str
    raw: str | None = None          # linha original do log
    level: str | None = None        # "info" | "warn" | "error" | "chat" | "cmd" | "dim" | "muted"
    source: str | None = None       # "MineRun" | "Server" | etc
    player: str | None = None       # join/leave/chat/cmd
    message: str | None = None      # chat
    command: str | None = None      # command
    max_players: int | None = None  # startup_finished


class ServerLogParser:
    """Parser de logs do servidor Minecraft — retorna lista de ServerEvent por linha."""
    _PATTERNS: list[tuple[str, re.Pattern, callable]] = []

    def __init__(self):
        if not self._PATTERNS:
            self._compile_patterns()

    def _compile_patterns(self):
        # ── Join ──────────────────────────────────────────────────────────────
        # Padrão 1 (robusto, kernel do servidor): "Name[/ip:port] logged in with entity id"
        # Funciona em Vanilla, Spigot, Paper, Purpur, Folia, etc., em qualquer idioma.
        logged_in_pat = re.compile(
            r"([A-Za-z0-9_]{1,16})\[/[\d.:a-fA-F]+:\d+\]\s+logged in with entity id",
            re.IGNORECASE
        )
        # Padrão 2 (fallback): "Name joined the game"
        joined_game_pat = re.compile(
            r"(?<![A-Za-z0-9_])([A-Za-z0-9_]{1,16})\s+(?:joined the game|entrou no jogo)",
            re.IGNORECASE
        )

        # ── Leave ─────────────────────────────────────────────────────────────
        # Padrão 1 (robusto, kernel do servidor): "Name lost connection: motivo"
        lost_conn_pat = re.compile(
            r"(?<![A-Za-z0-9_])([A-Za-z0-9_]{1,16})\s+lost connection:",
            re.IGNORECASE
        )
        # Padrão 2 (fallback): "Name left the game"
        left_game_pat = re.compile(
            r"(?<![A-Za-z0-9_])([A-Za-z0-9_]{1,16})\s+(?:left the game|saiu do jogo)",
            re.IGNORECASE
        )

        chat_pat = re.compile(r"^\s*<([A-Za-z0-9_]{1,16})>\s*(.+)$")
        cmd_pat = re.compile(
            r".*\[(?:Server|[A-Za-z0-9_]{1,16})\]\s+([A-Za-z0-9_]{1,16})\s+issued server command:\s*(.+)$",
            re.IGNORECASE
        )
        startup_pat = re.compile(
            r"Done\s*\([\d.]+s\)!\s*For help, type",
            re.IGNORECASE
        )
        shutdown_pat = re.compile(
            r".*Stopping server|Server stopped|Saving worlds",
            re.IGNORECASE
        )

        self._PATTERNS = [
            # Join: "logged in" é mais confiável (kernel); "joined the game" é fallback (plugin)
            ("join", logged_in_pat, lambda m: ServerEvent(
                type="join", player=m.group(1), raw=m.group(0)
            )),
            ("join", joined_game_pat, lambda m: ServerEvent(
                type="join", player=m.group(1), raw=m.group(0)
            )),
            # Leave: "lost connection" é mais confiável (kernel); "left the game" é fallback (plugin)
            ("leave", lost_conn_pat, lambda m: ServerEvent(
                type="leave", player=m.group(1), raw=m.group(0)
            )),
            ("leave", left_game_pat, lambda m: ServerEvent(
                type="leave", player=m.group(1), raw=m.group(0)
            )),
            ("chat", chat_pat, lambda m: ServerEvent(
                type="chat", player=m.group(1), message=m.group(2), raw=m.group(0)
            )),
            ("command", cmd_pat, lambda m: ServerEvent(
                type="command", player=m.group(1), command=m.group(2), raw=m.group(0)
            )),
            ("startup_finished", startup_pat, lambda m: ServerEvent(
                type="startup_finished", raw=m.group(0)
            )),
            ("shutdown", shutdown_pat, lambda m: ServerEvent(
                type="shutdown", raw=m.group(0)
            )),
        ]

    # Regex para extrair o nível do prefixo Minecraft/Paper/Spigot
    # Suporta: [14:31:53 WARN]:  e  [Server thread/INFO]:
    _PREFIX_LEVEL = re.compile(
        r'\[(?:[\d: ]+|[\w /]+)/?(INFO|WARN|WARNING|ERROR|SEVERE|FATAL|DEBUG)\]',
        re.IGNORECASE
    )

    def parse(self, line: str) -> list[ServerEvent]:
        events = []
        # 1ª passagem: remove ANSI com ESC byte  (ESC[38;2;255;255;255m)
        clean_line = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', line)
        # 2ª passagem: remove ANSI bare sem ESC  ([38;2;255;255;255m)
        # Padrão seguro: [ + (digito+;)+ + digitos + m
        clean_line = re.sub(r'\[(?:[0-9]+;)+[0-9]*m', '', clean_line)
        ll = clean_line.lower()

        for _name, pattern, builder in self._PATTERNS:
            m = pattern.search(clean_line)
            if m:
                try:
                    events.append(builder(m))
                except Exception:
                    pass

        if not events:
            # Extrai nível do prefixo timestamp/thread (evita falsos positivos no corpo)
            prefix_m = self._PREFIX_LEVEL.search(clean_line)
            if prefix_m:
                extracted = prefix_m.group(1).upper()
                if extracted in ('WARN', 'WARNING'):
                    level = 'warn'
                elif extracted in ('ERROR', 'SEVERE', 'FATAL'):
                    level = 'error'
                else:
                    level = 'info'
            else:
                # Fallback para linhas sem prefixo (stack traces, continuações)
                if any(k in ll for k in ('exception in thread', 'caused by:',
                                         'at com.', 'at net.', 'at org.', 'at java.')):
                    level = 'error'
                elif clean_line.strip().startswith('<') and '>' in clean_line:
                    level = 'chat'
                elif 'issued server command' in ll:
                    level = 'cmd'
                else:
                    level = 'dim'

            events.append(ServerEvent(
                type='console',
                raw=line,  # Keep original with ANSI for display
                level=level,
                source='Server'
            ))

        return events


class EventDispatcher:
    """Dispatcher simples: registra handlers por tipo de evento e despacha."""
    def __init__(self):
        self._handlers: dict[str, list[callable]] = defaultdict(list)

    def on(self, event_type: str, handler: callable):
        self._handlers[event_type].append(handler)

    def off(self, event_type: str, handler: callable):
        if handler in self._handlers.get(event_type, []):
            self._handlers[event_type].remove(handler)

    def dispatch(self, event: ServerEvent):
        for h in self._handlers.get(event.type, []):
            try:
                h(event)
            except Exception as e:
                import traceback
                print(f"[EventDispatcher] Erro no handler {event.type}: {e}")
                traceback.print_exc()
        for h in self._handlers.get("*", []):
            try:
                h(event)
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════════════
#  PLAYER LISTS UNIFICADO (whitelist, banlist, ops, uuids) — v6.0
# ══════════════════════════════════════════════════════════════════════════════
class PlayerLists:
    """
    Estado sincronizado em memória: whitelist, banlist, ops, uuids.
    Recarregado sob demanda (sem watchdog).
    """
    def __init__(self, server_dir: str):
        self.server_dir = server_dir
        self.whitelist: set[str] = set()
        self.banlist: dict[str, dict] = {}      # name -> {reason, expires, ...}
        self.ops: set[str] = set()              # ops.json
        self.uuids: dict[str, str] = {}         # name -> uuid (futuro)
        self._load()

    def _load(self):
        base = Path(self.server_dir)
        if not base.exists():
            return

        # whitelist.json — array de {"name": "Steve", "uuid": "..."}
        wl = base / "whitelist.json"
        if wl.exists():
            try:
                data = json.loads(wl.read_text(encoding="utf-8"))
                for entry in data:
                    name = entry.get("name") if isinstance(entry, dict) else str(entry)
                    if name: self.whitelist.add(name)
            except Exception:
                pass

        # banned-players.json — array de {"name": "...", "uuid": "...", "reason": "...", "expires": "..."}
        bl = base / "banned-players.json"
        if bl.exists():
            try:
                data = json.loads(bl.read_text(encoding="utf-8"))
                for entry in data:
                    name = entry.get("name")
                    if name:
                        self.banlist[name] = {
                            "reason": entry.get("reason", ""),
                            "expires": entry.get("expires", ""),
                            "uuid": entry.get("uuid", ""),
                        }
            except Exception:
                pass

        # ops.json — array de {"name": "...", "uuid": "...", "level": 4, "bypassesPlayerLimit": false}
        opsf = base / "ops.json"
        if opsf.exists():
            try:
                data = json.loads(opsf.read_text(encoding="utf-8"))
                for entry in data:
                    name = entry.get("name") if isinstance(entry, dict) else str(entry)
                    if name: self.ops.add(name)
            except Exception:
                pass

    def reload(self):
        """Recarrega todos os arquivos do disco."""
        self.whitelist.clear()
        self.banlist.clear()
        self.ops.clear()
        self._load()

    # Helpers
    def is_whitelisted(self, name: str) -> bool:
        return name in self.whitelist

    def is_banned(self, name: str) -> bool:
        return name in self.banlist

    def is_op(self, name: str) -> bool:
        return name in self.ops

    def get_uuid(self, name: str) -> str | None:
        return self.uuids.get(name)


# ══════════════════════════════════════════════════════════════════════════════
#  AVATAR CACHE — Apenas gerencia arquivos (sem depender de Tkinter) — v6.0
# ══════════════════════════════════════════════════════════════════════════════
class AvatarCache:
    """
    Cache local de avatares em .cache/avatars/{name}.png.
    Não conhece Tkinter — apenas gerencia download e arquivos.
    O PlayerWidget decide como transformar em PhotoImage.
    """
    def __init__(self):
        self.dir = Path(__file__).parent / ".cache" / "avatars"
        self.dir.mkdir(parents=True, exist_ok=True)

    def get_path(self, name: str) -> Path | None:
        """Retorna Path do avatar se existir ou após download. None se falhar."""
        safe_name = re.sub(r'[^A-Za-z0-9_]', '_', name)
        path = self.dir / f"{safe_name}.png"
        if path.exists():
            return path
        # Download
        url = f"https://mc-heads.net/avatar/{safe_name}/20"
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=4) as r:
                data = r.read()
            path.write_bytes(data)
            return path
        except Exception:
            return None

# ══════════════════════════════════════════════════════════════════════════════
#  PLAYER TRACKER — mantém estado interno de quem está online
# ══════════════════════════════════════════════════════════════════════════════
class PlayerTracker:
    """
    Fonte-de-verdade dos jogadores online.

    Mantém um set interno alimentado pelos eventos de join/leave do log.
    Nao depende de /list, regex de idioma, plugins ou formato do servidor.
    Usa as mensagens do kernel (logged in / lost connection), que sao
    emitidas em qualquer engine (Vanilla, Spigot, Paper, Purpur, Folia...)
    e nao sao alteradas por plugins de idioma.

    Sincronizacao inicial: se RCON ou Query estiver disponivel, o
    MineRunApp preenche o estado logo apos o servidor ficar pronto.
    Se nenhum estiver, o set começa vazio e fica correto a partir
    do primeiro join/leave capturado.
    """

    def __init__(self) -> None:
        self._players: set[str] = set()

    # Mutacoes
    def join(self, name: str) -> None:
        self._players.add(name)

    def leave(self, name: str) -> None:
        self._players.discard(name)

    def clear(self) -> None:
        self._players.clear()

    def set_all(self, names: list) -> None:
        """Substitui todo o estado (sync via RCON/Query)."""
        self._players = set(names)

    # Leitura
    @property
    def count(self) -> int:
        return len(self._players)

    @property
    def players(self) -> list:
        return sorted(self._players)

    def __contains__(self, name: str) -> bool:
        return name in self._players


# ══════════════════════════════════════════════════════════════════════════════
#  MINECRAFT RCON CLIENT — protocolo TCP nativo, sem dependencias externas
# ══════════════════════════════════════════════════════════════════════════════
class MinecraftRcon:
    """
    Cliente RCON minimo para Minecraft (Source RCON Protocol).
    Nao requer bibliotecas externas; usa apenas socket da stdlib.

    Habilite no servidor:
        enable-rcon=true
        rcon.password=sua_senha
        rcon.port=25575   (padrao)
    """

    _TYPE_LOGIN    = 3
    _TYPE_COMMAND  = 2
    _TYPE_RESPONSE = 0

    def __init__(self, host="localhost", port=25575,
                 password="", timeout=5.0):
        self.host     = host
        self.port     = port
        self.password = password
        self.timeout  = timeout
        self._sock    = None
        self._req_id  = 1

    def connect(self) -> bool:
        """Conecta e autentica. Retorna True em caso de sucesso."""
        import socket as _socket
        try:
            self._sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
            self._sock.settimeout(self.timeout)
            self._sock.connect((self.host, self.port))
            return self._authenticate()
        except Exception:
            self._sock = None
            return False

    def disconnect(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    def command(self, cmd: str):
        """
        Envia um comando e retorna a resposta completa em texto (ou None em falha).
        Suporta respostas multi-packet via padding packet:
        envia segundo pacote vazio e coleta respostas ate ver o pad.
        """
        if not self._sock:
            return None
        try:
            self._req_id += 1
            cmd_id = self._req_id
            self._send_packet(cmd_id, self._TYPE_COMMAND, cmd)
            # Padding packet para detectar fim de resposta multi-packet
            self._req_id += 1
            pad_id = self._req_id
            self._send_packet(pad_id, self._TYPE_COMMAND, "")
            parts = []
            while True:
                rid, _rtype, payload = self._recv_packet()
                if rid == pad_id:
                    break
                if rid == cmd_id or rid == -1:
                    parts.append(payload)
            return "".join(parts)
        except Exception:
            return None

    def _authenticate(self) -> bool:
        self._send_packet(self._req_id, self._TYPE_LOGIN, self.password)
        rid, _type, _ = self._recv_packet()
        return rid == self._req_id

    def _send_packet(self, req_id: int, type_: int, payload: str) -> None:
        import struct
        data   = payload.encode("utf-8") + b"\x00\x00"
        length = 4 + 4 + len(data)
        packet = struct.pack("<iii", length, req_id, type_) + data
        self._sock.sendall(packet)

    def _recv_packet(self):
        import struct
        length_bytes = self._recv_exactly(4)
        (length,)    = struct.unpack("<i", length_bytes)
        data         = self._recv_exactly(length)
        req_id, type_ = struct.unpack("<ii", data[:8])
        payload      = data[8:-2].decode("utf-8", errors="replace")
        return req_id, type_, payload

    def _recv_exactly(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("Conexao RCON encerrada prematuramente")
            buf += chunk
        return buf


# ══════════════════════════════════════════════════════════════════════════════
#  MINECRAFT QUERY CLIENT — protocolo GameSpy4 UDP, sem dependencias externas
# ══════════════════════════════════════════════════════════════════════════════
class MinecraftQuery:
    """
    Cliente do protocolo GameSpy4 Query do Minecraft (UDP).
    Retorna a lista de jogadores diretamente do servidor.

    Habilite no servidor:
        enable-query=true
        query.port=25565   (padrao = mesmo de server-port)
    """

    _MAGIC = b"\xFE\xFD"

    def __init__(self, host="localhost", port=25565, timeout=3.0):
        self.host    = host
        self.port    = port
        self.timeout = timeout

    def get_players(self):
        """Retorna lista de nomes online, ou None se Query indisponivel."""
        import socket as _socket
        import struct
        try:
            sock = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            session_id = 1 & 0x0F0F0F0F

            # Handshake
            hs_pkt = self._MAGIC + b"\x09" + struct.pack(">i", session_id)
            sock.sendto(hs_pkt, (self.host, self.port))
            data, _ = sock.recvfrom(1024)
            token_str = data[5:].rstrip(b"\x00").decode("ascii", errors="replace")
            challenge = struct.pack(">i", int(token_str))

            # Full stat request
            req_pkt = (
                self._MAGIC + b"\x00"
                + struct.pack(">i", session_id)
                + challenge
                + b"\x00\x00\x00\x00"
            )
            sock.sendto(req_pkt, (self.host, self.port))
            data, _ = sock.recvfrom(4096)
            sock.close()

            # Secao de jogadores: "\x00\x01player_\x00\x00"
            marker = b"\x00\x01player_\x00\x00"
            idx = data.find(marker)
            if idx == -1:
                return []
            section = data[idx + len(marker):]
            if section.endswith(b"\x00\x00"):
                section = section[:-2]
            elif section.endswith(b"\x00"):
                section = section[:-1]
            if not section:
                return []
            return [p.decode("utf-8", errors="replace")
                    for p in section.split(b"\x00") if p]
        except Exception:
            return None

#  SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
SETTINGS_FILE = Path(__file__).with_name("minerun_settings.json")


@dataclass
class Settings:
    server_dir:  str = ""
    java_path:   str = "java"
    jar_path:    str = ""
    xms:         str = "1"
    xmx:         str = "4"
    gc:          str = "Padrão (JVM decide)"
    encoding:    str = "UTF-8"
    locale:      str = ""
    extra_args:  str = ""
    server_args: str = ""

    def save(self) -> None:
        SETTINGS_FILE.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False),
            encoding="utf-8")

    @classmethod
    def load(cls) -> "Settings":
        if SETTINGS_FILE.exists():
            try:
                raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                return cls(**{k: v for k, v in raw.items()
                              if k in cls.__dataclass_fields__})
            except Exception:
                pass
        return cls()

    def build_cmd(self) -> list:
        java = (self.java_path or "java").strip()
        cmd  = [java, f"-Xms{self.xms or 1}G", f"-Xmx{self.xmx or 4}G"]

        gc_flag = GC_OPTIONS.get(self.gc, self.gc)
        if gc_flag.strip():
            cmd.extend(gc_flag.split())

        if self.encoding.strip():
            cmd.append(f"-Dfile.encoding={self.encoding.strip()}")

        if self.locale.strip():
            parts = self.locale.strip().replace("-", "_").split("_")
            cmd.append(f"-Duser.language={parts[0]}")
            if len(parts) > 1:
                cmd.append(f"-Duser.country={parts[1]}")

        if self.extra_args.strip():
            cmd.extend(self.extra_args.split())

        cmd += ["-jar", self.jar_path, "--nogui"]

        if self.server_args.strip():
            cmd.extend(self.server_args.split())

        return cmd


# ══════════════════════════════════════════════════════════════════════════════
#  ESTADO DO SERVIDOR
# ══════════════════════════════════════════════════════════════════════════════
OFFLINE  = "offline"
STARTING = "starting"
ONLINE   = "online"
STOPPING = "stopping"

STATE_META = {
    OFFLINE:  (RED,   "Offline"),
    STARTING: (AMBER, "Iniciando…"),
    ONLINE:   (GREEN, "Online"),
    STOPPING: (AMBER, "Parando…"),
}

_POPEN_FLAGS: dict = {}
if os.name == "nt":
    _POPEN_FLAGS["creationflags"] = subprocess.CREATE_NO_WINDOW

# Regex para sanitizar linhas do servidor: remove caracteres de controle
# (exceto tab \x09) e o replacement char U+FFFD que aparece de encoding errado.
# O ESC (\x1b) é mantido aqui — é removido depois pelo strip_ansi do parser.
_CTRL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\ufffd]")


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS VISUAIS
# ══════════════════════════════════════════════════════════════════════════════
def _hex_lerp(c1: str, c2: str, t: float) -> str:
    c1, c2 = c1.lstrip("#"), c2.lstrip("#")
    r1,g1,b1 = int(c1[:2],16), int(c1[2:4],16), int(c1[4:],16)
    r2,g2,b2 = int(c2[:2],16), int(c2[2:4],16), int(c2[4:],16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))

def _darken(c: str, f=0.82)  -> str: return _hex_lerp(c, "#000000", 1-f)
def _lighten(c: str, f=0.18) -> str: return _hex_lerp(c, "#ffffff", f)


def lbl(parent, text="", font=F_UI, fg=FG, bg=None, anchor="w", **kw):
    return tk.Label(parent, text=text, font=font, fg=fg,
                    bg=bg if bg is not None else parent.cget("bg"),
                    anchor=anchor, **kw)


def sep(parent, color=BORDER, thickness=1, orient="h", **kw):
    if orient == "h":
        return tk.Frame(parent, bg=color, height=thickness, **kw)
    return tk.Frame(parent, bg=color, width=thickness, **kw)


def _show_ctx_popup(anchor, items: list, x: int, y: int) -> None:
    """
    Menu de contexto personalizado no tema escuro.
    items: lista de ("label", command, state) ou None para separador.
    state: "normal" | "disabled"
    """
    pop = tk.Toplevel(anchor)
    pop.overrideredirect(True)
    pop.configure(bg=BORDER)

    inner = tk.Frame(pop, bg=BG_CARD)
    inner.pack(fill="both", expand=True, padx=1, pady=1)

    _done = [False]

    def _close():
        if _done[0]:
            return
        _done[0] = True
        try:
            pop.destroy()
        except Exception:
            pass

    for item in items:
        if item is None:
            tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=8, pady=2)
            continue

        label, cmd, state = item
        disabled = (state == "disabled")

        row = tk.Label(inner, text=label, font=F_SM,
                       fg=FG_MUTED if disabled else FG,
                       bg=BG_CARD, anchor="w",
                       padx=14, pady=5,
                       cursor="arrow" if disabled else "hand2")
        row.pack(fill="x")

        if not disabled and cmd:
            def _enter(e, r=row):  r.config(bg="#264f78", fg=FG)
            def _leave(e, r=row):  r.config(bg=BG_CARD,   fg=FG)
            def _click(e, c=cmd):  _close(); c()
            row.bind("<Enter>",           _enter)
            row.bind("<Leave>",           _leave)
            row.bind("<ButtonRelease-1>", _click)

    pop.update_idletasks()
    pw = max(pop.winfo_reqwidth(), 190)
    ph = pop.winfo_reqheight()

    # Posicionamento multi-monitor: usa os limites da janela-pai em vez de
    # winfo_screenwidth/height (que retornam apenas o monitor principal).
    top = anchor.winfo_toplevel()
    top.update_idletasks()
    tx = top.winfo_rootx()
    ty = top.winfo_rooty()
    tw = top.winfo_width()
    th = top.winfo_height()
    # Prefere abrir para baixo-direita; inverte se nao couber dentro da janela
    px = x if (x + pw) <= tx + tw else max(tx, x - pw)
    py = y if (y + ph) <= ty + th else max(ty, y - ph)
    pop.geometry(f"{pw}x{ph}+{px}+{py}")
    pop.grab_set()
    pop.focus_set()

    # Fecha ao clicar FORA (grab redireciona cliques externos: e.widget == pop).
    # IMPORTANTE: nao fechar quando o clique e em um filho do popup (item de menu)
    # pois o ButtonPress chegaria antes do ButtonRelease que executa o comando.
    def _on_outside_click(e):
        if e.widget is pop:
            _close()  # clique foi redirecionado de fora do popup
    pop.bind("<ButtonPress-1>", _on_outside_click)
    pop.bind("<FocusOut>",      lambda e: pop.after(80, _close))
    pop.bind("<Escape>",        lambda e: _close())


def _show_styled_input(parent, title: str, prompt: str,
                        initial: str = "") -> "str | None":
    """Janela de input estilizada no tema escuro. Retorna o texto ou None se cancelado."""
    result = [None]

    top = parent.winfo_toplevel()
    pop = tk.Toplevel(top)
    pop.title(title)
    pop.configure(bg=BG)
    pop.resizable(False, False)
    pop.grab_set()
    pop.transient(top)

    # Header
    hdr = tk.Frame(pop, bg=BG_HEADER, pady=10)
    hdr.pack(fill="x")
    lbl(hdr, f"  {title}", font=F_BOLD, fg=FG, bg=BG_HEADER).pack(side="left", padx=10)
    sep(pop).pack(fill="x")

    # Body — Label com wraplength fixo para caber na largura do diálogo
    body = tk.Frame(pop, bg=BG, padx=20, pady=14)
    body.pack(fill="both", expand=True)
    tk.Label(body, text=prompt, font=F_UI, fg=FG_MUTED, bg=BG,
             wraplength=360, justify="left", anchor="w").pack(anchor="w", pady=(0, 6))

    var = tk.StringVar(value=initial)
    ent = styled_entry(body, textvariable=var, width=42)
    ent.pack(fill="x", ipady=5)
    ent.focus_set()
    if initial:
        ent.select_range(0, "end")

    # Footer
    sep(pop).pack(fill="x")
    foot = tk.Frame(pop, bg=BG_HEADER, pady=8)
    foot.pack(fill="x")

    # Centralizar após construir todos os widgets (altura real calculada pelo Tk)
    pop.update_idletasks()
    px, py = top.winfo_rootx(), top.winfo_rooty()
    pW, pH = top.winfo_width(), top.winfo_height()
    w = 400
    h = pop.winfo_reqheight()
    pop.geometry(f"{w}x{h}+{px + (pW - w)//2}+{py + (pH - h)//2}")

    def _ok(_=None):
        result[0] = var.get()
        pop.destroy()

    def _cancel(_=None):
        pop.destroy()

    Btn(foot, "Cancelar", color=BG_CARD, fg=FG_MUTED,
        command=_cancel).pack(side="right", padx=6)
    Btn(foot, "OK", color=GREEN, fg="#000",
        command=_ok).pack(side="right", padx=6)

    ent.bind("<Return>", _ok)
    ent.bind("<Escape>", _cancel)
    pop.bind("<Escape>", _cancel)

    top.wait_window(pop)
    return result[0]


def _show_styled_info(parent, title: str, lines: list) -> None:
    """Janela de informação estilizada no tema escuro."""
    top = parent.winfo_toplevel()
    pop = tk.Toplevel(top)
    pop.title(title)
    pop.configure(bg=BG)
    pop.resizable(False, False)
    pop.grab_set()
    pop.transient(top)

    pop.update_idletasks()
    px, py = top.winfo_rootx(), top.winfo_rooty()
    pW, pH = top.winfo_width(), top.winfo_height()
    w, h = 420, 60 + len(lines) * 28 + 60
    pop.geometry(f"{w}x{h}+{px + (pW - w)//2}+{py + (pH - h)//2}")

    hdr = tk.Frame(pop, bg=BG_HEADER, pady=10)
    hdr.pack(fill="x")
    lbl(hdr, f"  {title}", font=F_BOLD, fg=FG, bg=BG_HEADER).pack(side="left", padx=10)
    sep(pop).pack(fill="x")

    body = tk.Frame(pop, bg=BG, padx=20, pady=14)
    body.pack(fill="both", expand=True)
    for key, value in lines:
        row = tk.Frame(body, bg=BG)
        row.pack(fill="x", pady=2)
        lbl(row, f"{key}:", font=F_BOLD, fg=FG_MUTED, bg=BG, width=14, anchor="e").pack(side="left", padx=(0, 8))
        lbl(row, value, font=F_UI, fg=FG, bg=BG, anchor="w").pack(side="left")

    sep(pop).pack(fill="x")
    foot = tk.Frame(pop, bg=BG_HEADER, pady=8)
    foot.pack(fill="x")

    def _close(_=None): pop.destroy()

    Btn(foot, "Fechar", color=BG_CARD, fg=FG,
        command=_close).pack(side="right", padx=6)
    pop.bind("<Escape>", _close)
    pop.bind("<Return>", _close)

    top.wait_window(pop)


def _show_styled_confirm(parent, title: str, message: str) -> bool:
    """Diálogo de confirmação estilizado. Retorna True se confirmado."""
    result = [False]
    top = parent.winfo_toplevel()
    pop = tk.Toplevel(top)
    pop.title(title)
    pop.configure(bg=BG)
    pop.resizable(False, False)
    pop.grab_set()
    pop.transient(top)

    pop.update_idletasks()
    px, py = top.winfo_rootx(), top.winfo_rooty()
    pW, pH = top.winfo_width(), top.winfo_height()
    w, h = 400, 160
    pop.geometry(f"{w}x{h}+{px + (pW - w)//2}+{py + (pH - h)//2}")

    hdr = tk.Frame(pop, bg=BG_HEADER, pady=10)
    hdr.pack(fill="x")
    lbl(hdr, f"  ⚠  {title}", font=F_BOLD, fg=AMBER, bg=BG_HEADER).pack(side="left", padx=10)
    sep(pop).pack(fill="x")

    body = tk.Frame(pop, bg=BG, padx=20, pady=18)
    body.pack(fill="both", expand=True)
    for line in message.splitlines():
        lbl(body, line, font=F_UI, fg=FG, bg=BG).pack(anchor="w")

    sep(pop).pack(fill="x")
    foot = tk.Frame(pop, bg=BG_HEADER, pady=8)
    foot.pack(fill="x")

    def _yes(_=None):
        result[0] = True
        pop.destroy()

    def _no(_=None):
        pop.destroy()

    Btn(foot, "Cancelar", color=BG_CARD, fg=FG_MUTED, command=_no).pack(side="right", padx=6)
    Btn(foot, "Confirmar", color=RED, fg=FG, command=_yes).pack(side="right", padx=6)
    pop.bind("<Escape>", _no)

    top.wait_window(pop)
    return result[0]



def _show_inventory_dialog(parent, player_name: str, uuid: "str | None",
                           dat_file: "Path | None", playerdata_dir: Path) -> None:
    """Diálogo de inventário NBT — lê e exibe o conteúdo real do arquivo .dat."""

    # ── helpers de slot ───────────────────────────────────────────────────────
    _ARMOR_LABELS = {36: "Boots", 37: "Leggings", 38: "Chestplate", 39: "Helmet"}
    _SECTION = {
        **{i: "Hotbar" for i in range(0, 9)},
        **{i: "Inventory" for i in range(9, 36)},
        **{i: f"Armor ({_ARMOR_LABELS[i]})" for i in range(36, 40)},
        40: "Offhand",
    }

    def _fmt_id(raw: str) -> str:
        """minecraft:diamond_pickaxe → Diamond Pickaxe"""
        return raw.replace("minecraft:", "").replace("_", " ").title()

    def _parse_dat(path: Path) -> dict:
        """Lê o .dat gzip-NBT e devolve estrutura resumida.

        Compatível com:
          • Minecraft Java ≤ 1.20.4  (tag Compound, Count Byte, Enchantments List)
          • Minecraft Java ≥ 1.20.5  (components Compound, count Int, nova estrutura)
          • nbtlib 2.x (root transparente — File IS the root compound)
        """
        def _int_safe(v, default=0):
            """Converte v para int; retorna default (pode ser None) se falhar."""
            try:   return int(v)
            except Exception: return default

        def _float_safe(v, default=0.0) -> float:
            try:   return float(v)
            except Exception: return default

        def _str_safe(v, default="?") -> str:
            if v is None: return default
            try:   return str(v)
            except Exception: return default

        def _parse_enchs(tag_or_comp) -> list[str]:
            """Extrai encantamentos de qualquer formato de tag/components."""
            enchs = []
            if not tag_or_comp:
                return enchs
            # Formato antigo: tag.Enchantments = List[{id:String, lvl:Short}]
            if "Enchantments" in tag_or_comp:
                for e in tag_or_comp["Enchantments"]:
                    try:
                        eid  = _fmt_id(_str_safe(e.get("id", "?")))
                        elvl = _int_safe(e.get("lvl", 1))
                        enchs.append(f"{eid} {elvl}")
                    except Exception:
                        pass
                return enchs
            # Formato muito antigo: tag.ench = List[{id:Short, lvl:Short}]
            if "ench" in tag_or_comp:
                for e in tag_or_comp["ench"]:
                    try:
                        eid  = f"Ench#{_int_safe(e.get('id', 0))}"
                        elvl = _int_safe(e.get("lvl", e.get("l", 1)))
                        enchs.append(f"{eid} {elvl}")
                    except Exception:
                        pass
                return enchs
            # Formato 1.20.5+: components["minecraft:enchantments"].levels = {id_str: Int}
            if "minecraft:enchantments" in tag_or_comp:
                try:
                    ench_data = tag_or_comp["minecraft:enchantments"]
                    levels = ench_data.get("levels", ench_data) if hasattr(ench_data, "get") else ench_data
                    for eid, elvl in (levels.items() if hasattr(levels, "items") else []):
                        enchs.append(f"{_fmt_id(_str_safe(eid))} {_int_safe(elvl)}")
                except Exception:
                    pass
            return enchs

        def _parse_item(entry) -> dict:
            """Extrai campos de um item NBT (ambos os formatos)."""
            # Slot: manteve-se capitalized em player.dat em todas as versões conhecidas.
            # Aceita qualquer inteiro — MC usa signed byte (ex.: offhand = 40 no player.dat,
            # mas algumas representações modded usam negativos; não rejeitamos nenhum valor.)
            raw_slot = entry.get("Slot", entry.get("slot"))
            if raw_slot is None:
                raise KeyError("sem campo Slot/slot no item")
            slot = _int_safe(raw_slot, None)
            if slot is None:
                raise ValueError(f"Slot não é um inteiro: {raw_slot!r}")

            item_id = _str_safe(entry.get("id"), "minecraft:air")

            # Count (≤1.20.4 = Byte) → count (≥1.20.5 = Int)
            count = _int_safe(
                entry.get("Count", entry.get("count", 1)), 1)

            # tag (antigo) ou components (1.20.5+)
            extras = entry.get("tag") or entry.get("components") or {}

            # Damage: tag.Damage (antigo) ou components["minecraft:damage"] (novo)
            dmg = 0
            if extras:
                if "Damage" in extras:
                    dmg = _int_safe(extras["Damage"])
                elif "minecraft:damage" in extras:
                    dmg = _int_safe(extras["minecraft:damage"])

            enchs = _parse_enchs(extras)
            return {"slot": slot, "id": item_id, "count": count,
                    "dmg": dmg, "enchs": enchs}

        try:
            import nbtlib
        except ImportError:
            return {"error": "nbtlib não instalado (pip install nbtlib)",
                    "items": {}, "ender": {}, "stats": {},
                    "item_errors": [], "raw_keys": []}

        try:
            nbt  = nbtlib.load(str(path))
            # nbtlib 2.x: File IS the root compound — nbt.get("", nbt) returns nbt itself
            root = nbt.get("", nbt)

            raw_keys = list(root.keys())

            # ── Inventário ────────────────────────────────────────────────────
            items: dict[int, dict] = {}
            item_errors: list[str] = []
            for i, entry in enumerate(root.get("Inventory", [])):
                try:
                    parsed = _parse_item(entry)
                    items[parsed["slot"]] = {k: v for k, v in parsed.items() if k != "slot"}
                except Exception as ex:
                    keys = list(entry.keys()) if hasattr(entry, "keys") else "?"
                    item_errors.append(f"slot#{i}: {ex} (chaves={keys})")

            # ── Ender Chest ───────────────────────────────────────────────────
            ender: dict[int, dict] = {}
            ender_errors: list[str] = []
            for i, entry in enumerate(root.get("EnderItems", [])):
                try:
                    parsed = _parse_item(entry)
                    ender[parsed["slot"]] = {
                        "id":    parsed["id"],
                        "count": parsed["count"],
                    }
                except Exception as ex:
                    keys = list(entry.keys()) if hasattr(entry, "keys") else "?"
                    ender_errors.append(f"slot#{i}: {ex} (chaves={keys})")

            # ── Stats — cada campo em try/except independente ─────────────────
            def _stat(key, conv, default):
                v = root.get(key)
                if v is None:
                    return default
                try:
                    return conv(v)
                except Exception:
                    return default

            pos: list[float] = []
            try:
                pos = [round(_float_safe(v), 2) for v in root.get("Pos", [])]
            except Exception:
                pass

            # Dimension: Int em MC ≤ 1.15 (-1/0/1), String em ≥ 1.16
            raw_dim = root.get("Dimension", "?")
            if raw_dim is not None and _int_safe(raw_dim, -999) != -999 and not isinstance(raw_dim, str):
                dim_map = {-1: "Nether", 0: "Overworld", 1: "The End"}
                dim = dim_map.get(_int_safe(raw_dim), str(raw_dim))
            else:
                dim = _str_safe(raw_dim, "?")

            stats = {
                "health":   round(_stat("Health",   float, 20.0), 1),
                "food":     _stat("foodLevel", int,   20),
                "xp_level": _stat("XpLevel",   int,   0),
                "xp_total": _stat("XpTotal",   int,   0),
                "pos":      pos,
                "dim":      dim,
            }

            return {
                "items":        items,
                "ender":        ender,
                "stats":        stats,
                "item_errors":  item_errors,
                "ender_errors": ender_errors,
                "raw_keys":     raw_keys,
                "error":        None,
            }

        except Exception as ex:
            import traceback
            return {
                "error":        f"{type(ex).__name__}: {ex}",
                "detail":       traceback.format_exc(),
                "items":        {}, "ender": {}, "stats": {},
                "item_errors":  [], "ender_errors": [], "raw_keys": [],
            }

    # ── montar UI ─────────────────────────────────────────────────────────────
    top = parent.winfo_toplevel()
    pop = tk.Toplevel(top)
    pop.title(f"Inventário — {player_name}")
    pop.configure(bg=BG)
    pop.resizable(True, True)
    pop.grab_set()
    pop.transient(top)
    pop.minsize(560, 420)

    # -- Header
    hdr = tk.Frame(pop, bg=BG_HEADER, pady=10)
    hdr.pack(fill="x")
    lbl(hdr, f"  🎒  {player_name}", font=F_BOLD, fg=FG, bg=BG_HEADER).pack(side="left", padx=10)
    if uuid:
        lbl(hdr, f"UUID: {uuid}  ", font=F_XSM, fg=FG_MUTED, bg=BG_HEADER).pack(side="right", padx=10)
    sep(pop).pack(fill="x")

    body = tk.Frame(pop, bg=BG)
    body.pack(fill="both", expand=True, padx=16, pady=12)

    if dat_file is None:
        msg = ("Arquivo .dat não encontrado." if uuid else
               "UUID do jogador não disponível.\nAdicione-o à whitelist ou ops para registrar o UUID.")
        lbl(body, msg, font=F_UI, fg=FG_MUTED, bg=BG).pack(anchor="center", expand=True)
    else:
        data = _parse_dat(dat_file)
        if data["error"]:
            # Erro crítico ao abrir o arquivo
            err_frame = tk.Frame(body, bg=BG)
            err_frame.pack(fill="both", expand=True, anchor="w")
            lbl(err_frame, f"⚠  Erro ao ler o arquivo NBT:", font=F_BOLD, fg=RED, bg=BG).pack(anchor="w", pady=(4,2))
            lbl(err_frame, data["error"], font=F_SM, fg=RED, bg=BG, wraplength=520, justify="left").pack(anchor="w")
            detail = data.get("detail", "")
            if detail:
                lbl(err_frame, "Detalhes (traceback):", font=F_XSM, fg=FG_MUTED, bg=BG).pack(anchor="w", pady=(8,2))
                det_txt = tk.Text(err_frame, bg=BG_CARD, fg=FG_MUTED, font=("Consolas",8),
                                  height=8, relief="flat", state="normal", wrap="word")
                det_txt.insert("1.0", detail)
                det_txt.config(state="disabled")
                det_txt.pack(fill="both", expand=True, padx=0, pady=(0,4))
        else:
            # ── Stats strip ──────────────────────────────────────────────
            stats = data["stats"]
            sf = tk.Frame(body, bg=BG_CARD, padx=12, pady=6)
            sf.pack(fill="x", pady=(0, 6))
            stat_items = [
                (f"❤  {stats['health']}/20", GREEN if stats['health'] > 14 else
                       AMBER if stats['health'] > 6 else RED),
                (f"🍗  {stats['food']}/20",  GREEN if stats['food'] > 14 else
                       AMBER if stats['food'] > 6 else RED),
                (f"✨  Nível {stats['xp_level']}  ({stats['xp_total']} XP total)", BLUE),
            ]
            if stats["pos"]:
                x, y, z = stats["pos"]
                stat_items.append((f"📍  X{x} Y{y} Z{z}  [{stats['dim']}]", FG_MUTED))
            for txt, clr in stat_items:
                lbl(sf, txt, font=F_SM, fg=clr, bg=BG_CARD).pack(side="left", padx=10)

            # Avisos de itens com erro de parse (não críticos)
            item_errors  = data.get("item_errors", [])
            ender_errors = data.get("ender_errors", [])
            all_errors   = (
                [f"Inv — {e}" for e in item_errors[:3]] +
                [f"Ender — {e}" for e in ender_errors[:2]]
            )
            if all_errors:
                warn_txt = f"⚠  {len(item_errors)+len(ender_errors)} item(ns) ignorado(s): " + " | ".join(all_errors)
                lbl(body, warn_txt, font=F_XSM, fg=AMBER, bg=BG,
                    wraplength=560, justify="left").pack(anchor="w", pady=(0, 4))

            # ── Notebook manual (duas abas: Inventário / Ender Chest) ────
            tab_bar = tk.Frame(body, bg=BG_HEADER)
            tab_bar.pack(fill="x")
            content_frame = tk.Frame(body, bg=BG)
            content_frame.pack(fill="both", expand=True, pady=(4, 0))

            def _make_tree(parent_f):
                cols = ("slot", "secao", "item", "qtd", "obs")
                tree = ttk.Treeview(parent_f, columns=cols, show="headings",
                                    style="Dark.Treeview")
                for col, hd, w in [("slot","Slot",55),("secao","Seção",130),
                                    ("item","Item",200),("qtd","Qtd",45),("obs","Info",130)]:
                    tree.heading(col, text=hd)
                    tree.column(col, width=w, anchor="w" if col not in ("slot","qtd") else "center")
                sb = tk.Scrollbar(parent_f, orient="vertical", command=tree.yview)
                tree.configure(yscrollcommand=sb.set)
                sb.pack(side="right", fill="y")
                tree.pack(fill="both", expand=True)
                return tree

            # Estilos Treeview dark
            style = ttk.Style()
            style.theme_use("default")
            style.configure("Dark.Treeview",
                background=BG_INPUT, foreground=FG, fieldbackground=BG_INPUT,
                rowheight=22, font=F_SM)
            style.configure("Dark.Treeview.Heading",
                background=BG_CARD, foreground=FG_MUTED, font=F_XSM)
            style.map("Dark.Treeview", background=[("selected", "#264f78")])

            # Frames de conteúdo para cada aba
            frames = {}
            tabs   = {}
            # Aba extra de diagnóstico se inventário vazio com chaves conhecidas
            raw_keys  = data.get("raw_keys", [])
            has_items = bool(data["items"])
            tab_names = [("inv", "🎒  Inventário"), ("ender", "📦  Ender Chest")]
            if not has_items and raw_keys:
                tab_names.append(("diag", "🔍  Diagnóstico"))

            def _switch_tab(name):
                for n, f in frames.items():
                    f.pack_forget()
                frames[name].pack(fill="both", expand=True)
                for n, b in tabs.items():
                    b.config(bg=BG_CARD if n != name else BG_INPUT,
                             fg=FG_MUTED if n != name else FG)

            for key, label in tab_names:
                frames[key] = tk.Frame(content_frame, bg=BG)
                b = tk.Button(tab_bar, text=label, font=F_SM,
                              bg=BG_CARD, fg=FG_MUTED, relief="flat",
                              activebackground=BG_INPUT, activeforeground=FG,
                              padx=10, pady=4, bd=0,
                              command=lambda k=key: _switch_tab(k))
                b.pack(side="left")
                tabs[key] = b

            # Preenche inventário
            inv_tree = _make_tree(frames["inv"])
            items = data["items"]
            if items:
                for slot in sorted(items):
                    it  = items[slot]
                    obs = ""
                    if it["dmg"]:
                        obs += f"Dmg:{it['dmg']} "
                    if it["enchs"]:
                        obs += ", ".join(it["enchs"])
                    inv_tree.insert("", "end", values=(
                        slot, _SECTION.get(slot, f"Slot {slot}"),
                        _fmt_id(it["id"]), it["count"], obs.strip()
                    ))
            else:
                inv_tree.insert("", "end", values=("—", "—", "(inventário vazio)", "—", ""))

            # Preenche Ender Chest
            ender_tree = _make_tree(frames["ender"])
            ender = data["ender"]
            if ender:
                for slot in sorted(ender):
                    it = ender[slot]
                    ender_tree.insert("", "end", values=(
                        slot, f"Ender [{slot}]", _fmt_id(it["id"]), it["count"], ""
                    ))
            else:
                ender_tree.insert("", "end", values=("—", "—", "(ender chest vazio)", "—", ""))

            # Aba de diagnóstico: mostra chaves brutas do NBT
            if "diag" in frames:
                diag_f = frames["diag"]
                lbl(diag_f, "Chaves encontradas no NBT raiz do jogador:",
                    font=F_SM, fg=FG_MUTED, bg=BG).pack(anchor="w", pady=(8,4))
                keys_txt = tk.Text(diag_f, bg=BG_CARD, fg=GREEN, font=("Consolas",9),
                                   height=10, relief="flat", state="normal", wrap="word")
                keys_txt.insert("1.0", "\n".join(raw_keys))
                keys_txt.config(state="disabled")
                keys_txt.pack(fill="both", expand=True, padx=4, pady=(0,4))
                lbl(diag_f,
                    "Inventário vazio pode indicar: jogador nunca logou, "
                    "formato MC não reconhecido, ou arquivo desatualizado (logue/deslogue no servidor).",
                    font=F_XSM, fg=FG_MUTED, bg=BG, wraplength=520, justify="left"
                    ).pack(anchor="w", pady=(4,0))

            _switch_tab("inv")

    # -- Footer
    sep(pop).pack(fill="x")
    foot = tk.Frame(pop, bg=BG_HEADER, pady=8)
    foot.pack(fill="x")

    def _close(_=None): pop.destroy()

    if dat_file:
        def _open_folder():
            try:
                import platform
                if platform.system() == "Windows":
                    subprocess.Popen(["explorer", "/select,", str(dat_file)])
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", str(dat_file.parent)])
                else:
                    subprocess.Popen(["xdg-open", str(dat_file.parent)])
            except Exception:
                pass
        Btn(foot, "📁  Abrir Pasta", color=BG_CARD, fg=FG_MUTED,
            command=_open_folder).pack(side="left", padx=6)

    Btn(foot, "Fechar", color=BG_CARD, fg=FG,
        command=_close).pack(side="right", padx=6)
    pop.bind("<Escape>", _close)

    # Centralizar
    pop.update_idletasks()
    px, py = top.winfo_rootx(), top.winfo_rooty()
    pW, pH = top.winfo_width(), top.winfo_height()
    w, h = 600, 500
    pop.geometry(f"{w}x{h}+{px + (pW - w)//2}+{py + (pH - h)//2}")

    top.wait_window(pop)


def _bind_entry_ctx(entry: tk.Entry) -> None:
    """Adiciona menu de contexto estilizado a qualquer tk.Entry."""
    def _show(e):
        has_sel = entry.selection_present()
        try:
            has_clip = bool(entry.clipboard_get())
        except tk.TclError:
            has_clip = False

        # Captura selecao e texto agora, antes do popup roubar o foco
        try:
            sel_text = entry.selection_get() if has_sel else ""
        except tk.TclError:
            sel_text = ""

        def _recortar():
            if sel_text:
                entry.clipboard_clear()
                entry.clipboard_append(sel_text)
            entry.focus_set()
            entry.event_generate("<<Cut>>")

        def _copiar():
            if sel_text:
                entry.clipboard_clear()
                entry.clipboard_append(sel_text)
            else:
                entry.focus_set()
                entry.event_generate("<<Copy>>")

        def _colar():
            entry.focus_set()
            entry.event_generate("<<Paste>>")

        def _sel_all():
            entry.focus_set()
            entry.selection_range(0, "end")
            entry.icursor("end")

        items = [
            ("Recortar",        _recortar, "normal" if has_sel  else "disabled"),
            ("Copiar",          _copiar,   "normal" if has_sel  else "disabled"),
            ("Colar",           _colar,    "normal" if has_clip else "disabled"),
            None,
            ("Selecionar tudo", _sel_all,  "normal"),
        ]
        _show_ctx_popup(entry, items, e.x_root, e.y_root)

    entry.bind("<Button-3>", _show)


def styled_entry(parent, textvariable=None, width=30, **kw):
    cfg = dict(bg=BG_INPUT, fg=FG, font=F_UI, relief="flat",
               insertbackground=GREEN, bd=0,
               highlightthickness=1, highlightbackground=BORDER,
               highlightcolor=GREEN, width=width)
    if textvariable:
        cfg["textvariable"] = textvariable
    cfg.update(kw)
    e = tk.Entry(parent, **cfg)
    _bind_entry_ctx(e)
    return e


# ══════════════════════════════════════════════════════════════════════════════
#  BOTÃO
# ══════════════════════════════════════════════════════════════════════════════
class Btn(tk.Button):

    def __init__(self, parent, text="", color=BG_CARD, fg=FG,
                 disabled_color=FG_DIM, font=F_BOLD, padx=14, pady=7, **kw):
        self._color   = color
        self._hover   = _lighten(color, 0.12)
        self._press   = _darken(color, 0.85)
        self._dis_clr = disabled_color
        super().__init__(parent, text=text, fg=fg,
                         bg=color, activeforeground=fg,
                         activebackground=self._hover,
                         font=font, relief="flat", bd=0,
                         cursor="hand2", padx=padx, pady=pady, **kw)
        self.bind("<Enter>",           lambda _: self._e())
        self.bind("<Leave>",           lambda _: self._l())
        self.bind("<Button-1>",        lambda _: self._p())
        self.bind("<ButtonRelease-1>", lambda _: self._r())

    def _e(self):
        if self["state"] != "disabled": self.config(bg=self._hover)
    def _l(self):
        if self["state"] != "disabled": self.config(bg=self._color)
    def _p(self):
        if self["state"] != "disabled": self.config(bg=self._press)
    def _r(self):
        if self["state"] != "disabled": self.config(bg=self._hover)

    def enable(self):
        self.config(state="normal", bg=self._color,
                    activebackground=self._hover, cursor="hand2")

    def disable(self):
        self.config(state="disabled", bg=self._dis_clr,
                    activebackground=self._dis_clr, cursor="")


# ══════════════════════════════════════════════════════════════════════════════
#  FILTER BUTTON  (pill toggle)
# ══════════════════════════════════════════════════════════════════════════════
class FilterBtn(tk.Label):

    def __init__(self, parent, text, color, on_toggle=None, **kw):
        self._on_bg  = color
        self._off_bg = _hex_lerp(color, BG_HEADER, 0.8)
        self._on_fg  = "#000" if color in (GREEN, AMBER) else FG
        self._off_fg = FG_DIM
        self._active = True
        self._cb     = on_toggle
        super().__init__(parent, text=text, font=F_XSM,
                         bg=color, fg=self._on_fg,
                         cursor="hand2", padx=9, pady=3,
                         relief="flat", **kw)
        self.bind("<Button-1>", self._toggle)

    def _toggle(self, _=None):
        self._active = not self._active
        self.config(bg=self._on_bg  if self._active else self._off_bg,
                    fg=self._on_fg  if self._active else self._off_fg)
        if self._cb:
            self._cb(self._active)

    @property
    def active(self) -> bool:
        return self._active


# ══════════════════════════════════════════════════════════════════════════════
#  SCROLLBAR CUSTOMIZADA
# ══════════════════════════════════════════════════════════════════════════════
class FlatScrollbar(tk.Canvas):

    TRACK = "#0d0f18"
    THUMB = "#2e3450"
    HOVER = "#3d4470"
    PRESS = "#4a527f"

    def __init__(self, parent, width=SCROLL_W, command=None, **kw):
        super().__init__(parent, width=width, bg=self.TRACK,
                         highlightthickness=0, relief="flat", **kw)
        self._cmd = command
        self._top = 0.0; self._bot = 1.0
        self._drag = False; self._dy0 = 0; self._dt0 = 0.0
        self._hov  = False
        self.bind("<Configure>",          self._draw)
        self.bind("<ButtonPress-1>",      self._click)
        self.bind("<B1-Motion>",          self._drag_move)
        self.bind("<ButtonRelease-1>",    self._release)
        self.bind("<MouseWheel>",         self._wheel)
        self.bind("<Enter>", lambda _: self._set_hov(True))
        self.bind("<Leave>", lambda _: self._set_hov(False))

    def set(self, lo, hi):
        self._top = float(lo); self._bot = float(hi); self._draw()

    def _draw(self, *_):
        self.delete("all")
        h, w = self.winfo_height(), self.winfo_width()
        if h < 2: return
        r = w // 2
        self._rr(2, 2, w-2, h-2, r, self.TRACK)
        ty = max(4, int(self._top * h))
        by = max(min(h-4, int(self._bot * h)), ty + 16)
        c  = self.PRESS if self._drag else self.HOVER if self._hov else self.THUMB
        self._rr(2, ty, w-2, by, r, c)

    def _rr(self, x1, y1, x2, y2, r, fill):
        r = min(r, (x2-x1)//2, (y2-y1)//2)
        if r < 1:
            self.create_rectangle(x1,y1,x2,y2,fill=fill,outline=""); return
        for sx,sy,st in [(x1,y1,90),(x2-2*r,y1,0),(x1,y2-2*r,180),(x2-2*r,y2-2*r,270)]:
            self.create_arc(sx,sy,sx+2*r,sy+2*r,start=st,extent=90,fill=fill,outline="")
        self.create_rectangle(x1+r,y1,  x2-r,y2,  fill=fill,outline="")
        self.create_rectangle(x1,  y1+r,x2,  y2-r,fill=fill,outline="")

    def _thumb_bounds(self):
        h = self.winfo_height()
        ty = max(4, int(self._top * h))
        return ty, max(min(h-4, int(self._bot * h)), ty+16)

    def _click(self, e):
        ty, by = self._thumb_bounds()
        if ty <= e.y <= by:
            self._drag = True; self._dy0 = e.y; self._dt0 = self._top
        else:
            vis = self._bot - self._top
            self._goto(max(0., self._top-vis) if e.y < ty
                       else min(1.-vis, self._top+vis))
        self._draw()

    def _drag_move(self, e):
        if not self._drag: return
        vis = self._bot - self._top
        self._goto(max(0., min(1.-vis, self._dt0+(e.y-self._dy0)/self.winfo_height())))

    def _release(self, _): self._drag = False; self._draw()

    def _wheel(self, e):
        if self._cmd: self._cmd("scroll", -1 if e.delta > 0 else 1, "units")

    def _goto(self, pos):
        if self._cmd: self._cmd("moveto", pos)
        vis = self._bot - self._top
        self._top, self._bot = pos, pos + vis
        self._draw()

    def _set_hov(self, v): self._hov = v; self._draw()


# ══════════════════════════════════════════════════════════════════════════════
#  SERVER CONTROLLER  — toda a lógica de processo vive aqui
# ══════════════════════════════════════════════════════════════════════════════
class ServerController:
    """
    Gerencia o processo Java do servidor.
    Não depende de tkinter — comunica via callbacks.
    """

    def __init__(self):
        self.proc: subprocess.Popen | None = None
        self.state: str        = OFFLINE
        self.uptime_start: float | None    = None

        # Callbacks configurados pelo MineRunApp (sempre agendados via root.after)
        self.on_line:         object = None   # (line: str)  → None
        self.on_state_change: object = None   # (state: str) → None

    @property
    def running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def start(self, settings: Settings) -> str | None:
        """Inicia o servidor. Retorna mensagem de erro ou None em caso de sucesso."""
        cmd = settings.build_cmd()
        cwd = settings.server_dir or str(Path(settings.jar_path).parent)
        try:
            self.proc = subprocess.Popen(
                cmd, cwd=cwd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True, bufsize=1, encoding="utf-8", errors="ignore",
                **_POPEN_FLAGS)
        except FileNotFoundError:
            return f"Java não encontrado: '{cmd[0]}'"
        except Exception as e:
            return str(e)
        self.uptime_start = time.time()
        threading.Thread(target=self._reader, daemon=True).start()
        return None

    def stop(self) -> None:
        if not self.proc: return
        try:
            self.proc.stdin.write("stop\n")
            self.proc.stdin.flush()
        except Exception:
            try: self.proc.terminate()
            except Exception: pass

    def force_kill(self) -> None:
        if self.proc and self.proc.poll() is None:
            try: self.proc.kill()
            except Exception: pass

    def send(self, cmd: str) -> None:
        if self.proc:
            try:
                self.proc.stdin.write(cmd + "\n")
                self.proc.stdin.flush()
            except Exception:
                pass

    def _reader(self) -> None:
        try:
            for raw in self.proc.stdout:
                line = _CTRL_CHARS_RE.sub("", raw.rstrip("\r\n"))
                if self.on_line:
                    self.on_line(line)
        except Exception:
            pass
        if self.on_state_change:
            self.on_state_change("_ended")


# ══════════════════════════════════════════════════════════════════════════════
#  CONSOLE WIDGET  — abstração sobre tk.Text
# ══════════════════════════════════════════════════════════════════════════════
class ConsoleWidget(tk.Frame):
    """
    Widget de console com camada de abstração.
    O restante do código nunca fala diretamente com o tk.Text interno.
    """

    _TAG_COLORS: dict[str, str] = {
        "info":    BLUE,
        "warn":    AMBER,
        "error":   RED,
        "chat":    PURPLE,
        "cmd":     GREEN,
        "success": GREEN,
        "muted":   FG_MUTED,
        "dim":     FG_DIM,
        "default": FG,
    }

    _FILTER_MAP: dict[str, set] = {
        "INFO":  {"info", "default", "success"},
        "WARN":  {"warn"},
        "ERROR": {"error"},
        "CHAT":  {"chat"},
        "CMD":   {"cmd"},
        "SYS":   {"muted", "dim"},
    }

    _FILTER_COLORS: dict[str, str] = {
        "INFO":  BLUE,
        "WARN":  AMBER,
        "ERROR": RED,
        "CHAT":  PURPLE,
        "CMD":   GREEN,
        "SYS":   FG_MUTED,
    }

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._lines:        list[dict]           = []
        self._filter_btns:  dict[str, FilterBtn] = {}
        self._search:       str                  = ""
        self._search_hits:  list[str]            = []
        self._search_idx:   int                  = -1
        self._autoscroll    = tk.BooleanVar(value=True)
        self._ctx_idx       = "1.0"
        self._build()

    # ── Construção ────────────────────────────────────────────────────────────
    def _build(self):
        # Cabeçalho
        hdr = tk.Frame(self, bg=BG_CARD)
        hdr.pack(fill="x")

        row1 = tk.Frame(hdr, bg=BG_CARD)
        row1.pack(fill="x", padx=10, pady=(4,4))
        lbl(row1, "Console", font=F_BOLD, fg=FG, bg=BG_CARD).pack(side="left")
        tk.Checkbutton(row1, text="Auto-scroll", variable=self._autoscroll,
                       bg=BG_CARD, fg=FG_MUTED, selectcolor=BG_CARD,
                       activebackground=BG_CARD, activeforeground=GREEN,
                       font=F_XSM, bd=0, cursor="hand2").pack(side="right")

        sep(row1, orient="v").pack(side="right", fill="y", padx=(8,12), pady=2)
        Btn(row1, "▼", color=BG_CARD, fg=FG_MUTED, padx=5, pady=1, font=F_XSM,
            command=lambda: self._search_nav(1)).pack(side="right", padx=(0,2))
        Btn(row1, "▲", color=BG_CARD, fg=FG_MUTED, padx=5, pady=1, font=F_XSM,
            command=lambda: self._search_nav(-1)).pack(side="right", padx=(0,2))
        self._sv = tk.StringVar()
        self._sv.trace_add("write", lambda *_: self._on_search())
        styled_entry(row1, textvariable=self._sv, width=20).pack(side="right", padx=(4,4), ipady=3)
        sep(row1, orient="v").pack(side="right", fill="y", padx=(8,6), pady=2)

        lbl(row1, "Filtrar:", font=F_XSM, fg=FG_MUTED, bg=BG_CARD).pack(side="left", padx=(12,6))
        for name, color in self._FILTER_COLORS.items():
            fb = FilterBtn(row1, name, color,
                           on_toggle=lambda active, n=name: self._on_filter(n, active))
            fb.pack(side="left", padx=2)
            self._filter_btns[name] = fb

        sep(self).pack(fill="x")

        # Área de texto
        tw = tk.Frame(self, bg=BG_INPUT)
        tw.pack(fill="both", expand=True)
        self._text = tk.Text(tw, state="disabled", bg=BG_INPUT, fg=FG,
                             font=F_MONO, relief="flat", bd=0, wrap="word",
                             insertbackground=GREEN, highlightthickness=0,
                             padx=12, pady=8, spacing1=1, spacing3=1,
                             selectbackground="#1e3a5f", selectforeground=FG,
                             inactiveselectbackground="#162d4a")
        self._text.pack(side="left", fill="both", expand=True)
        sb = FlatScrollbar(tw, command=self._text.yview)
        sb.pack(side="right", fill="y", padx=(2,4), pady=4)
        self._text.config(yscrollcommand=sb.set)

        for tag, color in self._TAG_COLORS.items():
            self._text.tag_config(tag, foreground=color)
        self._text.tag_config("cmd",        font=F_MONO_B)
        self._text.tag_config("ts",         foreground="#2e3450", font=F_MONO)
        self._text.tag_config("src",        foreground="#3d4470", font=F_MONO)
        self._text.tag_config("search_hit", background="#854d0e", foreground="#fef9c3")
        self._text.tag_config("search_current", background="#f59e0b", foreground="#0d0f18")

        # Menu de contexto (popup customizado)
        def _ctx(e):
            self._ctx_idx = self._text.index(f"@{e.x},{e.y}")
            # Captura selecao AGORA — o popup vai roubar o foco e a sel sera perdida
            try:
                self._ctx_sel = self._text.get("sel.first", "sel.last")
            except tk.TclError:
                self._ctx_sel = ""
            has_sel = bool(self._ctx_sel)
            items = [
                ("Copiar seleção",  self._copy_sel,  "normal" if has_sel else "disabled"),
                ("Copiar linha",    self._copy_line, "normal"),
                ("Copiar tudo",     self._copy_all,  "normal"),
                None,
                ("Limpar console",  self.clear,      "normal"),
            ]
            _show_ctx_popup(self._text, items, e.x_root, e.y_root)

        self._text.bind("<Button-3>", _ctx)
        self._text.bind("<Button-2>", _ctx)
        # Ctrl+C funciona mesmo com o widget em modo disabled
        self._text.bind("<Control-c>", lambda e: self._copy_sel() or "break")
        self._text.bind("<Control-C>", lambda e: self._copy_sel() or "break")

    # ── API pública (camada de abstração) ─────────────────────────────────────
    def write_info(self,    text: str, source: str = "Server"): self._record(text, "info",    source)
    def write_warn(self,    text: str, source: str = "Server"): self._record(text, "warn",    source)
    def write_error(self,   text: str, source: str = "Server"): self._record(text, "error",   source)
    def write_chat(self,    text: str, source: str = "Server"): self._record(text, "chat",    source)
    def write_command(self, text: str, source: str = ""):       self._record(text, "cmd",     source)
    def write_cmd(self, text: str, source: str = ""):
        self._record(text, "cmd", source)

    def write_system(self,  text: str, level: str = "muted"):   self._record(text, level,     "MineRun")
    def write_success(self, text: str, source: str = "MineRun"): self._record(text, "success", source)
    def write_dim(self,     text: str, source: str = "MineRun"): self._record(text, "dim",     source)

    def clear(self):
        self._lines.clear()
        self._text.config(state="normal")
        self._text.delete("1.0", "end")
        self._text.config(state="disabled")

    # ── Internals ─────────────────────────────────────────────────────────────
    def _record(self, text: str, level: str, source: str):
        ts    = time.strftime("%H:%M:%S")
        entry = {"ts": ts, "text": text, "level": level, "source": source}
        self._lines.append(entry)
        if self._visible(entry):
            self._append(entry)
            if self._search:
                self._hl_in_last(text)

    def _visible(self, entry: dict) -> bool:
        # Oculta apenas quando o botão do respectivo tipo está desativado (dim)
        for n, lvls in self._FILTER_MAP.items():
            if n in self._filter_btns and not self._filter_btns[n].active:
                if entry["level"] in lvls:
                    return False
        if self._search and self._search.lower() not in entry["text"].lower():
            return False
        return True

    def _append(self, entry: dict):
        t = self._text
        t.config(state="normal")
        if entry["source"]:
            t.insert("end", f"[{entry['source']}] ", "src")
        t.insert("end", entry["text"] + "\n", entry["level"])
        t.config(state="disabled")
        if self._autoscroll.get():
            t.see("end")

    def _rerender(self):
        t = self._text
        t.config(state="normal")
        t.delete("1.0", "end")
        for e in self._lines:
            if self._visible(e):
                if e["source"]:
                    t.insert("end", f"[{e['source']}] ", "src")
                t.insert("end", e["text"] + "\n", e["level"])
        t.config(state="disabled")
        if self._search:
            self._hl_all()
        if self._autoscroll.get():
            t.see("end")

    def _on_filter(self, name: str, _active: bool):
        self._rerender()

    def _on_search(self):
        self._search = self._sv.get().strip()
        self._rerender()

    def _hl_all(self):
        t = self._text
        t.tag_remove("search_hit", "1.0", "end")
        t.tag_remove("search_current", "1.0", "end")
        self._search_hits = []
        self._search_idx  = -1
        if not self._search:
            return
        start = "1.0"
        while True:
            pos = t.search(self._search, start, stopindex="end", nocase=True)
            if not pos: break
            end = f"{pos}+{len(self._search)}c"
            t.tag_add("search_hit", pos, end)
            self._search_hits.append(pos)
            start = end

    def _search_nav(self, delta: int):
        """Navega entre os matches destacados (+1 próximo, -1 anterior)."""
        if not self._search_hits:
            return
        n = len(self._search_hits)
        t = self._text
        # Remove destaque atual
        if 0 <= self._search_idx < n:
            cur = self._search_hits[self._search_idx]
            cur_end = f"{cur}+{len(self._search)}c"
            t.tag_remove("search_current", cur, cur_end)
            t.tag_add("search_hit", cur, cur_end)
        # Avança / retrocede (circular)
        self._search_idx = (self._search_idx + delta) % n
        new_pos = self._search_hits[self._search_idx]
        new_end = f"{new_pos}+{len(self._search)}c"
        t.tag_remove("search_hit", new_pos, new_end)
        t.tag_add("search_current", new_pos, new_end)
        t.see(new_pos)

    def _hl_in_last(self, text: str):
        if self._search.lower() not in text.lower(): return
        t  = self._text
        ln = int(t.index("end-1c").split(".")[0])
        st = f"{ln}.0"
        while True:
            pos = t.search(self._search, st, stopindex=f"{ln}.end", nocase=True)
            if not pos: break
            end = f"{pos}+{len(self._search)}c"; t.tag_add("search_hit", pos, end); st = end

    def _copy_sel(self):
        """
        Copia a selecao ativa para o clipboard.
        Precedencia:
          1. Selecao viva da tag 'sel' (Ctrl+C ou selecao atual)
          2. Texto capturado em _ctx_sel no momento do botao direito
             (necessario porque o popup rouba o foco e limpa a selecao
              em widgets Text desabilitados)
        """
        # 1) Tenta selecao viva primeiro (funciona para Ctrl+C)
        text = ""
        try:
            text = self._text.get("sel.first", "sel.last")
        except tk.TclError:
            pass
        # 2) Fallback: usa o texto capturado no right-click
        if not text:
            text = getattr(self, "_ctx_sel", "")
            self._ctx_sel = ""  # consome o cache para evitar reutilizacao
        if text:
            self._text.clipboard_clear()
            self._text.clipboard_append(text)

    def _copy_line(self):
        line = self._text.get(f"{self._ctx_idx} linestart", f"{self._ctx_idx} lineend")
        self._text.clipboard_clear(); self._text.clipboard_append(line.strip())

    def _copy_all(self):
        self._text.clipboard_clear(); self._text.clipboard_append(self._text.get("1.0", "end"))


# ══════════════════════════════════════════════════════════════════════════════
#  PLAYER WIDGET  — um componente por jogador
# ══════════════════════════════════════════════════════════════════════════════
class PlayerWidget(tk.Frame):
    """Linha de jogador: avatar (16px) + nick + menu de contexto."""

    _BG_N = BG_SIDEBAR
    _BG_H = "#191e30"

    def __init__(self, parent, name: str, on_action,
                 whitelisted: bool = False, banned: bool = False, is_op: bool = False, **kw):
        super().__init__(parent, bg=self._BG_N, cursor="hand2", **kw)
        self.name        = name
        self.whitelisted = whitelisted
        self.banned      = banned
        self.is_op       = is_op
        self.on_action   = on_action    # (action: str, name: str) → None
        self._img        = None         # mantém referência ao PhotoImage

        # Avatar
        self.av = tk.Label(self, bg=self._BG_N, text="👤",
                           font=("Segoe UI", 11), width=2, anchor="center")
        self.av.pack(side="left", padx=(8,6), pady=5)

        # Nick
        self.nk = tk.Label(self, text=name, bg=self._BG_N,
                            fg=FG, font=F_UI, anchor="w")
        self.nk.pack(side="left", fill="x", expand=True, pady=5, padx=(0,8))

        for w in (self, self.av, self.nk):
            w.bind("<Enter>",   lambda _: self._hover(True))
            w.bind("<Leave>",   lambda _: self._hover(False))
            w.bind("<Button-3>",self._menu)
            w.bind("<Button-2>",self._menu)  # macOS
            w.bind("<Double-Button-1>", self._on_double_click)

        threading.Thread(target=self._load_avatar, daemon=True).start()

    def _get_app(self):
        """Sobe a arvore de widgets ate encontrar a instancia de MineRunApp."""
        w = self
        while w:
            if hasattr(w, 'player_lists'):
                return w
            w = getattr(w, 'master', None)
        return None

    def _hover(self, on: bool):
        bg = self._BG_H if on else self._BG_N
        for w in (self, self.av, self.nk):
            try: w.config(bg=bg)
            except tk.TclError: pass

    def _load_avatar(self):
        """Carrega avatar via AvatarCache (thread-safe)."""
        app = self._get_app()
        if not app or not hasattr(app, 'avatar_cache'):
            return
        path = app.avatar_cache.get_path(self.name)
        if path:
            self.after(0, self._set_avatar_from_file, path)

    def _set_avatar_from_file(self, path: Path):
        try:
            img = tk.PhotoImage(file=str(path))
            self._img = img
            self.av.config(image=img, text="", width=20, height=20)
        except Exception:
            pass

    def _menu(self, event):
        """Menu de contexto do jogador usando o popup estilizado do app."""
        # Verifica status atual dinamicamente via player_lists (sempre atualizado)
        # Recarrega do disco antes de consultar para evitar dessincronização com
        # comandos executados fora do MineRun ou via RCON.
        app = self._get_app()
        if app and hasattr(app, 'player_lists'):
            app.player_lists.reload()
            is_op       = app.player_lists.is_op(self.name)
            whitelisted = app.player_lists.is_whitelisted(self.name)
            banned      = app.player_lists.is_banned(self.name)
            # Sincroniza cache do widget com o estado atual
            self.is_op       = is_op
            self.whitelisted = whitelisted
            self.banned      = banned
        else:
            is_op       = self.is_op
            whitelisted = self.whitelisted
            banned      = self.banned

        wl_check = "✓ " if whitelisted else ""
        bl_check = "✓ " if banned      else ""
        op_label = "▼  Rebaixar (deop)" if is_op else "▲  Promover (op)"

        def act(a): return lambda: self.on_action(a, self.name)

        items = [
            # ── Administração ──────────────────────────────────────────────
            ("── Administração ──", None, "disabled"),
            (op_label, act("promote" if not is_op else "demote"), "normal"),
            None,
            # ── Acesso ─────────────────────────────────────────────────────
            ("── Acesso ──", None, "disabled"),
            (f"{wl_check}Whitelist",  act("whitelist_toggle"), "normal"),
            (f"{bl_check}Banlist",    act("banlist_toggle"),   "normal"),
            None,
            # ── Moderação ──────────────────────────────────────────────────
            ("── Moderação ──", None, "disabled"),
            ("Kick…",   act("kick"),  "normal"),
            ("Ban…",    act("ban"),   "normal"),
            ("Mute…",   act("mute"),  "normal"),
            None,
            # ── Utilidades ─────────────────────────────────────────────────
            ("── Utilidades ──", None, "disabled"),
            ("Copiar Nick",    act("copy_nick"),      "normal"),
            ("Abrir Pasta",    act("open_folder"),    "normal"),
            ("Ver UUID",       act("ver_uuid"),       "normal"),
            ("Ver Inventário", act("ver_inventario"), "normal"),
            ("Teleportar…",    act("teleport"),       "normal"),
            None,
            # ── Debug ──────────────────────────────────────────────────────
            ("── Debug ──", None, "disabled"),
            ("Executar comando…", act("run_command"), "normal"),
        ]
        _show_ctx_popup(self, items, event.x_root, event.y_root)

    def _on_double_click(self, event):
        """Abre janela de detalhes do jogador (PlayerDetailsWindow)."""
        app = self._get_app()
        if app and hasattr(app, 'open_player_details'):
            app.open_player_details(self.name)


# ══════════════════════════════════════════════════════════════════════════════
#  PLAYER DETAILS WINDOW  — Janela modal com detalhes do jogador (v6.0)
# ══════════════════════════════════════════════════════════════════════════════
class PlayerDetailsWindow(tk.Toplevel):
    """Janela modal com detalhes do jogador (skin, cabeça, UUID, status, etc.)."""

    FIELDS = [
        ("Skin", "skin"),
        ("Cabeça", "head"),
        ("Nick", "nick"),
        ("UUID", "uuid"),
        ("Último Login", "last_login"),
        ("Ping", "ping"),
        ("Gamemode", "gamemode"),
        ("Dimensão", "dimension"),
        ("Posição", "position"),
        ("XP", "xp"),
        ("Vida", "health"),
        ("Fome", "food"),
        ("Whitelist", "whitelist"),
        ("Banido", "banned"),
        ("OP", "op"),
        ("Inventário", "inventory"),
        ("Permissões", "permissions"),
    ]

    def __init__(self, parent, name: str, app: "MineRunApp"):
        super().__init__(parent)
        self.name = name
        self.app = app
        self.title(f"Detalhes do Jogador: {name}")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)

        # Centralizar na janela pai
        self.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        w = 380
        h = 480
        self.geometry(f"{w}x{h}+{px + (pw - w)//2}+{py + (ph - h)//2}")

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # Área principal com scroll
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=16, pady=16)

        # Canvas + Scrollbar para muitos campos
        canvas = tk.Canvas(main, bg=BG, bd=0, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        sb = FlatScrollbar(main, command=canvas.yview)
        sb.pack(side="right", fill="y", padx=(4,0), pady=4)
        canvas.config(yscrollcommand=sb.set)

        inner = tk.Frame(canvas, bg=BG)
        win = canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind("<Configure>", lambda e: canvas.config(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-1 if e.delta > 0 else 1, "units"))

        # Header com avatar grande
        header = tk.Frame(inner, bg=BG_CARD, pady=12)
        header.pack(fill="x", pady=(0, 12))

        self.avatar_lbl = tk.Label(header, bg=BG_CARD, text="👤", font=("Segoe UI", 48), fg=FG)
        self.avatar_lbl.pack()

        # Grid de campos
        for i, (label, key) in enumerate(self.FIELDS):
            row = tk.Frame(inner, bg=BG)
            row.pack(fill="x", pady=3)

            tk.Label(row, text=f"{label}:", font=F_BOLD, fg=FG_MUTED, bg=BG,
                     width=14, anchor="e").pack(side="left", padx=(0, 8))

            value_lbl = tk.Label(row, text="Não disponível", font=F_UI, fg=FG, bg=BG,
                                 anchor="w", justify="left")
            value_lbl.pack(side="left", fill="x", expand=True)

            setattr(self, f"_lbl_{key}", value_lbl)

    def _load_data(self):
        """Carrega dados do jogador e preenche os campos."""
        # Avatar (cabeça grande)
        if hasattr(self.app, 'avatar_cache'):
            path = self.app.avatar_cache.get_path(self.name)
            if path:
                try:
                    img = tk.PhotoImage(file=str(path))
                    self._avatar_img = img  # manter referência
                    self.avatar_lbl.config(image=img, text="")
                except Exception:
                    pass

        # PlayerLists para whitelist/ban/op
        pl = self.app.player_lists
        self._set("nick", self.name)
        self._set("uuid", pl.get_uuid(self.name) or "Não disponível")
        self._set("whitelist", "Sim ✓" if pl.is_whitelisted(self.name) else "Não")
        self._set("banned", "Sim ✓" if pl.is_banned(self.name) else "Não")
        self._set("op", "Sim ✓" if pl.is_op(self.name) else "Não")

        # Demais campos não disponíveis ainda
        for key in ["skin", "head", "last_login", "ping", "gamemode",
                    "dimension", "position", "xp", "health", "food",
                    "inventory", "permissions"]:
            self._set(key, "Não disponível")

    def _set(self, key: str, value: str):
        lbl = getattr(self, f"_lbl_{key}", None)
        if lbl:
            lbl.config(text=value)


# ══════════════════════════════════════════════════════════════════════════════
#  PLAYER PANEL  — Canvas scrollável com PlayerWidgets
# ══════════════════════════════════════════════════════════════════════════════
class PlayerPanel(tk.Frame):
    """
    Painel de jogadores.
    Cada jogador é um PlayerWidget independente — estrutura de explorador.
    """

    def __init__(self, parent, on_action, **kw):
        super().__init__(parent, bg=BG_SIDEBAR, width=SIDEBAR_W, **kw)
        self.pack_propagate(False)
        self.on_action = on_action
        self.widgets: dict[str, PlayerWidget] = {}

        # Cabeçalho
        hdr = tk.Frame(self, bg=BG_CARD, height=36)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        lbl(hdr, "  Jogadores", font=F_BOLD, fg=FG,
            bg=BG_CARD).pack(side="left", fill="y", padx=4)
        self.badge = tk.Label(hdr, text="0 / 20", font=F_XSM,
                              fg=BG, bg=FG_MUTED, padx=6, pady=2)
        self.badge.pack(side="right", padx=8, pady=7)
        sep(self).pack(fill="x")

        # Canvas scrollável
        wrap = tk.Frame(self, bg=BG_SIDEBAR)
        wrap.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(wrap, bg=BG_SIDEBAR, bd=0, highlightthickness=0)
        self._canvas.pack(side="left", fill="both", expand=True)

        sb = FlatScrollbar(wrap, command=self._canvas.yview)
        sb.pack(side="right", fill="y", padx=(0,4), pady=4)
        self._canvas.config(yscrollcommand=sb.set)

        self._inner = tk.Frame(self._canvas, bg=BG_SIDEBAR)
        self._win   = self._canvas.create_window((0,0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>",  self._update_scroll)
        self._canvas.bind("<Configure>", self._update_width)
        self._canvas.bind("<MouseWheel>",self._on_wheel)

    def _update_scroll(self, _=None):
        self._canvas.config(scrollregion=self._canvas.bbox("all"))

    def _update_width(self, e):
        self._canvas.itemconfig(self._win, width=e.width)

    def _on_wheel(self, e):
        self._canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")

    def add(self, name: str):
        if name in self.widgets: return
        # Passa estado de whitelist/ban/op do PlayerLists
        app = self._get_app()
        whitelisted = app.player_lists.is_whitelisted(name) if app else False
        banned = app.player_lists.is_banned(name) if app else False
        is_op = app.player_lists.is_op(name) if app else False
        w = PlayerWidget(self._inner, name, self.on_action,
                         whitelisted=whitelisted, banned=banned, is_op=is_op)
        w.pack(fill="x", padx=4, pady=(2,0))
        self.widgets[name] = w
        self._update_badge()

    def _get_app(self):
        """Busca a instância de MineRunApp pelo widget root."""
        w = self
        while w:
            if hasattr(w, 'player_lists'):
                return w
            w = w.master
        return None

    def remove(self, name: str):
        if name in self.widgets:
            self.widgets[name].destroy()
            del self.widgets[name]
            self._update_badge()

    def clear(self):
        for w in list(self.widgets.values()):
            w.destroy()
        self.widgets.clear()
        self._update_badge()

    def count(self) -> int:
        return len(self.widgets)

    def names(self) -> list:
        return list(self.widgets.keys())

    def _update_badge(self):
        max_players = getattr(self, 'max_players', 20)
        self.badge.config(text=f"{self.count()} / {max_players}")


# ══════════════════════════════════════════════════════════════════════════════
#  APP  — orquestra tudo
# ══════════════════════════════════════════════════════════════════════════════
class MineRunApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MineRun  —  Gerenciador de Servidor")
        self.root.geometry(f"{WIN_W}x{WIN_H}")
        self.root.minsize(MIN_W, MIN_H)
        self.root.configure(bg=BG)

        # Configurações
        self.settings = Settings.load()

        # Sistema de eventos (v6.0)
        self.parser = ServerLogParser()
        self.dispatcher = EventDispatcher()
        # Registra handlers
        self.dispatcher.on("console", self._on_console_event)
        self.dispatcher.on("join", self._on_join)
        self.dispatcher.on("leave", self._on_leave)
        self.dispatcher.on("startup_finished", self._on_startup_finished)

        # PlayerTracker (v6.1) — fonte-de-verdade dos jogadores online
        self.tracker = PlayerTracker()

        # PlayerLists unificado (v6.0)
        self.player_lists = PlayerLists(self.settings.server_dir or ".")

        # Avatar Cache (v6.0)
        self.avatar_cache = AvatarCache()

        # Controller (sem tkinter)
        self.ctrl = ServerController()
        self.ctrl.on_line         = lambda l: self.root.after(0, self._on_line, l)
        self.ctrl.on_state_change = lambda s: self.root.after(0, self._on_ctrl_event, s)

        # Histórico de comandos
        self.cmd_history: list[str] = []
        self.history_idx: int       = 0

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._tick()

        self.log_success("Bem-vindo ao MineRun 6.0")
        if not self.settings.jar_path:
            self.log_warn("Configure o servidor em ⚙ Configurações antes de iniciar.")
        self.log_dim("─" * 72)

    # ──────────────────────────────────────────────────────────────────────────
    #  WRAPPERS DE DESACOPLAMENTO (alto nível)
    # ──────────────────────────────────────────────────────────────────────────
    # Console / Logging
    def log(self, text: str, level: str = "info", source: str = "MineRun"):
        """Escreve no console via wrapper unificado."""
        getattr(self.console, f"write_{level}")(text, source)

    def log_info(self, text: str, source: str = "MineRun"):
        self.console.write_info(text, source)

    def log_warn(self, text: str, source: str = "MineRun"):
        self.console.write_warn(text, source)

    def log_error(self, text: str, source: str = "MineRun"):
        self.console.write_error(text, source)

    def log_success(self, text: str, source: str = "MineRun"):
        self.console.write_success(text, source)

    def log_system(self, text: str, level: str = "muted"):
        self.console.write_system(text, level)

    def log_chat(self, text: str, source: str = "Server"):
        self.console.write_chat(text, source)

    def log_command(self, text: str, source: str = ""):
        self.console.write_command(text, source)

    def log_dim(self, text: str, source: str = "MineRun"):
        self.console.write_dim(text, source)

    def clear_console(self):
        self.console.clear()

    # Jogadores
    def player_add(self, name: str):
        self.player_panel.add(name)

    def player_remove(self, name: str):
        self.player_panel.remove(name)

    def player_clear(self):
        self.player_panel.clear()

    def player_count(self) -> int:
        return self.player_panel.count()

    def player_names(self) -> list[str]:
        return list(self.player_panel.widgets.keys())

    def player_get(self, name: str):
        return self.player_panel.widgets.get(name)

    def player_update_badge(self):
        self.player_panel.max_players = getattr(self, 'max_players', 20)
        self.player_panel._update_badge()

    def open_player_details(self, name: str):
        """Abre janela de detalhes do jogador (duplo clique)."""
        PlayerDetailsWindow(self.root, name, self)

    # Servidor
    def send_server_command(self, cmd: str):
        self.ctrl.send(cmd)

    def stop_server(self):
        if self.ctrl.proc:
            self._set_state(STOPPING)
            self.log_system("Enviando comando stop…", "warn")
            self.ctrl.stop()
            self.root.after(30_000, self._force_kill)

    def restart_server(self):
        self.log_system("Reiniciando servidor…", "warn")
        self._restart_pending = True
        self.stop_server()

    def start_server(self):
        s = self.settings
        if not s.jar_path or not Path(s.jar_path).is_file():
            messagebox.showerror("MineRun",
                "Arquivo JAR não encontrado.\nConfigure em ⚙ Configurações.")
            return
        self._set_state(STARTING)
        self.log_system("Iniciando servidor…", "info")
        self.log_system(f"Diretório: {s.server_dir or Path(s.jar_path).parent}", "muted")
        self.log_system(f"Comando:   {' '.join(s.build_cmd())}", "muted")
        self.log_dim("─" * 72)
        err = self.ctrl.start(s)
        if err:
            self.log_error(err)
            self._set_state(OFFLINE)

    def force_kill_server(self):
        if self.ctrl.running:
            self.log_error("Forçando encerramento (timeout 30s).")
            self.ctrl.force_kill()

    # ──────────────────────────────────────────────────────────────────────────
    #  BUILD UI
    # ──────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        sep(self.root).pack(fill="x")

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)

        # Player panel (lado esquerdo)
        self.player_panel = PlayerPanel(body, on_action=self._player_action)
        self.player_panel.pack(side="left", fill="y")
        sep(body, orient="v").pack(side="left", fill="y")

        # Console (centro/direita)
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self.console = ConsoleWidget(right)
        self.console.pack(fill="both", expand=True)

        sep(right).pack(fill="x")
        self._build_cmd_bar(right)

        sep(self.root).pack(fill="x")
        self._build_statusbar()

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=BG_HEADER, height=52)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        inner = tk.Frame(hdr, bg=BG_HEADER)
        inner.pack(fill="both", expand=True, padx=18)

        # ── Lado esquerdo: Logo + Botões do Servidor ───────────────────────
        left = tk.Frame(inner, bg=BG_HEADER)
        left.pack(side="left", fill="y")

        logo = tk.Frame(left, bg=BG_HEADER)
        logo.pack(side="left", fill="y")
        lbl(logo, "⬡", font=("Segoe UI", 20), fg=GREEN,
            bg=BG_HEADER).pack(side="left", padx=(0,8))
        lbl(logo, "MineRun", font=("Segoe UI", 14, "bold"),
            fg=FG, bg=BG_HEADER).pack(side="left")
        lbl(logo, "  v6.0", font=F_XSM, fg=FG_MUTED,
            bg=BG_HEADER).pack(side="left", pady=(4,0))

        # Botões: Iniciar / Reiniciar / Parar
        # padx esquerdo calculado para alinhar "Iniciar" com a divisória Jogadores/Console
        grp_server = tk.Frame(left, bg=BG_HEADER)
        grp_server.pack(side="left", padx=(SIDEBAR_W - 130, 8))

        self.btn_start   = Btn(grp_server, "▶  Iniciar",   color=GREEN, fg="#000", command=self._on_start)
        self.btn_restart = Btn(grp_server, "↻  Reiniciar", color=AMBER, fg="#000", command=self._on_restart)
        self.btn_stop    = Btn(grp_server, "■  Parar",     color=RED,               command=self._on_stop)

        for b in (self.btn_start, self.btn_restart, self.btn_stop):
            b.pack(side="left", padx=3, pady=8)

        # ── Centro: Espaço livre para conteúdo futuro ──────────────────────
        self.header_center = tk.Frame(inner, bg=BG_HEADER)
        self.header_center.pack(side="left", fill="both", expand=True)

        # ── Lado direito: Utilidades + Status ──────────────────────────────
        right = tk.Frame(inner, bg=BG_HEADER)
        right.pack(side="right", fill="y")

        # Botões: Pasta / Configurações / Limpar
        grp_utils = tk.Frame(right, bg=BG_HEADER)
        grp_utils.pack(side="left", padx=(24, 0))

        Btn(grp_utils, "📁  Pasta",        color=BG_CARD, command=self._open_folder).pack(side="left", padx=3, pady=8)
        Btn(grp_utils, "⚙  Configurações", color=BG_CARD, command=self.open_settings).pack(side="left", padx=3, pady=8)
        Btn(grp_utils, "🗑  Limpar",        color=BG_CARD, command=self.clear_console).pack(side="left", padx=3, pady=8)

        # Separador vertical antes do status
        sep(grp_utils, orient="v").pack(side="left", fill="y", padx=12, pady=10)

        # Badge de status (online/offline)
        badge = tk.Frame(right, bg=BG_HEADER)
        badge.pack(side="left", fill="y")
        self.dot       = lbl(badge, "●", font=("Segoe UI", 13), fg=RED, bg=BG_HEADER)
        self.dot.pack(side="left", padx=(0,5))
        self.state_lbl = lbl(badge, "Offline", font=F_BOLD, fg=RED, bg=BG_HEADER)
        self.state_lbl.pack(side="left")

        self._set_state(OFFLINE)

    # ── Barra de comando ──────────────────────────────────────────────────────
    def _build_cmd_bar(self, parent):
        bar = tk.Frame(parent, bg=BG_HEADER, pady=8)
        bar.pack(fill="x")
        lbl(bar, "❯", font=("Consolas", 12, "bold"),
            fg=GREEN, bg=BG_HEADER).pack(side="left", padx=(14, 8))
        self.cmd_entry = styled_entry(bar, width=60)
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=(0,8), ipady=6)
        self.cmd_entry.bind("<Return>", lambda _: self._send_cmd())
        self.cmd_entry.bind("<Up>",     self._history_up)
        self.cmd_entry.bind("<Down>",   self._history_down)
        Btn(bar, "Enviar", color=GREEN, fg="#000", pady=6,
            command=self._send_cmd).pack(side="right", padx=(0,10))

    # ── Status bar — RAM, CPU, Players, Uptime ────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=BG_HEADER, height=36)
        bar.pack(fill="x"); bar.pack_propagate(False)
        inner = tk.Frame(bar, bg=BG_HEADER)
        inner.pack(fill="both", expand=True, padx=16)

        self.metrics: dict[str, tk.Label] = {}
        for key, icon in [("RAM","💾"),("CPU","⚡"),("Uptime","🕐")]:
            f = tk.Frame(inner, bg=BG_HEADER)
            f.pack(side="left", padx=10, fill="y")
            lbl(f, f"{icon} {key}", font=F_XSM, fg=FG_MUTED,
                bg=BG_HEADER).pack(side="left", padx=(0,4))
            v = lbl(f, "—", font=("Segoe UI", 9, "bold"), fg=FG_MUTED, bg=BG_HEADER)
            v.pack(side="left")
            self.metrics[key] = v
            sep(inner, orient="v").pack(side="left", fill="y", padx=(10,0), pady=8)

        lbl(inner, "MineRun v5.0  ·  Keven Castilho © 2026",
            font=F_XSM, fg=FG_DIM, bg=BG_HEADER).pack(side="right")

    # ──────────────────────────────────────────────────────────────────────────
    #  ESTADO
    # ──────────────────────────────────────────────────────────────────────────
    def _set_state(self, state: str):
        self.ctrl.state = state
        color, label   = STATE_META[state]
        self.dot.config(fg=color)
        self.state_lbl.config(fg=color, text=label)

        off = state == OFFLINE
        on  = state == ONLINE

        if off: self.btn_start.enable()
        else:   self.btn_start.disable()

        if on:
            self.btn_restart.enable(); self.btn_stop.enable()
        elif state == STARTING:
            self.btn_restart.disable(); self.btn_stop.enable()
        else:
            self.btn_restart.disable(); self.btn_stop.disable()

        # Reseta cache do processo e flag de prime quando servidor para/inicia
        if state == STARTING:
            self._cpu_primed = False
            self._ps_proc    = None

    # ──────────────────────────────────────────────────────────────────────────
    #  AÇÕES DO SERVIDOR
    # ──────────────────────────────────────────────────────────────────────────
    def _on_start(self):
        s = self.settings
        if not s.jar_path or not Path(s.jar_path).is_file():
            messagebox.showerror("MineRun",
                "Arquivo JAR não encontrado.\nConfigure em ⚙ Configurações.")
            return
        self._set_state(STARTING)
        self.log_system("Iniciando servidor…", "info")
        self.log_system(f"Diretório: {s.server_dir or Path(s.jar_path).parent}", "muted")
        self.log_system(f"Comando:   {' '.join(s.build_cmd())}", "muted")
        self.log_dim("─" * 72)

        err = self.ctrl.start(s)
        if err:
            self.log_error(err, "MineRun")
            self._set_state(OFFLINE)

    def _on_restart(self):
        self.log_system("Reiniciando servidor…", "warn")
        self._restart_pending = True
        self._on_stop()

    _restart_pending = False

    def _on_stop(self):
        if not self.ctrl.proc: return
        self._set_state(STOPPING)
        self.log_system("Enviando comando stop…", "warn")
        self.stop_server()

    def _force_kill(self):
        if self.ctrl.running:
            self.log_error("Forçando encerramento (timeout 30s).", "MineRun")
            self.force_kill_server()

    # ── Eventos vindos do controller (sempre na thread principal) ─────────────
    def _on_ctrl_event(self, event: str):
        if event == "_ended":
            if self._restart_pending:
                self._restart_pending = False
                self.log_system("Servidor parado. Reiniciando em 1s…", "muted")
                self._set_state(OFFLINE)
                self.root.after(1000, self._on_start)
            else:
                self.log_warn("Servidor encerrado.")
                self.log_dim("─" * 72)
                self._set_state(OFFLINE)
            self.tracker.clear()
            self.player_clear()
            self.ctrl.proc = None
            self.ctrl.uptime_start = None

    def _on_line(self, line: str):
        """Parseia linha via ServerLogParser e despacha eventos."""
        events = self.parser.parse(line)
        for ev in events:
            self.dispatcher.dispatch(ev)

    # ──────────────────────────────────────────────────────────────────────────
    #  HANDLERS DE EVENTOS
    # ──────────────────────────────────────────────────────────────────────────
    def _on_console_event(self, ev: ServerEvent):
        if ev.raw:
            lvl = ev.level or "info"
            src = ev.source or "Server"
            getattr(self.console, f"write_{lvl}")(ev.raw, src)

    def _on_join(self, ev: ServerEvent):
        if ev.player:
            # Evita duplicata: se o tracker ja tem o jogador (ex: join duplo), ignora
            if ev.player in self.tracker:
                return
            self.tracker.join(ev.player)
            self.player_add(ev.player)
            self.player_update_badge()

    def _on_leave(self, ev: ServerEvent):
        if ev.player:
            self.tracker.leave(ev.player)
            self.player_remove(ev.player)
            self.player_update_badge()

    def _on_startup_finished(self, ev: ServerEvent):
        self._set_state(ONLINE)
        # Recarrega listas de jogadores (whitelist, banlist, ops)
        self.player_lists.reload()
        # Lê max-players do server.properties
        max_players = self._read_max_players()
        self.max_players = max_players
        self.player_update_badge()
        # Sincroniza lista inicial: tenta RCON > Query > estado limpo
        self.tracker.clear()
        self.player_clear()
        self.root.after(1500, self._sync_initial_players)

    # ── Sincronia Inicial de Jogadores (RCON > Query > estado limpo) ──────

    def _sync_initial_players(self) -> None:
        """
        Tenta sincronizar a lista de jogadores online logo apos o servidor iniciar.
        Ordem: RCON (mais confiavel) -> Query UDP -> estado limpo (join/leave).
        Roda em thread para nao travar a UI.
        """
        threading.Thread(target=self._sync_worker, daemon=True).start()

    def _sync_worker(self) -> None:
        """Worker que tenta RCON, depois Query, rodando em background."""
        props = self._read_server_properties()
        host  = "localhost"

        # ── Opcao 1: RCON ─────────────────────────────────────────────────
        if props.get("enable-rcon", "").lower() == "true":
            password = props.get("rcon.password", "")
            try:
                port = int(props.get("rcon.port", 25575))
            except (ValueError, TypeError):
                port = 25575
            if password:
                rcon = MinecraftRcon(host=host, port=port, password=password)
                if rcon.connect():
                    response = rcon.command("list")
                    rcon.disconnect()
                    if response is not None:
                        players = self._parse_rcon_list_response(response)
                        self.root.after(0, self._apply_initial_players, players, "RCON")
                        return

        # ── Opcao 2: Query Protocol ───────────────────────────────────────
        if props.get("enable-query", "").lower() == "true":
            try:
                port = int(props.get("query.port",
                                      props.get("server-port", 25565)))
            except (ValueError, TypeError):
                port = 25565
            query   = MinecraftQuery(host=host, port=port)
            players = query.get_players()
            if players is not None:
                self.root.after(0, self._apply_initial_players, players, "Query")
                return

        # ── Opcao 3: Nao ha sync — trackeamento por join/leave ────────────
        self.root.after(0, self._log_no_sync)

    def _apply_initial_players(self, players: list, source: str) -> None:
        """
        Aplica a lista inicial no tracker e no painel (thread principal).
        MERGE seguro: une snapshot RCON/Query com eventos join/leave que
        chegaram entre startup_finished e a resposta do sync.
        """
        merged = sorted(set(players) | set(self.tracker.players))
        self.tracker.set_all(merged)
        self.player_clear()
        for name in merged:
            self.player_add(name)
        self.player_update_badge()
        self.log_system(
            f"{source}: {len(merged)} jogador(es) online na sincronizacao inicial.",
            "muted"
        )

    def _log_no_sync(self) -> None:
        self.log_system(
            "Rastreamento por join/leave ativo. "
            "Habilite RCON ou Query no servidor para sincronizacao inicial.",
            "muted"
        )

    def _parse_rcon_list_response(self, response: str) -> list:
        """
        Extrai nomes da resposta do comando 'list' via RCON.
        A resposta tipica e: 'There are N of a max of M players online: Name1, Name2'
        O RCON retorna texto puro (sem codigo de idioma), entao o parse e seguro.
        Mas se o formato mudar, cai para extrair qualquer coisa apos ':' .
        """
        # Tenta extrair a parte apos o primeiro ':'
        colon = response.find(":")
        if colon == -1:
            return []
        names_part = response[colon + 1:].strip()
        if not names_part:
            return []
        # Valida: cada token deve ser um nick valido (3-16 chars alfanum/underscore)
        import re as _re
        nick_re = _re.compile(r'^[A-Za-z0-9_]{1,16}$')
        names = [
            n.strip() for n in names_part.split(",")
            if nick_re.match(n.strip())
        ]
        return names

    def _read_server_properties(self) -> dict:
        """
        Le server.properties e retorna um dicionario {chave: valor}.
        Ignora linhas de comentario (#) e linhas mal formatadas.
        """
        props: dict = {}
        try:
            server_dir = self.settings.server_dir or (
                str(Path(self.settings.jar_path).parent)
                if self.settings.jar_path else None
            )
            if not server_dir:
                return props
            sd = str(server_dir)
            if sd.startswith("http://") or sd.startswith("https://"):
                return props
            p = Path(server_dir) / "server.properties"
            if not p.exists():
                return props
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, _, v = line.partition("=")
                    props[k.strip()] = v.strip()
        except Exception:
            pass
        return props

    def _read_max_players(self) -> int:
        """Lê max-players do server.properties. Fallback: 20."""
        try:
            server_dir = self.settings.server_dir or (
                Path(self.settings.jar_path).parent if self.settings.jar_path else None
            )
            if server_dir:
                sd = str(server_dir)
                if sd.startswith("http://") or sd.startswith("https://"):
                    return 20
                props = Path(server_dir) / "server.properties"
                if props.exists():
                    for line in props.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if line.startswith("max-players="):
                            return int(line.split("=")[1].strip())
        except Exception:
            pass
        return 20

    # ──────────────────────────────────────────────────────────────────────────
    #  JOGADORES — ações do menu de contexto
    # ──────────────────────────────────────────────────────────────────────────
    def _get_player_uuid(self, name: str) -> "str | None":
        """Procura o UUID do jogador nos arquivos JSON do servidor."""
        base = self._get_server_base()
        if base is None:
            return None
        for fname in ["whitelist.json", "ops.json", "banned-players.json"]:
            fpath = base / fname
            if fpath.exists():
                try:
                    data = json.loads(fpath.read_text(encoding="utf-8"))
                    for entry in data:
                        if isinstance(entry, dict) and entry.get("name", "").lower() == name.lower():
                            uid = entry.get("uuid", "")
                            if uid:
                                return uid
                except Exception:
                    pass
        return None

    def _get_server_base(self) -> "Path | None":
        """Retorna o diretório base do servidor como Path, ou None se não configurado."""
        if self.settings.server_dir:
            return Path(self.settings.server_dir)
        if self.settings.jar_path:
            return Path(self.settings.jar_path).parent
        return None

    def _find_playerdata_dir(self) -> "Path | None":
        """Localiza a pasta playerdata consultando level-name em server.properties.

        Ordem de busca:
          1. level-name do server.properties (valor configurado pelo admin)
          2. Fallbacks comuns: world, world_nether, world_the_end
        Retorna None se nenhuma pasta existir.
        """
        base = self._get_server_base()
        if base is None:
            return None
        # Lê level-name do server.properties (fonte canônica)
        props = self._read_server_properties()
        level_name = props.get("level-name", "").strip()
        # Candidatos em ordem de prioridade
        candidates = []
        if level_name:
            candidates.append(level_name)
        candidates += ["world", "world_nether", "world_the_end"]
        for wname in candidates:
            pd = base / wname / "playerdata"
            if pd.exists():
                return pd
        return None

    # Ações que exigem servidor online para enviar comandos
    _CMD_ACTIONS = frozenset({
        "promote", "demote", "whitelist_toggle", "banlist_toggle",
        "kick", "ban", "mute", "teleport", "run_command",
    })

    def _player_action(self, action: str, name: str):
        pw = self.player_get(name)

        # Guard: ações de comando exigem servidor online
        if action in self._CMD_ACTIONS:
            if self.ctrl.state != ONLINE or not self.ctrl.proc:
                messagebox.showwarning("MineRun",
                    f"O servidor precisa estar online para executar esta ação.\n"
                    f"({action} → {name})")
                return

        if action == "promote":
            self.send_server_command(f"op {name}")
            self.log_system(f"op {name}", "info")
            if pw: pw.is_op = True
            self.root.after(500, self.player_lists.reload)

        elif action == "demote":
            self.send_server_command(f"deop {name}")
            self.log_system(f"deop {name}", "info")
            if pw: pw.is_op = False
            self.root.after(500, self.player_lists.reload)

        elif action == "whitelist_toggle":
            if pw and pw.whitelisted:
                self.send_server_command(f"whitelist remove {name}")
                self.log_system(f"whitelist remove {name}", "info")
                pw.whitelisted = False
            else:
                self.send_server_command(f"whitelist add {name}")
                self.log_system(f"whitelist add {name}", "info")
                if pw: pw.whitelisted = True
            self.root.after(500, self.player_lists.reload)

        elif action == "banlist_toggle":
            if pw and pw.banned:
                self.send_server_command(f"pardon {name}")
                self.log_system(f"pardon {name}", "info")
                pw.banned = False
            else:
                self.send_server_command(f"ban {name}")
                self.log_system(f"ban {name}", "info")
                if pw: pw.banned = True
            self.root.after(500, self.player_lists.reload)

        elif action == "kick":
            # Diálogo estilizado no tema do app
            reason = _show_styled_input(
                self.root, "Kick",
                f"Motivo para expulsar  {name}  (deixe em branco para sem motivo):")
            if reason is not None:
                cmd = f"kick {name} {reason}".strip()
                self.send_server_command(cmd)
                self.log_warn(f"❯ {cmd}")
                self.player_remove(name)

        elif action == "ban":
            reason = _show_styled_input(
                self.root, "Ban",
                f"Motivo para banir  {name}  permanentemente:")
            if reason is not None:
                cmd = f"ban {name} {reason}".strip()
                msg = f"Banir permanentemente  {name}?\n\nComando: {cmd}"
                if _show_styled_confirm(self.root, "Confirmar Ban", msg):
                    self.send_server_command(cmd)
                    self.log_error(f"❯ {cmd}", "MineRun")
                    self.player_remove(name)

        elif action == "mute":
            # Mute: vanilla não tem comando nativo; envia comando customizável
            cmd_text = _show_styled_input(
                self.root, "Mute",
                f"Comando de mute para  {name}  (ex: mute {name} 10m):",
                initial=f"mute {name}")
            if cmd_text and cmd_text.strip():
                self.send_server_command(cmd_text.strip())
                self.log_system(f"❯ {cmd_text.strip()}", "warn")

        elif action == "copy_nick":
            self.root.clipboard_clear()
            self.root.clipboard_append(name)
            self.log_system(f"Nick copiado: {name}", "muted")

        elif action == "open_folder":
            # Abre a pasta de dados do jogador (world/playerdata)
            base = self._get_server_base()
            if base is None:
                messagebox.showwarning("MineRun",
                    "Nenhuma pasta de servidor configurada.\nDefina-a em ⚙ Configurações.")
                return
            uuid = self._get_player_uuid(name)
            # Localiza playerdata consultando level-name do server.properties
            playerdata_dir = self._find_playerdata_dir()
            if playerdata_dir is None:
                messagebox.showwarning(
                    "MineRun",
                    f"Pasta de dados do jogador não encontrada.\n"
                    f"Esperado: {base / 'world' / 'playerdata'}\n\n"
                    f"Verifique se o servidor já foi iniciado ao menos uma vez.")
                return
            try:
                import platform
                system = platform.system()
                if system == "Windows" and uuid:
                    # Seleciona o arquivo .dat específico do jogador se tiver UUID
                    dat_file = playerdata_dir / f"{uuid}.dat"
                    if dat_file.exists():
                        subprocess.Popen(
                            ["explorer", "/select,", str(dat_file)])
                        self.log_system(f"Abrindo dados de {name}: {dat_file.name}", "muted")
                        return
                # Fallback: abre a pasta playerdata
                if system == "Windows":
                    os.startfile(str(playerdata_dir))
                elif system == "Darwin":
                    subprocess.Popen(["open", str(playerdata_dir)])
                else:
                    subprocess.Popen(["xdg-open", str(playerdata_dir)])
                self.log_system(f"Abrindo pasta: {playerdata_dir}", "muted")
            except Exception as e:
                messagebox.showwarning("MineRun", f"Não foi possível abrir a pasta:\n{e}")

        elif action == "ver_uuid":
            uuid = self._get_player_uuid(name)
            if uuid:
                _show_styled_info(self.root, f"UUID — {name}", [
                    ("Jogador", name),
                    ("UUID",    uuid),
                ])
                # Copia para clipboard automaticamente
                self.root.clipboard_clear()
                self.root.clipboard_append(uuid)
                self.log_system(f"UUID de {name}: {uuid} (copiado)", "muted")
            else:
                _show_styled_info(self.root, f"UUID — {name}", [
                    ("Jogador", name),
                    ("UUID",    "Não encontrado"),
                    ("Dica",    "Adicione à whitelist ou ops para registrar o UUID"),
                ])

        elif action == "ver_inventario":
            uuid = self._get_player_uuid(name)
            playerdata_dir = self._find_playerdata_dir()
            if playerdata_dir is None:
                base_check = self._get_server_base()
                if base_check is None:
                    messagebox.showwarning("MineRun",
                        "Nenhuma pasta de servidor configurada.\nDefina-a em ⚙ Configurações.")
                else:
                    props = self._read_server_properties()
                    level = props.get("level-name", "world")
                    messagebox.showwarning("MineRun",
                        f"Pasta de dados do jogador não encontrada.\n"
                        f"Esperado: {base_check / level / 'playerdata'}\n\n"
                        f"Verifique se o servidor já foi iniciado ao menos uma vez.")
                return
            dat_file = None
            if uuid:
                candidate_dat = playerdata_dir / f"{uuid}.dat"
                if candidate_dat.exists():
                    dat_file = candidate_dat
            _show_inventory_dialog(self.root, name, uuid, dat_file, playerdata_dir)

        elif action == "teleport":
            # Diálogo: nome de outro jogador ou coordenadas
            dest = _show_styled_input(
                self.root, "Teleportar",
                f"Destino para  {name}  (jogador ou x y z):",
                initial="")
            if dest and dest.strip():
                cmd = f"tp {name} {dest.strip()}"
                self.send_server_command(cmd)
                self.log_system(f"❯ {cmd}", "info")

        elif action == "run_command":
            cmd_text = _show_styled_input(
                self.root, "Executar Comando",
                f"Comando a executar  (use {name} para referenciar o jogador):",
                initial=f"tell {name} ")
            if cmd_text and cmd_text.strip():
                self.send_server_command(cmd_text.strip())
                self.log_system(f"❯ {cmd_text.strip()}", "info")

    # ──────────────────────────────────────────────────────────────────────────
    #  COMANDO
    # ──────────────────────────────────────────────────────────────────────────
    def _send_cmd(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd: return
        if self.ctrl.state != ONLINE or not self.ctrl.proc:
            self.log_warn("O servidor não está online."); return
        self.cmd_history.append(cmd)
        self.history_idx = len(self.cmd_history)
        self.log_command(f"❯ {cmd}")
        self.send_server_command(cmd)
        self.cmd_entry.delete(0, "end")

    def _history_up(self, _=None):
        if not self.cmd_history: return
        self.history_idx = max(0, self.history_idx - 1)
        self.cmd_entry.delete(0, "end")
        self.cmd_entry.insert(0, self.cmd_history[self.history_idx])

    def _history_down(self, _=None):
        if not self.cmd_history: return
        self.history_idx = min(len(self.cmd_history), self.history_idx + 1)
        self.cmd_entry.delete(0, "end")
        if self.history_idx < len(self.cmd_history):
            self.cmd_entry.insert(0, self.cmd_history[self.history_idx])

    # ──────────────────────────────────────────────────────────────────────────
    #  TICK — métricas a cada 1 s
    # ──────────────────────────────────────────────────────────────────────────
    def _tick(self):
        if self.ctrl.state == ONLINE and self.ctrl.proc:

            # Alterna estado de blink a cada tick (1 s) para uso em 100 %
            self._blink_on = not getattr(self, '_blink_on', False)

            if HAS_PSUTIL:
                try:
                    # Cria o objeto Process UMA ÚNICA VEZ por sessão do servidor.
                    # cpu_percent(interval=None) depende de estado interno acumulado
                    # entre chamadas no MESMO objeto — recriar a cada tick zera esse
                    # estado e faz o valor voltar a 0 % sempre.
                    if getattr(self, '_ps_proc', None) is None:
                        self._ps_proc    = psutil.Process(self.ctrl.proc.pid)
                        self._cpu_primed = False

                    p = self._ps_proc

                    # ── RAM ──────────────────────────────────────────────────
                    ram_bytes = p.memory_info().rss
                    total_ram = psutil.virtual_memory().total
                    ram_pct   = ram_bytes / total_ram * 100 if total_ram else 0
                    ram_gb    = ram_bytes / 1024 ** 3
                    ram_fg    = _metric_color(ram_pct, self._blink_on)
                    if ram_gb >= 1:
                        ram_text = f"{ram_gb:.1f} GB"
                    else:
                        ram_text = f"{ram_bytes / 1024**2:.0f} MB"

                    # ── CPU ──────────────────────────────────────────────────
                    # Primeiro tick: "prime" — o psutil precisa de duas amostras
                    # do mesmo objeto para calcular a diferença de tempo de CPU.
                    if not self._cpu_primed:
                        p.cpu_percent(interval=None)   # descarta; só inicializa
                        self._cpu_primed = True
                        cpu_text = "—"
                        cpu_fg   = FG_MUTED
                    else:
                        # Retorna % relativa ao total de núcleos (ex: 800 % em 8 cores).
                        # Exibimos o valor bruto — é o mesmo que o Gerenciador de Tarefas
                        # mostra na coluna "CPU" por processo.
                        cpu_pct  = p.cpu_percent(interval=None)
                        cpu_text = f"{cpu_pct:.0f}%"
                        cpu_fg   = _metric_color(cpu_pct, self._blink_on)

                    self.metrics["RAM"].config(text=ram_text, fg=ram_fg)
                    self.metrics["CPU"].config(text=cpu_text, fg=cpu_fg)
                except psutil.NoSuchProcess:
                    self._ps_proc = None   # processo morreu; reseta para próxima sessão
            else:
                self.metrics["RAM"].config(text="N/A", fg=FG_MUTED)
                self.metrics["CPU"].config(text="N/A", fg=FG_MUTED)


            if self.ctrl.uptime_start:
                e = int(time.time() - self.ctrl.uptime_start)
                h, m, s = e//3600, (e%3600)//60, e%60
                self.metrics["Uptime"].config(text=f"{h:02d}:{m:02d}:{s:02d}", fg=FG)

        else:
            for v in self.metrics.values():
                v.config(text="—", fg=FG_MUTED)

        self.root.after(1000, self._tick)

    # ──────────────────────────────────────────────────────────────────────────
    #  CONFIGURAÇÕES
    # ──────────────────────────────────────────────────────────────────────────
    def _open_folder(self):
        path = self.settings.server_dir or (
            str(Path(self.settings.jar_path).parent) if self.settings.jar_path else None
        )
        if not path:
            messagebox.showwarning("MineRun", "Nenhuma pasta de servidor configurada.\nDefina-a em ⚙ Configurações.")
            return
        try:
            import platform
            system = platform.system()
            if system == "Windows":
                os.startfile(path)
            elif system == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("MineRun", f"Não foi possível abrir a pasta:\n{e}")

    def open_settings(self):
        w = tk.Toplevel(self.root)
        w.title("Configurações — MineRun")
        w.configure(bg=BG)
        w.resizable(True, True)
        w.grab_set()

        # Header
        h = tk.Frame(w, bg=BG_HEADER, pady=14)
        h.pack(fill="x")
        lbl(h, "  ⚙  Configurações do Servidor",
            font=F_TITLE, fg=FG, bg=BG_HEADER).pack(side="left", padx=10)
        sep(w).pack(fill="x")

        # Canvas scrollável
        outer  = tk.Frame(w, bg=BG)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=BG, bd=0, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)
        sb_cfg = FlatScrollbar(outer, command=canvas.yview)
        sb_cfg.pack(side="right", fill="y", padx=(2,4), pady=4)
        canvas.config(yscrollcommand=sb_cfg.set)

        c   = tk.Frame(canvas, bg=BG, padx=28, pady=18)
        wid = canvas.create_window((0,0), window=c, anchor="nw")
        c.bind("<Configure>",    lambda _: canvas.config(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))

        def _wheel(e): canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _wheel)
        w.bind("<Destroy>", lambda _: canvas.unbind_all("<MouseWheel>"))

        # ── Campos ────────────────────────────────────────────────────────────
        vars_map: dict[str, tk.StringVar] = {}
        row = 0

        def _section(title: str):
            nonlocal row
            sec = tk.Frame(c, bg=BG)
            sec.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(18,6))
            lbl(sec, title, font=("Segoe UI", 8, "bold"), fg=GREEN, bg=BG).pack(side="left")
            tk.Frame(sec, bg=BORDER, height=1).pack(side="left", fill="x",
                                                    expand=True, padx=(10,0))
            row += 1

        def _field(attr: str, label: str, browse_kind=None, widget_override=None):
            nonlocal row
            var = tk.StringVar(value=getattr(self.settings, attr, ""))
            vars_map[attr] = var

            lbl(c, label, fg=FG_MUTED, bg=BG, width=22).grid(
                row=row, column=0, sticky="w", pady=6)

            if widget_override:
                widget_override(c, var).grid(
                    row=row, column=1, sticky="ew", padx=(8,6), pady=6, ipady=4)
            else:
                ent = styled_entry(c, textvariable=var, width=36)
                ent.grid(row=row, column=1, sticky="ew", padx=(8,6), pady=6, ipady=6)
                if browse_kind:
                    Btn(c, "…", color=BG_CARD, fg=FG_MUTED, font=F_XSM, padx=8,
                        command=lambda e=ent, k=browse_kind, t=label:
                            self._browse(e, t, k)
                        ).grid(row=row, column=2, sticky="w", pady=6)
            row += 1

        # GC — dropdown personalizado: Entry + Toplevel/Listbox com tema escuro
        def _gc_combo(parent, var):
            values = list(GC_OPTIONS.keys())
            if var.get() not in values:
                var.set(values[0])

            # --- Frame externo (borda estilizada, igual aos Entry da tela) ---
            frame = tk.Frame(parent, bg=BG_INPUT,
                             highlightthickness=1,
                             highlightbackground=BORDER,
                             highlightcolor=GREEN)

            entry = tk.Entry(frame, textvariable=var,
                             state="readonly", readonlybackground=BG_INPUT,
                             fg=FG, font=F_UI, relief="flat", bd=0,
                             cursor="arrow")
            entry.pack(side="left", fill="both", expand=True, padx=(8, 0))

            arrow = tk.Label(frame, text="\u25be", bg=BG_INPUT, fg=FG_MUTED,
                             font=("Segoe UI", 10), cursor="hand2", padx=10)
            arrow.pack(side="right", fill="y")

            # --- Popup ---
            _pop = [None]

            def _close(event=None):
                if _pop[0]:
                    try:
                        _pop[0].destroy()
                    except Exception:
                        pass
                    _pop[0] = None
                frame.config(highlightbackground=BORDER)
                arrow.config(fg=FG_MUTED)
                try:
                    if w.winfo_exists():
                        w.grab_set()
                except Exception:
                    pass

            def _open(event=None):
                # Alterna: segundo clique fecha
                if _pop[0]:
                    _close()
                    return

                # Libera o grab modal para o popup funcionar
                try:
                    w.grab_release()
                except Exception:
                    pass

                frame.update_idletasks()
                fx  = frame.winfo_rootx()
                fy  = frame.winfo_rooty()
                fw  = frame.winfo_width()
                fh  = frame.winfo_height()

                pop = tk.Toplevel(frame)
                pop.overrideredirect(True)
                pop.configure(bg=BORDER)
                _pop[0] = pop

                # Scrollbar flat
                sb = tk.Scrollbar(pop, orient="vertical",
                                  relief="flat", bd=0,
                                  troughcolor=BG_CARD, bg=BORDER,
                                  activebackground=FG_MUTED, width=8)

                lb = tk.Listbox(pop, bg=BG_CARD, fg=FG, font=F_UI,
                                selectbackground="#264f78",
                                selectforeground=FG,
                                activestyle="none",
                                relief="flat", bd=0,
                                highlightthickness=0,
                                yscrollcommand=sb.set)

                for val in values:
                    lb.insert("end", "  " + val)

                # Pré-seleciona valor atual
                try:
                    idx = values.index(var.get())
                    lb.selection_set(idx)
                    lb.see(idx)
                except ValueError:
                    pass

                n_visible = min(len(values), 8)
                lb.config(height=n_visible)

                if len(values) > 8:
                    sb.config(command=lb.yview)
                    sb.pack(side="right", fill="y", pady=1)

                lb.pack(side="left", fill="both", expand=True, padx=1, pady=1)

                lb.update_idletasks()
                pop_h = lb.winfo_reqheight() + 2
                pop.geometry(f"{fw}x{pop_h}+{fx}+{fy + fh}")

                # O popup captura todos os eventos
                pop.grab_set()
                lb.focus_set()

                def _select(e=None):
                    sel = lb.curselection()
                    if sel:
                        var.set(values[sel[0]])
                    _close()

                def _motion(e):
                    idx = lb.nearest(e.y)
                    lb.selection_clear(0, "end")
                    lb.selection_set(idx)

                lb.bind("<ButtonRelease-1>", _select)
                lb.bind("<Motion>",          _motion)
                lb.bind("<Return>",          _select)
                lb.bind("<Escape>",          lambda e: _close())
                lb.bind("<Up>",   lambda e: (
                    lb.selection_clear(0, "end"),
                    lb.selection_set(max(0, (lb.curselection() or (0,))[0] - 1)),
                    lb.see((lb.curselection() or (0,))[0])
                ))
                lb.bind("<Down>", lambda e: (
                    lb.selection_clear(0, "end"),
                    lb.selection_set(min(len(values)-1, (lb.curselection() or (len(values)-1,))[0] + 1)),
                    lb.see((lb.curselection() or (0,))[0])
                ))
                # Clique fora da listbox (na borda do popup) fecha
                pop.bind("<ButtonPress-1>", lambda e: _close())

            def _hover_on(e=None):
                frame.config(highlightbackground=FG_MUTED)
                arrow.config(fg=FG)

            def _hover_off(e=None):
                if not _pop[0]:
                    frame.config(highlightbackground=BORDER)
                    arrow.config(fg=FG_MUTED)

            for wgt in (frame, entry, arrow):
                wgt.bind("<ButtonPress-1>", _open)
                wgt.bind("<Enter>",         _hover_on)
                wgt.bind("<Leave>",         _hover_off)

            return frame

        _section("🖥  SERVIDOR")
        _field("server_dir",  "Pasta do Servidor",    browse_kind="dir")
        _field("java_path",   "Executável Java",       browse_kind="file")
        _field("jar_path",    "Arquivo JAR",           browse_kind="jar")

        _section("💾  MEMÓRIA")
        _field("xms",         "Memória Inicial (GB)")
        _field("xmx",         "Memória Máxima (GB)")

        _section("⚙  JVM")
        _field("gc",          "Garbage Collector",     widget_override=_gc_combo)
        _field("encoding",    "Encoding")
        _field("locale",      "Idioma  (ex: pt_BR)")
        _field("extra_args",  "Argumentos extras")

        _section("🌐  SERVIDOR")
        _field("server_args", "Argumentos do Servidor")

        c.columnconfigure(1, weight=1)

        # Rodapé
        sep(w).pack(fill="x")
        foot = tk.Frame(w, bg=BG_HEADER, pady=10)
        foot.pack(fill="x")
        Btn(foot, "Cancelar", color=BG_CARD, fg=FG_MUTED,
            command=w.destroy).pack(side="right", padx=6)
        Btn(foot, "Salvar", color=GREEN, fg="#000",
            command=lambda: self._save_settings(w, vars_map)).pack(side="right", padx=6)

        w.update_idletasks()
        cw = 640
        ch = min(c.winfo_reqheight() + 56 + 56 + 8, 700)
        x  = (self.root.winfo_screenwidth()  - cw) // 2
        y  = (self.root.winfo_screenheight() - ch) // 2
        w.geometry(f"{cw}x{ch}+{x}+{y}")
        w.minsize(520, 420)

    def _save_settings(self, win, vars_map: dict):
        for attr, var in vars_map.items():
            setattr(self.settings, attr, var.get().strip())
        self.settings.save()
        self.console.write_success("Configurações salvas.")
        win.destroy()

    def _browse(self, ent_widget, title: str, kind: str):
        if kind == "jar":
            p = filedialog.askopenfilename(
                title=title, filetypes=[("JAR", "*.jar"), ("Todos", "*.*")])
        elif kind == "file":
            p = filedialog.askopenfilename(title=title)
        else:
            p = filedialog.askdirectory(title=title)
        if p:
            ent_widget.delete(0, "end")
            ent_widget.insert(0, p)

    def _on_close(self):
        """Chamado ao fechar a janela — encerra servidor se estiver rodando."""
        if self.ctrl.state == ONLINE and self.ctrl.proc:
            self.log_warn("Fechando MineRun — encerrando servidor...")
            self.ctrl.force_kill()
        self.root.destroy()

    # ──────────────────────────────────────────────────────────────────────────
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    MineRunApp().run()
