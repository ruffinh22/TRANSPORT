#!/bin/bash
# Script SQL pour mettre à jour les références FeexPay et les statuts

cd /var/www/html/backend

echo "🔄 Mise à jour des retraits via SQL..."

# Connexion PostgreSQL et mise à jour
psql -U admin -d rhumo << 'SQL'

-- Retrait 1: 450 FCFA
UPDATE feexpay_withdrawals 
SET 
    feexpay_transfer_id = '74ce8827-0415-45f5-a974-0000b423f406',
    status = 'completed',
    processed_at = NOW(),
    feexpay_response = '{"status": "SUCCESSFUL", "reference": "74ce8827-0415-45f5-a974-0000b423f406", "amount": 450}'::jsonb,
    updated_at = NOW()
WHERE id = '1f1718c5-a30b-49b9-ba39-e4739cc55fac';

-- Retrait 2: 550 FCFA  
UPDATE feexpay_withdrawals 
SET 
    feexpay_transfer_id = '8874b3f5-3bd2-4e8a-8b16-03b2f3a994be',
    status = 'completed',
    processed_at = NOW(),
    feexpay_response = '{"status": "SUCCESSFUL", "reference": "8874b3f5-3bd2-4e8a-8b16-03b2f3a994be", "amount": 550}'::jsonb,
    updated_at = NOW()
WHERE id = '6254c363-56d0-41cd-9f55-ebb7bd685e00';

-- Afficher les résultats
SELECT 
    id,
    amount,
    status,
    feexpay_transfer_id,
    created_at
FROM feexpay_withdrawals
WHERE id IN (
    '1f1718c5-a30b-49b9-ba39-e4739cc55fac',
    '6254c363-56d0-41cd-9f55-ebb7bd685e00'
)
ORDER BY created_at DESC;

SQL

echo ""
echo "✅ Retraits mis à jour !"
echo "🔄 Redémarrez Gunicorn si nécessaire: sudo systemctl restart gunicorn"
