# Étape 1 : Construction de l'application (Build)
FROM node:18-alpine AS build

WORKDIR /app

# Copier les fichiers de dépendances
COPY package.json package-lock.json* ./

# Installer les dépendances
RUN npm install

# Copier le reste du code frontend
COPY . .

# Construire l'application Vite (crée un dossier dist/)
RUN npm run build

# Étape 2 : Service avec Nginx (Production)
FROM nginx:alpine

# Copier les fichiers compilés depuis l'étape 1 vers Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Exposer le port par défaut de Nginx
EXPOSE 80

# Démarrer Nginx
CMD ["nginx", "-g", "daemon off;"]
