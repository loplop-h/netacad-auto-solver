# 🎯 CCNA Netacad Auto-Solver

Programa automático para resolver tests/exámenes de Cisco Netacad usando respuestas de [ITExamAnswers.net](https://itexamanswers.net).

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Playwright](https://img.shields.io/badge/Playwright-Browser%20Automation-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Características

- 🤖 **Auto-resolve** tests CCNA automáticamente
- 🔍 **Fuzzy matching** — funciona aunque las preguntas varíen
- 📦 **Caché de respuestas** — no re-descarga si ya las tiene
- 🖥️ **Login manual** — tú controlas tu sesión (más seguro)
- 🌐 **Multiplataforma** — Windows, Mac, Linux

## 🚀 Instalación

### 1. Requisitos previos
- [Python 3.8+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/) (opcional, para clonar)

### 2. Clonar e instalar

```bash
# Clonar el repo
git clone https://github.com/tu-usuario/netacad-auto-solver.git
cd netacad-auto-solver

# Instalar dependencias
pip install -r requirements.txt

# Instalar navegador Chromium (solo la primera vez)
playwright install chromium
```

## 📖 Uso

### Ejecutar el programa

```bash
python solver.py
```

### Paso a paso:

1. **Pega la URL de las respuestas** de ITExamAnswers.net
   ```
   📎 Answer key URL: https://itexamanswers.net/ccna-1-v7-modules-8-10-communicating-between-networks-exam-answers.html
   ```

2. **El programa descarga y parsea las respuestas** automáticamente

3. **Se abre Chrome** — inicia sesión en Netacad

4. **Navega al test** que quieres resolver

5. **Pulsa ENTER** cuando la primera pregunta sea visible

6. **¡El programa selecciona las respuestas correctas automáticamente!** 🎉

## 📝 URLs de Exámenes Soportados

| Módulos | URL de Respuestas |
|---|---|
| 1-3 | `https://itexamanswers.net/ccna-1-v7-modules-1-3-exam-answers.html` |
| 4-7 | `https://itexamanswers.net/ccna-1-v7-modules-4-7-exam-answers.html` |
| 8-10 | `https://itexamanswers.net/ccna-1-v7-modules-8-10-communicating-between-networks-exam-answers.html` |
| 11-13 | `https://itexamanswers.net/ccna-1-v7-modules-11-13-ip-addressing-exam-answers-full.html` |
| 14-15 | `https://itexamanswers.net/ccna-1-v7-modules-14-15-exam-answers.html` |
| 16-17 | `https://itexamanswers.net/ccna-1-v7-modules-16-17-exam-answers.html` |

> Puedes usar **cualquier URL** de ITExamAnswers, no solo las listadas aquí.

## 🏗️ Estructura del Proyecto

```
netacad-auto-solver/
├── solver.py              # Script principal (lo que ejecutas)
├── requirements.txt       # Dependencias Python
├── README.md              # Este archivo
├── src/
│   ├── __init__.py
│   ├── scraper.py         # Scraper de respuestas
│   ├── matcher.py         # Fuzzy matching pregunta↔respuesta
│   ├── browser.py         # Control del navegador
│   └── question_handler.py # Manejo de tipos de pregunta
└── exams/                 # Caché de respuestas
    └── .gitkeep
```

## ⚙️ Cómo funciona

```
ITExamAnswers.net ──→ Scraper ──→ Answer Key (JSON)
                                       │
Netacad Test ──→ Browser ──→ Read Question
                    │              │
                    │         Fuzzy Match ←── Answer Key
                    │              │
                    └── Click Answer + Submit
```

1. **Scraper**: Descarga la página de respuestas y extrae las correctas (marcadas en rojo)
2. **Matcher**: Compara el texto de la pregunta del test con el answer key usando similitud difusa
3. **Browser**: Controla Chrome con Playwright para leer preguntas, seleccionar respuestas y pulsar Submit

## 🐛 Solución de problemas

| Problema | Solución |
|---|---|
| `playwright` no instalado | `pip install playwright && playwright install chromium` |
| El scraper no encuentra respuestas | Verifica que la URL de ITExamAnswers sea correcta |
| No selecciona la respuesta correcta | El test puede tener preguntas nuevas no cubiertas |
| El navegador se cierra solo | Ejecuta de nuevo; a veces Netacad tiene timeouts |

## 📄 Licencia

MIT License — usa, modifica y comparte libremente.

## ⚠️ Disclaimer

Este proyecto es solo para fines educativos. El uso de este software es responsabilidad del usuario. Asegúrate de cumplir con las políticas de tu institución educativa.
