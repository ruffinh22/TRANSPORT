#!/bin/bash
# Script de surveillance des retours FeexPay en temps réel

echo "🔍 Surveillance FeexPay en temps réel"
echo "===================================="
echo "⏰ Démarré: $(date)"
echo "❌ Ctrl+C pour arrêter"
echo ""

# Créer les dossiers de logs s'ils n'existent pas
mkdir -p webhook_captures
mkdir -p captures
mkdir -p logs

# Fonction de cleanup
cleanup() {
    echo -e "\n👋 Surveillance arrêtée"
    exit 0
}
trap cleanup SIGINT

# Surveillance des fichiers de log et captures
echo "👀 Surveillance active des fichiers:"
echo "   📁 webhook_captures/"
echo "   📁 captures/"  
echo "   📄 logs/rumo_rush.log"
echo ""

# Utiliser inotifywait si disponible, sinon polling
if command -v inotifywait > /dev/null 2>&1; then
    echo "🚀 Mode surveillance avancé (inotify)"
    
    inotifywait -m -e create,modify --format '%T %w%f %e' --timefmt '%H:%M:%S' \
        webhook_captures/ captures/ logs/ 2>/dev/null | while read line; do
        
        timestamp=$(echo $line | cut -d' ' -f1)
        file=$(echo $line | cut -d' ' -f2)
        event=$(echo $line | cut -d' ' -f3)
        
        if [[ "$file" == *"webhook_raw_"* ]]; then
            echo "🔔 [$timestamp] WEBHOOK REÇU: $(basename "$file")"
            if [[ -f "$file" ]]; then
                echo "   📋 Contenu:"
                # Afficher les premières lignes du webhook
                head -20 "$file" | sed 's/^/      /'
                echo ""
            fi
            
        elif [[ "$file" == *"feexpay_capture_"* ]]; then
            echo "📸 [$timestamp] CAPTURE CRÉÉE: $(basename "$file")"
            
        elif [[ "$file" == *"rumo_rush.log" ]]; then
            # Filtrer les logs FeexPay
            tail -1 "$file" | grep -i feexpay && {
                echo "📝 [$timestamp] LOG FEEXPAY: $(tail -1 "$file")"
            }
        fi
    done
    
else
    echo "⚡ Mode surveillance simple (polling)"
    
    last_webhook_count=0
    last_capture_count=0
    
    while true; do
        # Compter les nouveaux fichiers
        webhook_count=$(find webhook_captures/ -name "webhook_raw_*.json" 2>/dev/null | wc -l)
        capture_count=$(find captures/ -name "feexpay_capture_*.json" 2>/dev/null | wc -l)
        
        # Nouveaux webhooks
        if [[ $webhook_count -gt $last_webhook_count ]]; then
            new_webhooks=$((webhook_count - last_webhook_count))
            echo "🔔 [$(date '+%H:%M:%S')] $new_webhooks nouveau(x) webhook(s) reçu(s)"
            
            # Afficher le dernier webhook
            latest_webhook=$(find webhook_captures/ -name "webhook_raw_*.json" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
            if [[ -f "$latest_webhook" ]]; then
                echo "   📋 Dernier webhook: $(basename "$latest_webhook")"
                echo "   📄 Extrait:"
                head -10 "$latest_webhook" | sed 's/^/      /'
                echo ""
            fi
            last_webhook_count=$webhook_count
        fi
        
        # Nouvelles captures
        if [[ $capture_count -gt $last_capture_count ]]; then
            new_captures=$((capture_count - last_capture_count))
            echo "📸 [$(date '+%H:%M:%S')] $new_captures nouvelle(s) capture(s)"
            last_capture_count=$capture_count
        fi
        
        # Vérifier les logs récents
        if [[ -f "logs/rumo_rush.log" ]]; then
            # Logs des 5 dernières secondes contenant "feexpay"
            find logs/ -name "*.log" -newermt '5 seconds ago' -exec grep -l -i feexpay {} \; 2>/dev/null | while read logfile; do
                echo "📝 [$(date '+%H:%M:%S')] Activité FeexPay dans: $logfile"
                tail -5 "$logfile" | grep -i feexpay | sed 's/^/      /'
            done
        fi
        
        sleep 2
    done
fi