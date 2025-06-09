# Linux Task Manager
Screenshots


![Screenshot](https://i.ibb.co/TMRgWFnN/Screenshot-2025-06-09-13-11-10.png)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white&style=for-the-badge)](https://www.python.org/)
[![GTK](https://img.shields.io/badge/GTK-476A34?logo=gtk&logoColor=white&style=for-the-badge)](https://www.gtk.org/)
[![PyPI](https://img.shields.io/pypi/v/psutil?logo=python&logoColor=white&style=for-the-badge)](https://pypi.org/project/psutil/)

A lightweight **GTK 3** application for Linux that provides real-time monitoring and management of:

- System processes  
- CPU / RAM usage  
- Disk partitions  
- Network interfaces  

It features a modern sidebar interface, a searchable process list with kill functionality, and dynamic visualizations — built with **Python**, **GTK**, and **psutil**.

---

## Table of Contents

- [Features](#features)  
- [Requirements](#requirements)  
- [Installation](#installation)  
- [Usage](#usage)  
- [Contributing](#contributing)  
- [License](#license)  
- [Contact](#contact)

---

## Features

### 🧠 Processes
- List all processes with PID, name, CPU %, and RAM %
- Search by name or PID
- Right-click to end or kill process (with confirmation)

### 💻 System
- Live CPU and memory bars
- Uptime and system load

### 💾 Disk
- Mounted partitions with used and available space

### 🌐 Network
- Interfaces with IP address and data sent/received

### 🧩 Interface
- Sidebar navigation (System, Processes, Disk, Network)
- Fully responsive and dark themed
- Auto-refresh every 3 seconds

---

## Requirements

- Python 3.7+
- GTK 3 and PyGObject
- `psutil` Python package

---

## Installation

Choose the instructions for your Linux distro:

### ✅ Debian / Ubuntu

```bash
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-psutil git
git clone https://github.com/abhijithmr226/linux-task-manager.git
cd linux-task-manager
python3 main.py
