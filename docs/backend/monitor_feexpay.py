#!/usr/bin/env python
"""
Script de monitoring FeexPay en temps réel
Usage: python monitor_feexpay.py
"""

import os
import sys
import time
import django
from datetime import datetime, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.development')
django.setup()

from apps.payments.models import Transaction, FeexPayTransaction
from apps.payments.services.feexpay_service import FeexPayService
from django.contrib.auth.models import User
from django.utils import timezone

class FeexPayMonitor:
    def __init__(self):
        self.feexpay_service = FeexPayService()
        
    def check_recent_transactions(self, minutes=10):
        """Vérifier les transactions des X dernières minutes"""
        since = timezone.now() - timedelta(minutes=minutes)
        
        print(f"\n🔍 Vérification des transactions des {minutes} dernières minutes...")
        print(f"⏰ Depuis: {since.strftime('%H:%M:%S')}")
        print("=" * 60)
        
        # Transactions Django
        django_txs = Transaction.objects.filter(
            created_at__gte=since,
            method='feexpay'
        ).order_by('-created_at')
        
        # Transactions FeexPay
        feexpay_txs = FeexPayTransaction.objects.filter(
            created_at__gte=since
        ).order_by('-created_at')
        
        print(f"📊 Transactions Django: {django_txs.count()}")
        for tx in django_txs:
            status_emoji = "✅" if tx.status == 'completed' else "⏳" if tx.status == 'pending' else "❌"
            print(f"  {status_emoji} {tx.id} | {tx.amount}€ | {tx.status} | {tx.created_at.strftime('%H:%M:%S')}")
        
        print(f"\n📊 Transactions FeexPay: {feexpay_txs.count()}")
        for tx in feexpay_txs:
            status_emoji = "✅" if tx.status == 'completed' else "⏳" if tx.status == 'pending' else "❌"
            print(f"  {status_emoji} {tx.external_reference} | {tx.amount}€ | {tx.status} | {tx.created_at.strftime('%H:%M:%S')}")
        
    def check_pending_transactions(self):
        """Vérifier les transactions en attente"""
        print("\n🔄 Transactions en attente...")
        print("=" * 60)
        
        pending_txs = FeexPayTransaction.objects.filter(status='pending')
        
        if not pending_txs.exists():
            print("✅ Aucune transaction en attente")
            return
            
        for tx in pending_txs:
            print(f"⏳ {tx.external_reference} | {tx.amount}€ | Créée: {tx.created_at.strftime('%H:%M:%S')}")
            
            # Vérifier le statut sur FeexPay
            try:
                result = self.feexpay_service.check_transaction_status(tx.external_reference)
                if result:
                    remote_status = result.get('status', 'unknown')
                    print(f"   🌐 Statut FeexPay: {remote_status}")
                    
                    if remote_status != tx.status:
                        print(f"   ⚠️  Désynchronisation détectée! Local: {tx.status} | Remote: {remote_status}")
            except Exception as e:
                print(f"   ❌ Erreur vérification: {str(e)}")
    
    def sync_pending(self):
        """Synchroniser les transactions en attente"""
        print("\n🔄 Synchronisation automatique...")
        print("=" * 60)
        
        try:
            result = self.feexpay_service.sync_all_transactions()
            print(f"✅ Synchronisation terminée: {result}")
        except Exception as e:
            print(f"❌ Erreur de synchronisation: {str(e)}")
    
    def show_stats(self):
        """Afficher les statistiques"""
        print("\n📊 Statistiques générales")
        print("=" * 60)
        
        # Stats aujourd'hui
        today = timezone.now().date()
        today_txs = FeexPayTransaction.objects.filter(created_at__date=today)
        
        total = today_txs.count()
        completed = today_txs.filter(status='completed').count()
        pending = today_txs.filter(status='pending').count()
        failed = today_txs.filter(status='failed').count()
        
        total_amount = sum(tx.amount for tx in today_txs.filter(status='completed'))
        
        print(f"📅 Aujourd'hui ({today}):")
        print(f"  💰 Total traité: {total_amount}€")
        print(f"  📈 Total transactions: {total}")
        print(f"  ✅ Complétées: {completed}")
        print(f"  ⏳ En attente: {pending}")
        print(f"  ❌ Échouées: {failed}")
        
        # Taux de réussite
        if total > 0:
            success_rate = (completed / total) * 100
            print(f"  📊 Taux de réussite: {success_rate:.1f}%")
    
    def monitor_loop(self, interval=30):
        """Boucle de monitoring continue"""
        print("🚀 Monitoring FeexPay démarré...")
        print(f"🔄 Vérification toutes les {interval} secondes")
        print("❌ Ctrl+C pour arrêter")
        print("\n")
        
        try:
            while True:
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"\n⏰ {current_time} - Vérification en cours...")
                
                self.check_recent_transactions(minutes=5)
                self.check_pending_transactions()
                
                print(f"\n😴 Pause de {interval}s...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring arrêté par l'utilisateur")

def main():
    monitor = FeexPayMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "recent":
            minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            monitor.check_recent_transactions(minutes)
            
        elif command == "pending":
            monitor.check_pending_transactions()
            
        elif command == "sync":
            monitor.sync_pending()
            
        elif command == "stats":
            monitor.show_stats()
            
        elif command == "monitor":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            monitor.monitor_loop(interval)
            
        else:
            print("❌ Commande inconnue")
            print_help()
    else:
        # Mode interactif
        print("🎮 Mode interactif FeexPay Monitor")
        while True:
            print("\nOptions disponibles:")
            print("1. Vérifier transactions récentes")
            print("2. Vérifier transactions en attente") 
            print("3. Synchroniser")
            print("4. Statistiques")
            print("5. Monitoring continu")
            print("0. Quitter")
            
            choice = input("\nChoisir une option (0-5): ").strip()
            
            if choice == "1":
                minutes = input("Minutes à vérifier (défaut: 10): ").strip()
                minutes = int(minutes) if minutes.isdigit() else 10
                monitor.check_recent_transactions(minutes)
                
            elif choice == "2":
                monitor.check_pending_transactions()
                
            elif choice == "3":
                monitor.sync_pending()
                
            elif choice == "4":
                monitor.show_stats()
                
            elif choice == "5":
                interval = input("Interval en secondes (défaut: 30): ").strip()
                interval = int(interval) if interval.isdigit() else 30
                monitor.monitor_loop(interval)
                
            elif choice == "0":
                print("👋 Au revoir!")
                break
            else:
                print("❌ Option invalide")

def print_help():
    print("""
🔍 FeexPay Monitor - Commandes disponibles:

python monitor_feexpay.py                    # Mode interactif
python monitor_feexpay.py recent [minutes]   # Transactions récentes  
python monitor_feexpay.py pending            # Transactions en attente
python monitor_feexpay.py sync               # Synchroniser
python monitor_feexpay.py stats              # Statistiques
python monitor_feexpay.py monitor [interval] # Monitoring continu

Exemples:
python monitor_feexpay.py recent 30          # Dernières 30 minutes
python monitor_feexpay.py monitor 60         # Monitor toutes les 60s
""")

if __name__ == "__main__":
    main()