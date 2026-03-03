from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)

# In-memory storage for demo (replace with database in production)
institutions_db = []
join_requests_db = []
peers_db = []

class Institution:
    def __init__(self, data):
        self.id = str(uuid.uuid4())
        self.name = data['name']
        self.type = data['type']  # 'issuer' or 'verifier'
        self.role = data.get('role', 'verifier')
        self.peer_model = data.get('peer_model', 'hosted')
        self.msp_id = f"Org{len(institutions_db) + 1}MSP"
        self.status = 'pending'
        self.created_at = datetime.now().isoformat()
        self.peers = []
        self.config = {}

class JoinRequest:
    def __init__(self, data):
        self.id = str(uuid.uuid4())
        self.institution_name = data['institution_name']
        self.requested_role = data['requested_role']
        self.contact_email = data['contact_email']
        self.peer_model = data.get('peer_model', 'hosted')
        self.status = 'pending'
        self.submitted_at = datetime.now().isoformat()
        self.documents = data.get('documents', [])
        self.contact_person = data.get('contact_person', '')

class Peer:
    def __init__(self, institution_id, peer_model='hosted'):
        self.id = str(uuid.uuid4())
        self.institution_id = institution_id
        self.peer_model = peer_model
        self.name = f"peer{len(peers_db)}.org{institution_id}.certivert.com"
        self.status = 'stopped'
        self.created_at = datetime.now().isoformat()
        self.resources = {
            'cpu': '2 cores',
            'memory': '4GB',
            'storage': '100GB'
        }

