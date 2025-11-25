#!/bin/bash
# Complete VPS Backend Deployment Script

VPS_IP="192.3.81.106"
VPS_USER="root"
APP_DIR="/opt/email_finder_2/backend"

echo "🚀 Starting VPS Backend Deployment..."

echo ""
echo "📦 Step 1: Creating application directory on VPS..."
ssh ${VPS_USER}@${VPS_IP} "mkdir -p ${APP_DIR}"

echo ""
echo "📦 Step 2: Transferring backend files..."
scp -r backend/* ${VPS_USER}@${VPS_IP}:${APP_DIR}/

echo ""
echo "🔧 Step 3: Setting up Python environment..."
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
cd /opt/email_finder_2/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
ENDSSH

echo ""
echo "📝 Step 4: Verifying .env configuration..."
ssh ${VPS_USER}@${VPS_IP} "cat ${APP_DIR}/.env"

echo ""
echo "🚀 Step 5: Starting the server..."
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
cd /opt/email_finder_2/backend
source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /var/log/email_finder.log 2>&1 &
echo "Server started. PID: $!"
sleep 2
ps aux | grep uvicorn
ENDSSH

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📡 API URL: http://${VPS_IP}:8000"
echo "📋 Logs: ssh ${VPS_USER}@${VPS_IP} 'tail -f /var/log/email_finder.log'"
echo ""
echo "🧪 Test with:"
echo "curl -X POST http://${VPS_IP}:8000/api/find-email \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"domain\":\"outlook.com\",\"fullName\":\"Satya Nadella\"}'"
