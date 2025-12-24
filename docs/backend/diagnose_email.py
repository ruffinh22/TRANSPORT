#!/usr/bin/env python3
"""
Diagnostic avancé de la configuration email RumoRush
"""

import socket
import telnetlib
import ssl
import smtplib
from email.mime.text import MIMEText
import dns.resolver
import subprocess
import sys

def test_dns_resolution():
    """Test de résolution DNS"""
    print("🧪 Test de résolution DNS...")
    
    try:
        # Test résolution DNS
        result = socket.gethostbyname('mail.rumorush.com')
        print(f"✅ mail.rumorush.com résolu vers: {result}")
        
        # Test des enregistrements MX
        try:
            mx_records = dns.resolver.resolve('rumorush.com', 'MX')
            print("📧 Enregistrements MX trouvés:")
            for mx in mx_records:
                print(f"   Priority {mx.preference}: {mx.exchange}")
        except Exception as e:
            print(f"⚠️ Pas d'enregistrements MX trouvés: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de résolution DNS: {e}")
        return False

def test_port_connectivity():
    """Test de connectivité aux ports SMTP"""
    print("\n🧪 Test de connectivité aux ports...")
    
    host = 'mail.rumorush.com'
    ports = [25, 465, 587, 2525]  # Ports SMTP communs
    
    results = {}
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((host, port))
            
            if result == 0:
                print(f"✅ Port {port}: OUVERT")
                results[port] = True
                
                # Test de réponse SMTP
                try:
                    sock.send(b'EHLO test\r\n')
                    response = sock.recv(1024).decode()
                    if '250' in response or '220' in response:
                        print(f"   📧 Réponse SMTP valide sur le port {port}")
                except:
                    pass
            else:
                print(f"❌ Port {port}: FERMÉ")
                results[port] = False
            
            sock.close()
            
        except Exception as e:
            print(f"❌ Port {port}: ERREUR - {e}")
            results[port] = False
    
    return results

def test_telnet_connection():
    """Test de connexion telnet"""
    print("\n🧪 Test de connexion telnet...")
    
    try:
        # Essayer différents ports
        for port in [25, 587, 465]:
            try:
                print(f"   Essai du port {port}...")
                tn = telnetlib.Telnet('mail.rumorush.com', port, timeout=10)
                response = tn.read_until(b'\n', timeout=5)
                print(f"✅ Port {port} - Réponse: {response.decode().strip()}")
                tn.close()
                return True, port
            except Exception as e:
                print(f"❌ Port {port} - Erreur: {e}")
                continue
        
        return False, None
        
    except Exception as e:
        print(f"❌ Erreur telnet générale: {e}")
        return False, None

def test_alternative_configs():
    """Test de configurations alternatives"""
    print("\n🧪 Test de configurations alternatives...")
    
    configs = [
        {'host': 'mail.rumorush.com', 'port': 25, 'tls': False, 'ssl': False},
        {'host': 'mail.rumorush.com', 'port': 587, 'tls': True, 'ssl': False},
        {'host': 'mail.rumorush.com', 'port': 465, 'tls': False, 'ssl': True},
        {'host': 'smtp.rumorush.com', 'port': 587, 'tls': True, 'ssl': False},
        {'host': 'rumorush.com', 'port': 587, 'tls': True, 'ssl': False},
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"\n   Config {i}: {config['host']}:{config['port']} (TLS={config['tls']}, SSL={config['ssl']})")
        
        try:
            if config['ssl']:
                # SSL direct
                server = smtplib.SMTP_SSL(config['host'], config['port'], timeout=10)
            else:
                server = smtplib.SMTP(config['host'], config['port'], timeout=10)
                if config['tls']:
                    server.starttls()
            
            print(f"✅ Connexion réussie à {config['host']}:{config['port']}")
            
            # Test d'authentification
            try:
                server.login('support@rumorush.com', '7VHSQNzKj4T3Xy')
                print("✅ Authentification réussie !")
                server.quit()
                return config
            except Exception as auth_e:
                print(f"❌ Authentification échouée: {auth_e}")
                server.quit()
                
        except Exception as e:
            print(f"❌ Connexion échouée: {e}")
    
    return None

