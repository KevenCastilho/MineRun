# ⛏️ MineRun

**MineRun** é um gerenciador desktop para servidores **Minecraft Java Edition**, desenvolvido em **Python** com foco em simplicidade, desempenho e independência de painéis web.

O projeto oferece uma interface moderna para iniciar, monitorar e administrar servidores Minecraft diretamente pelo desktop, reunindo em uma única aplicação recursos normalmente distribuídos entre diversos utilitários.

---

## ✨ Recursos

* Inicialização e encerramento do servidor
* Console em tempo real
* Envio de comandos diretamente ao servidor
* Monitoramento de CPU e memória
* Lista de jogadores online
* Detecção automática de entrada e saída de jogadores
* Visualização do inventário dos jogadores através dos arquivos NBT
* Leitura de:

  * `playerdata`
  * `whitelist.json`
  * `ops.json`
  * `banned-players.json`
* Cache automático de avatares dos jogadores
* Suporte a RCON
* Suporte ao protocolo Query do Minecraft
* Sistema unificado de eventos
* Filtros do console
* Instalação automática das dependências necessárias
* Interface moderna desenvolvida com Tkinter

---

## 📸 Interface

> Capturas de tela serão adicionadas em breve.

---

## 🚀 Requisitos

* Python 3.11 ou superior
* Java instalado
* Windows (desenvolvimento principal)

As dependências Python são instaladas automaticamente na primeira execução.

---

## 📦 Dependências

* psutil
* nbtlib

---

## ▶️ Como executar

Clone o repositório:

```bash
git clone https://github.com/KevenCastilho/MineRun.git
```

Entre na pasta:

```bash
cd MineRun
```

Execute:

```bash
python MineRun.pyw
```

---

## 🎮 Recursos do Minecraft

O MineRun possui compatibilidade com servidores baseados em:

* Vanilla
* Bukkit
* Spigot
* Paper
* Purpur
* Folia

Sempre que possível utiliza informações fornecidas diretamente pelo servidor (RCON, Query ou arquivos oficiais), evitando depender de mensagens localizadas do console.

---

## 📂 Estruturas suportadas

* `server.properties`
* `whitelist.json`
* `ops.json`
* `banned-players.json`
* `playerdata/*.dat`
* `level.dat` *(suporte parcial em evolução)*

---

## 🛠️ Tecnologias

* Python
* Tkinter
* psutil
* nbtlib

---

## 📌 Objetivos

O objetivo do MineRun é oferecer uma alternativa leve aos painéis web tradicionais, permitindo administrar servidores Minecraft localmente de forma simples, rápida e com uma interface intuitiva.

O projeto continua em desenvolvimento e novas funcionalidades serão adicionadas gradualmente.

---

## 📄 Licença

Este projeto está licenciado sob a licença MIT.