@app.route('/api/institutions/join-request', methods=['POST'])
def submit_join_request():
    """Submit a request to join the CertiVert network"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['institution_name', 'requested_role', 'contact_email']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create join request
        join_request = JoinRequest(data)
        join_requests_db.append(join_request.__dict__)
        
        return jsonify({
            'success': True,
            'message': 'Join request submitted successfully',
            'request_id': join_request.id,
            'next_steps': [
                'Your application will be reviewed within 1-2 business days',
                'You may be contacted for additional information',
                'Upon approval, you will receive an onboarding package'
            ]
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/institutions/requests', methods=['GET'])
def get_join_requests():
    """Get all pending join requests (admin only)"""
    try:
        return jsonify({
            'success': True,
            'requests': join_requests_db,
            'count': len(join_requests_db)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/institutions/requests/<request_id>/approve', methods=['POST'])
def approve_join_request(request_id):
    """Approve a join request and create institution (admin only)"""
    try:
        # Find the request
        request_obj = None
        for req in join_requests_db:
            if req['id'] == request_id:
                request_obj = req
                break
        
        if not request_obj:
            return jsonify({'error': 'Join request not found'}), 404
        
        # Create institution
        institution_data = {
            'name': request_obj['institution_name'],
            'type': request_obj['requested_role'],
            'role': request_obj['requested_role'],
            'peer_model': request_obj['peer_model']
        }
        
        institution = Institution(institution_data)
        institution.status = 'active'
        institutions_db.append(institution.__dict__)
        
        # Update request status
        request_obj['status'] = 'approved'
        request_obj['approved_at'] = datetime.now().isoformat()
        request_obj['institution_id'] = institution.id
        
        # Generate MSP package
        msp_package = generate_msp_package(institution)
        
        # Generate connection profile
        connection_profile = generate_connection_profile(institution)
        
        # If hosted peer model, create peer
        if institution.peer_model == 'hosted':
            peer = Peer(institution.id, 'hosted')
            peer.status = 'running'
            peers_db.append(peer.__dict__)
            institution.peers.append(peer.id)
        
        return jsonify({
            'success': True,
            'message': 'Institution approved successfully',
            'institution': institution.__dict__,
            'msp_package': msp_package,
            'connection_profile': connection_profile,
            'next_steps': [
                'MSP certificates generated',
                'Channel configuration updated',
                'Peer deployment initiated' if institution.peer_model == 'hosted' else 'BYO peer setup instructions sent'
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/institutions', methods=['GET'])
def get_institutions():
    """Get all institutions in the network"""
    try:
        return jsonify({
            'success': True,
            'institutions': institutions_db,
            'count': len(institutions_db)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/institutions/<institution_id>', methods=['GET'])
def get_institution(institution_id):
    """Get institution details"""
    try:
        institution = None
        for inst in institutions_db:
            if inst['id'] == institution_id:
                institution = inst
                break
        
        if not institution:
            return jsonify({'error': 'Institution not found'}), 404
        
        # Get institution's peers
        institution_peers = [p for p in peers_db if p['institution_id'] == institution_id]
        
        return jsonify({
            'success': True,
            'institution': institution,
            'peers': institution_peers
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/institutions/<institution_id>/onboarding-package', methods=['GET'])
def get_onboarding_package(institution_id):
    """Generate onboarding package for an institution"""
    try:
        institution = None
        for inst in institutions_db:
            if inst['id'] == institution_id:
                institution = inst
                break
        
        if not institution:
            return jsonify({'error': 'Institution not found'}), 404
        
        # Generate MSP package
        msp_package = generate_msp_package(institution)
        
        # Generate connection profile
        connection_profile = generate_connection_profile(institution)
        
        # Generate deployment scripts based on peer model
        if institution['peer_model'] == 'byo':
            deployment_guide = generate_byo_peer_guide(institution)
        else:
            deployment_guide = generate_hosted_peer_info(institution)
        
        return jsonify({
            'success': True,
            'onboarding_package': {
                'msp_package': msp_package,
                'connection_profile': connection_profile,
                'deployment_guide': deployment_guide,
                'network_config': {
                    'orderer_endpoint': 'orderer.certivert.com:7050',
                    'channel_name': 'certificates-channel',
                    'chaincode_name': 'certificate-cc',
                    'chaincode_version': '1.0'
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fabric/update-channel-config', methods=['POST'])
def update_channel_config():
    """Update Fabric channel configuration to add new organization"""
    try:
        data = request.json
        institution_id = data.get('institution_id')
        
        if not institution_id:
            return jsonify({'error': 'Institution ID required'}), 400
        
        # Find institution
        institution = None
        for inst in institutions_db:
            if inst['id'] == institution_id:
                institution = inst
                break
        
        if not institution:
            return jsonify({'error': 'Institution not found'}), 404
        
        # Simulate channel config update
        # In production, this would:
        # 1. Fetch current config block
        # 2. Create config update with new org
        # 3. Sign and submit update
        # 4. Wait for commitment
        
        return jsonify({
            'success': True,
            'message': 'Channel configuration updated successfully',
            'changes': [
                f'Added {institution["msp_id"]} to channel',
                f'Updated endorsement policy',
                f'Added anchor peer configuration'
            ],
            'next_steps': [
                'Wait for config update commitment',
                'Verify new organization can access channel',
                'Test chaincode operations'
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/peers', methods=['GET'])
def get_peers():
    """Get all managed peers"""
    try:
        return jsonify({
            'success': True,
            'peers': peers_db,
            'count': len(peers_db)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/peers/deploy', methods=['POST'])
def deploy_peer():
    """Deploy a new hosted peer"""
    try:
        data = request.json
        institution_id = data.get('institution_id')
        
        if not institution_id:
            return jsonify({'error': 'Institution ID required'}), 400
        
        # Create new peer
        peer = Peer(institution_id, 'hosted')
        peer.status = 'deploying'
        peers_db.append(peer.__dict__)
        
        # Simulate deployment
        # In production, this would:
        # 1. Provision cloud resources
        # 2. Configure Docker containers
        # 3. Set up networking
        # 4. Start Fabric peer
        
        return jsonify({
            'success': True,
            'message': 'Peer deployment initiated',
            'peer': peer.__dict__,
            'estimated_completion': '5 minutes'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/peers/<peer_id>/start', methods=['POST'])
def start_peer(peer_id):
    """Start a stopped peer"""
    try:
        peer = None
        for p in peers_db:
            if p['id'] == peer_id:
                peer = p
                break
        
        if not peer:
            return jsonify({'error': 'Peer not found'}), 404
        
        peer['status'] = 'running'
        peer['started_at'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'message': 'Peer started successfully',
            'peer': peer
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/peers/<peer_id>/stop', methods=['POST'])
def stop_peer(peer_id):
    """Stop a running peer"""
    try:
        peer = None
        for p in peers_db:
            if p['id'] == peer_id:
                peer = p
                break
        
        if not peer:
            return jsonify({'error': 'Peer not found'}), 404
        
        peer['status'] = 'stopped'
        peer['stopped_at'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'message': 'Peer stopped successfully',
            'peer': peer
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_msp_package(institution):
    """Generate MSP certificate package for an institution"""
    return {
        'msp_id': institution['msp_id'],
        'admin_certs': [
            {
                'certificate': '-----BEGIN CERTIFICATE-----\nMOCK_ADMIN_CERT\n-----END CERTIFICATE-----',
                'private_key': '-----BEGIN PRIVATE KEY-----\nMOCK_PRIVATE_KEY\n-----END PRIVATE KEY-----'
            }
        ],
        'ca_certs': [
            {
                'certificate': '-----BEGIN CERTIFICATE-----\nMOCK_CA_CERT\n-----END CERTIFICATE-----'
            }
        ],
        'tls_ca_certs': [
            {
                'certificate': '-----BEGIN CERTIFICATE-----\nMOCK_TLS_CA_CERT\n-----END CERTIFICATE-----'
            }
        ]
    }

def generate_connection_profile(institution):
    """Generate connection profile for an institution"""
    return {
        'name': 'certivert-network',
        'version': '1.0.0',
        'client': {
            'organization': institution['msp_id'],
            'connection': {
                'timeout': {
                    'peer': {
                        'endorser': '300'
                    }
                }
            }
        },
        'organizations': {
            institution['msp_id']: {
                'mspid': institution['msp_id'],
                'peers': [f'peer0.{institution["msp_id"].lower()}.certivert.com'],
                'certificateAuthorities': [f'ca.{institution["msp_id"].lower()}.certivert.com']
            }
        },
        'peers': {
            f'peer0.{institution["msp_id"].lower()}.certivert.com': {
                'url': f'grpcs://peer0.{institution["msp_id"].lower()}.certivert.com:7051',
                'tlsCACerts': {
                    'pem': '-----BEGIN CERTIFICATE-----\nMOCK_TLS_CERT\n-----END CERTIFICATE-----'
                }
            }
        }
    }

def generate_byo_peer_guide(institution):
    """Generate BYO peer deployment guide"""
    return {
        'title': f'BYO Peer Deployment Guide for {institution["name"]}',
        'sections': [
            {
                'title': 'Prerequisites',
                'content': [
                    'Docker and Docker Compose installed',
                    '4GB RAM minimum, 8GB recommended',
                    '50GB free disk space',
                    'Linux/Unix environment'
                ]
            },
            {
                'title': 'Docker Compose Configuration',
                'content': 'See attached docker-compose.yaml template'
            },
            {
                'title': 'MSP Configuration',
                'content': 'Place MSP certificates in /etc/hyperledger/fabric/msp'
            },
            {
                'title': 'Network Configuration',
                'content': 'Configure ports 7051 (gRPC) and 7053 (TLS)'
            }
        ]
    }

def generate_hosted_peer_info(institution):
    """Generate hosted peer information"""
    return {
        'title': f'Hosted Peer Information for {institution["name"]}',
        'peer_endpoint': f'peer0.{institution["msp_id"].lower()}.certivert.com:7051',
        'tls_endpoint': f'peer0.{institution["msp_id"].lower()}.certivert.com:7053',
        'status': 'provisioning',
        'estimated_ready': '15 minutes'
    }

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'api': 'running',
            'database': 'connected',
            'fabric_network': 'online'
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=8000)
