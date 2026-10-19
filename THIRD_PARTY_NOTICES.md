# Avisos de terceros

Este proyecto reutiliza material de terceros con licencias que permiten su uso. Aquí se conserva el aviso que esas licencias exigen.

## Plantilla de interfaz: shadcn-dashboard-landing-template

Los componentes de `frontend/src/components/ui/` y la estructura de la barra lateral se adaptaron de
<https://github.com/shadcnstore/shadcn-dashboard-landing-template> (versión Vite), que a su vez se basa en
[shadcn/ui](https://ui.shadcn.com). Cambios propios: tema de colores, textos en español, sustitución del
paquete `cn` por `clsx` + `tailwind-merge` y eliminación de lo que el proyecto no usa.

```
MIT License

Copyright (c) 2025 ShadcnStore

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Imágenes (`frontend/public/images/`)

Obtenidas de Wikimedia Commons; la licencia de cada archivo se verificó en su página antes de usarla.

| Archivo | Obra | Autoría | Licencia |
|---|---|---|---|
| `promotoras-salud.jpg` | [Community Health Workers](https://commons.wikimedia.org/wiki/File:Community_Health_Workers_(5762479865).jpg) | USAID Africa Bureau | Dominio público |
| `oximetro.jpg` | [Pulox Pulse Oximeter](https://commons.wikimedia.org/wiki/File:Pulox_Pulse_Oximeter.JPG) | Stefan Bellini | CC0 |

Ambas imágenes se redimensionaron y comprimieron. La licencia cubre los derechos de autor, no el derecho a la
propia imagen de las personas que aparecen en la foto: si el proyecto se publica fuera del ámbito académico,
conviene sustituirla por una foto propia del equipo con autorización de quienes salgan.

## Dependencias

Las librerías de `backend/requirements.txt` y `frontend/package.json` conservan sus propias licencias
(Tailwind CSS, Base UI, lucide-react, Recharts, React, FastAPI, entre otras, todas de código abierto).
