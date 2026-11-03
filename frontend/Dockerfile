# Imagen del frontend para el perfil local: servidor de desarrollo de Vite con recarga en caliente.
FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173
# --host 0.0.0.0 para que el navegador de la PC pueda entrar al contenedor.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
