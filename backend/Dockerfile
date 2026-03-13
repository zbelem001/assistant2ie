# Utiliser une image Python officielle légère
FROM python:3.11-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code backend
COPY . .

# Exposer le port sur lequel l'API va tourner
EXPOSE 8000

# Commande pour démarrer l'application
CMD ["python", "api.py"]
