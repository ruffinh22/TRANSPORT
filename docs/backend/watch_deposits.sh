#!/bin/bash
# Script simple pour surveiller les logs de dépôt en temps réel

echo "🔍 Surveillance LOGS DÉPÔT en temps réel"
echo "======================================="
echo "⏰ Démarré: $(date)"
echo "❌ Ctrl+C pour arrêter"
echo ""

# Fonction de nettoyage
cleanup() {
    echo -e "\n👋 Surveillance arrêtée"
    exit 0
}
trap cleanup SIGINT

# Surveillance des logs Django
echo "👀 Surveillance des logs Django..."

if [[ -f "logs/rumo_rush.log" ]]; then
    echo "📄 Fichier de log trouvé: logs/rumo_rush.log"
    echo "🔄 Surveillance en temps réel..."
    echo ""
    
    # Suivre les logs en filtrant les termes pertinents
    tail -f logs/rumo_rush.log | grep --line-buffered -E "(DEPOSIT|deposit|FEEXPAY|feexpay|Transaction|ERROR|WARNING)" --color=always
else
    echo "❌ Fichier logs/rumo_rush.log non trouvé"
    echo "📁 Surveillance du serveur de développement..."
    echo ""
    
    # Surveiller les logs du serveur en direct (si le serveur tourne)
    echo "Surveillez la console du serveur Django pour voir les logs détaillés"
    echo "Les logs s'affichent directement dans le terminal où vous avez lancé:"
    echo "  python manage.py runserver"
    echo "  ou"
    echo "  uvicorn rumo_rush.asgi:application --reload"
    echo ""
    
    # Tenter de surveiller les processus Python en cours
    while true; do
        echo "⏰ $(date '+%H:%M:%S') - En attente des logs..."
        
        # Vérifier s'il y a des nouveaux fichiers de log
        if [[ -f "logs/rumo_rush.log" ]]; then
            echo "✅ Fichier de log détecté! Basculement vers surveillance fichier..."
            exec tail -f logs/rumo_rush.log | grep --line-buffered -E "(DEPOSIT|deposit|FEEXPAY|feexpay|Transaction|ERROR|WARNING)" --color=always
        fi
        
        sleep 5
    done
fi