def test_network_tools():
    """Test avec des outils réseau système"""
    print("\n🧪 Test avec outils réseau système...")
    
    # Test ping
    try:
        result = subprocess.run(['ping', '-c', '1', 'mail.rumorush.com'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Ping réussi vers mail.rumorush.com")
        else:
            print("❌ Ping échoué vers mail.rumorush.com")
    except Exception as e:
        print(f"⚠️ Impossible de tester ping: {e}")
    
    # Test traceroute
    try:
        result = subprocess.run(['traceroute', '-m', '5', 'mail.rumorush.com'], 
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print("✅ Traceroute disponible")
            lines = result.stdout.split('\n')[:3]  # Premiers sauts
            for line in lines:
                if line.strip():
                    print(f"   {line}")
        else:
            print("❌ Traceroute non disponible")
    except Exception as e:
        print(f"⚠️ Traceroute non installé: {e}")

def get_current_ip():
    """Obtenir l'IP actuelle"""
    try:
        # IP publique
        result = subprocess.run(['curl', '-s', 'ifconfig.me'], 
                              capture_output=True, text=True, timeout=10)
        public_ip = result.stdout.strip()
        
        # IP locale
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        print(f"\n📍 Informations réseau:")
        print(f"   IP locale: {local_ip}")
        print(f"   IP publique: {public_ip}")
        print(f"   Hostname: {hostname}")
        
    except Exception as e:
        print(f"⚠️ Impossible d'obtenir les IPs: {e}")

def suggest_solutions(working_config=None):
    """Suggérer des solutions"""
    print("\n" + "="*50)
    print("💡 SUGGESTIONS DE SOLUTIONS")
    print("="*50)
    
    if working_config:
        print(f"✅ Configuration fonctionnelle trouvée:")
        print(f"   Host: {working_config['host']}")
        print(f"   Port: {working_config['port']}")
        print(f"   TLS: {working_config['tls']}")
        print(f"   SSL: {working_config['ssl']}")
        print("\n📧 Utilisez cette configuration dans vos settings Django.")
    else:
        print("❌ Aucune configuration fonctionnelle trouvée.")
        print("\n🔧 Actions recommandées:")
        print("1. Vérifiez que le serveur mail.rumorush.com est opérationnel")
        print("2. Contactez votre hébergeur pour vérifier:")
        print("   - Que le serveur SMTP est accessible")
        print("   - Que les ports SMTP ne sont pas bloqués")
        print("   - Que les credentials sont corrects")
        print("3. Testez depuis un autre serveur/réseau")
        print("4. Vérifiez les logs du serveur SMTP")
        
        print("\n🔄 Alternatives temporaires:")
        print("1. Utilisez un service SMTP externe (Gmail, SendGrid, etc.)")
        print("2. Configurez un serveur SMTP local pour développement")
        print("3. Utilisez le backend console en développement")

def main():
    print("🎮 RumoRush - Diagnostic Email Avancé")
    print("="*50)
    
    get_current_ip()
    
    # Tests de diagnostic
    dns_ok = test_dns_resolution()
    port_results = test_port_connectivity()
    telnet_ok, telnet_port = test_telnet_connection()
    
    test_network_tools()
    
    working_config = test_alternative_configs()
    
    # Résumé
    print("\n" + "="*50)
    print("📊 RÉSUMÉ DU DIAGNOSTIC")
    print("="*50)
    print(f"DNS Resolution:    {'✅ OK' if dns_ok else '❌ ERREUR'}")
    print(f"Port 25:          {'✅ OUVERT' if port_results.get(25) else '❌ FERMÉ'}")
    print(f"Port 587:         {'✅ OUVERT' if port_results.get(587) else '❌ FERMÉ'}")
    print(f"Port 465:         {'✅ OUVERT' if port_results.get(465) else '❌ FERMÉ'}")
    print(f"Telnet Test:      {'✅ OK' if telnet_ok else '❌ ERREUR'}")
    print(f"Working Config:   {'✅ TROUVÉE' if working_config else '❌ AUCUNE'}")
    
    suggest_solutions(working_config)

if __name__ == "__main__":
    main()