#!/usr/bin/env python3
"""
Dynamic Docker Compose Generator for Hyperledger Fabric

This script generates docker-compose.yaml files based on deployment configuration,
allowing flexible resource allocation based on system capabilities and user preferences.
"""

import json
import yaml
import logging
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class DockerComposeGenerator:
    """Generate dynamic docker-compose files based on deployment configuration"""
    
    def __init__(self, config_path: str = "deployment-config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def generate_docker_compose(self) -> Dict[str, Any]:
        """Generate docker-compose configuration"""
        config = self.config
        
        docker_compose = {
            'version': '3.7',
            'services': {},
            'volumes': {},
            'networks': {
                'lgcse': {
                    'driver': 'bridge'
                }
            }
        }
        
        # Generate CA services
        self._generate_ca_services(docker_compose, config)
        
        # Generate orderer services
        self._generate_orderer_services(docker_compose, config)
        
        # Generate peer services
        self._generate_peer_services(docker_compose, config)
        
        # Generate CouchDB services
        self._generate_couchdb_services(docker_compose, config)
        
        # Generate monitoring services
        if config.get('monitoring', False):
            self._generate_monitoring_services(docker_compose, config)
        
        # Generate CLI service
        self._generate_cli_service(docker_compose, config)
        
        # Generate volumes
        self._generate_volumes(docker_compose, config)
        
        return docker_compose
    
    def _generate_ca_services(self, docker_compose: Dict[str, Any], config: Dict[str, Any]):
        """Generate Certificate Authority services"""
        services = docker_compose['services']
        
        # Orderer CA
        services['ca.orderer.example.com'] = {
            'image': 'hyperledger/fabric-ca:latest',
            'environment': [
                'FABRIC_CA_HOME=/etc/hyperledger/fabric-ca-server',
                'FABRIC_CA_SERVER_CA_NAME=ca-orderer',
                'FABRIC_CA_SERVER_TLS_ENABLED=true',
                'FABRIC_CA_SERVER_PORT=7054',
                'FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS=0.0.0.0:17054'
            ],
            'ports': ['7054:7054', '17054:17054'],
            'command': 'sh -c \'fabric-ca-server start -b admin:adminpw -d\'',
            'volumes': [
                '../organizations/fabric-ca/ordererOrg:/etc/hyperledger/fabric-ca-server'
            ],
            'container_name': 'ca_orderer',
            'networks': ['lgcse']
        }
        
        # Organization CAs
        org_msp_mapping = {
            'EcolOrgMSP': 'ecol',
            'LimkokwingOrgMSP': 'limkokwing',
            'BothoOrgMSP': 'botho',
            'NulOrgMSP': 'nul'
        }
        
        org_ports = {
            'ecol': 8054,
            'limkokwing': 9054,
            'botho': 10054,
            'nul': 11054
        }
        
        for org_msp in config['organizations']:
            org_name = org_msp_mapping.get(org_msp, org_msp.lower())
            port = org_ports.get(org_name, 8054)
            
            services[f'ca.{org_name}.example.com'] = {
                'image': 'hyperledger/fabric-ca:latest',
                'environment': [
                    f'FABRIC_CA_HOME=/etc/hyperledger/fabric-ca-server',
                    f'FABRIC_CA_SERVER_CA_NAME=ca-{org_name}',
                    'FABRIC_CA_SERVER_TLS_ENABLED=true',
                    f'FABRIC_CA_SERVER_PORT={port}',
                    f'FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS=0.0.0.0:{port + 10000}'
                ],
                'ports': [f'{port}:{port}', f'{port + 10000}:{port + 10000}'],
                'command': 'sh -c \'fabric-ca-server start -b admin:adminpw -d\'',
                'volumes': [
                    f'../organizations/fabric-ca/{org_name}Org:/etc/hyperledger/fabric-ca-server'
                ],
                'container_name': f'ca_{org_name}',
                'networks': ['lgcse']
            }
    
    def _generate_orderer_services(self, docker_compose: Dict[str, Any], config: Dict[str, Any]):
        """Generate Orderer services"""
        services = docker_compose['services']
        orderer_count = config.get('orderers', 1)
        
        for i in range(orderer_count):
            orderer_name = f'orderer{i}.example.com' if i > 0 else 'orderer.example.com'
            orderer_port = 7050 + i
            admin_port = 7053 + i
            
            services[orderer_name] = {
                'image': 'hyperledger/fabric-orderer:latest',
                'environment': [
                    'FABRIC_LOGGING_SPEC=INFO',
                    'ORDERER_GENERAL_LISTENADDRESS=0.0.0.0',
                    f'ORDERER_GENERAL_LISTENPORT={orderer_port}',
                    'ORDERER_GENERAL_BOOTSTRAPMETHOD=none',
                    'ORDERER_CHANNELPARTICIPATION_ENABLED=true',
                    f'ORDERER_GENERAL_LOCALMSPID=OrdererMSP',
                    'ORDERER_GENERAL_TLS_ENABLED=true',
                    'ORDERER_GENERAL_TLS_PRIVATEKEY=/etc/hyperledger/fabric/tls/server.key',
                    'ORDERER_GENERAL_TLS_CERTIFICATE=/etc/hyperledger/fabric/tls/server.crt',
                    'ORDERER_GENERAL_TLS_ROOTCAS=[/etc/hyperledger/fabric/tls/ca.crt]',
                    'ORDERER_KAFKA_TOPIC_REPLICATIONFACTOR=1',
                    'ORDERER_KAFKA_VERBOSE=true',
                    'ORDERER_GENERAL_CLUSTER_CLIENTCERTIFICATE=/etc/hyperledger/fabric/tls/server.crt',
                    'ORDERER_GENERAL_CLUSTER_CLIENTPRIVATEKEY=/etc/hyperledger/fabric/tls/server.key',
                    'ORDERER_GENERAL_CLUSTER_ROOTCAS=[/etc/hyperledger/fabric/tls/ca.crt]',
                    f'ORDERER_ADMIN_LISTENADDRESS=0.0.0.0:{admin_port}',
                    'ORDERER_ADMIN_TLS_ENABLED=true',
                    'ORDERER_ADMIN_TLS_PRIVATEKEY=/etc/hyperledger/fabric/tls/server.key',
                    'ORDERER_ADMIN_TLS_CERTIFICATE=/etc/hyperledger/fabric/tls/server.crt',
                    'ORDERER_ADMIN_TLS_ROOTCAS=[/etc/hyperledger/fabric/tls/ca.crt]',
                    'ORDERER_ADMIN_TLS_CLIENTROOTCAS=[/etc/hyperledger/fabric/tls/ca.crt]',
                    'ORDERER_METRICS_PROVIDER=prometheus',
                    f'ORDERER_OPERATIONS_LISTENADDRESS=0.0.0.0:{admin_port + 2000}',
                    'ORDERER_OPERATIONS_TLS_ENABLED=true',
                    'ORDERER_OPERATIONS_TLS_PRIVATEKEY=/etc/hyperledger/fabric/tls/server.key',
                    'ORDERER_OPERATIONS_TLS_CERTIFICATE=/etc/hyperledger/fabric/tls/server.crt',
                    'ORDERER_OPERATIONS_TLS_ROOTCAS=[/etc/hyperledger/fabric/tls/ca.crt]',
                    'ORDERER_OPERATIONS_TLS_CLIENTROOTCAS=[/etc/hyperledger/fabric/tls/ca.crt]'
                ],
                'working_dir': '/opt/gopath/src/github.com/hyperledger/fabric/orderer',
                'command': 'orderer',
                'ports': [f'{orderer_port}:{orderer_port}', f'{admin_port}:{admin_port}', f'{admin_port + 2000}:{admin_port + 2000}'],
                'volumes': [
                    f'../organizations/ordererOrganizations/example.com/orderers/{orderer_name}/msp:/etc/hyperledger/fabric/msp',
                    f'../organizations/ordererOrganizations/example.com/orderers/{orderer_name}/tls:/etc/hyperledger/fabric/tls',
                    f'{orderer_name}:/etc/hyperledger/fabric/orderer.example.com'
                ],
                'container_name': orderer_name,
                'networks': ['lgcse']
            }
    
    def _generate_peer_services(self, docker_compose: Dict[str, Any], config: Dict[str, Any]):
        """Generate Peer services"""
        services = docker_compose['services']
        org_msp_mapping = {
            'EcolOrgMSP': 'ecol',
            'LimkokwingOrgMSP': 'limkokwing',
            'BothoOrgMSP': 'botho',
            'NulOrgMSP': 'nul'
        }
        
        org_ports = {
            'ecol': 7051,
            'limkokwing': 9051,
            'botho': 11051,
            'nul': 12051
        }
        
        peers_per_org = config.get('peers_per_org', 1)
        
        for org_msp in config['organizations']:
            org_name = org_msp_mapping.get(org_msp, org_msp.lower())
            base_port = org_ports.get(org_name, 7051)
            
            for i in range(peers_per_org):
                peer_name = f'peer{i}.{org_name}.example.com'
                peer_port = base_port + (i * 1000)
                chaincode_port = peer_port + 1
                operations_port = 9444 + (i * 10)
                
                # Determine CouchDB index
                couchdb_index = 0
                if org_name == 'ecol':
                    couchdb_index = i
                elif org_name == 'limkokwing':
                    couchdb_index = 1 + i
                elif org_name == 'botho':
                    couchdb_index = 2 + i
                elif org_name == 'nul':
                    couchdb_index = 3 + i
                
                services[peer_name] = {
                    'image': 'hyperledger/fabric-peer:latest',
                    'environment': [
                        f'CORE_PEER_ID={peer_name}',
                        f'CORE_PEER_ADDRESS={peer_name}:{peer_port}',
                        f'CORE_PEER_LISTENADDRESS=0.0.0.0:{peer_port}',
                        f'CORE_PEER_CHAINCODEADDRESS={peer_name}:{chaincode_port}',
                        f'CORE_PEER_CHAINCODELISTENADDRESS=0.0.0.0:{chaincode_port}',
                        f'CORE_PEER_GOSSIP_BOOTSTRAP={peer_name}:{peer_port}',
                        f'CORE_PEER_GOSSIP_EXTERNALENDPOINT={peer_name}:{peer_port}',
                        f'CORE_PEER_LOCALMSPID={org_msp}',
                        'CORE_PEER_TLS_ENABLED=true',
                        f'CORE_PEER_TLS_CERT_FILE=/etc/hyperledger/fabric/tls/server.crt',
                        f'CORE_PEER_TLS_KEY_FILE=/etc/hyperledger/fabric/tls/server.key',
                        f'CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt',
                        'CORE_MSP_CONFIGPATH=/etc/hyperledger/fabric/msp',
                        f'CORE_OPERATIONS_LISTENADDRESS={peer_name}:{operations_port}',
                        'CORE_OPERATIONS_TLS_ENABLED=true',
                        f'CORE_OPERATIONS_TLS_CERT_FILE=/etc/hyperledger/fabric/tls/server.crt',
                        f'CORE_OPERATIONS_TLS_KEY_FILE=/etc/hyperledger/fabric/tls/server.key',
                        f'CORE_OPERATIONS_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt',
                        'CORE_METRICS_PROVIDER=prometheus',
                        'FABRIC_LOGGING_SPEC=INFO',
                        'CORE_CHAINCODE_LOGGING_LEVEL=INFO',
                        'CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock',
                        'CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE=lgcse',
                        'FABRIC_CFG_PATH=/etc/hyperledger/fabric',
                        'CORE_LEDGER_STATE_STATEDATABASE=CouchDB',
                        f'CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS=couchdb{couchdb_index}:5984',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME=admin',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD=adminpw',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_MAXRETRIES=3',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_MAXRETRIES_ONSTARTUP=10',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_REQUEST_TIMEOUT=35s',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_INTERNAL_QUERY_LIMIT=1000',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_MAX_BATCH_UPDATE_SIZE=500'
                    ],
                    'working_dir': '/opt/gopath/src/github.com/hyperledger/fabric/peer',
                    'command': 'peer node start',
                    'ports': [f'{peer_port}:{peer_port}', f'{chaincode_port}:{chaincode_port}', f'{operations_port}:{operations_port}'],
                    'volumes': [
                        f'../organizations/peerOrganizations/{org_name}.example.com/peers/{peer_name}/msp:/etc/hyperledger/fabric/msp',
                        f'../organizations/peerOrganizations/{org_name}.example.com/peers/{peer_name}/tls:/etc/hyperledger/fabric/tls',
                        f'{peer_name}:/etc/hyperledger/fabric',
                        '/var/run/docker.sock:/host/var/run/docker.sock'
                    ],
                    'container_name': peer_name,
                    'networks': ['lgcse'],
                    'depends_on': [f'couchdb{couchdb_index}']
                }
    
    def _generate_couchdb_services(self, docker_compose: Dict[str, Any], config: Dict[str, Any]):
        """Generate CouchDB services"""
        services = docker_compose['services']
        
        # Calculate total number of CouchDB instances needed
        org_msp_mapping = {
            'EcolOrgMSP': 'ecol',
            'LimkokwingOrgMSP': 'limkokwing',
            'BothoOrgMSP': 'botho',
            'NulOrgMSP': 'nul'
        }
        
        peers_per_org = config.get('peers_per_org', 1)
        total_couchdbs = len(config['organizations']) * peers_per_org
        
        for i in range(total_couchdbs):
            couchdb_port = 5984 + i
            services[f'couchdb{i}'] = {
                'image': 'couchdb:3.3.2',
                'environment': [
                    'COUCHDB_USER=admin',
                    'COUCHDB_PASSWORD=adminpw'
                ],
                'ports': [f'{couchdb_port}:5984'],
                'container_name': f'couchdb{i}',
                'networks': ['lgcse']
            }
    
    def _generate_monitoring_services(self, docker_compose: Dict[str, Any], config: Dict[str, Any]):
        """Generate monitoring services"""
        services = docker_compose['services']
        
        # Prometheus
        services['prometheus'] = {
            'image': 'prom/prometheus:latest',
            'ports': ['9090:9090'],
            'volumes': [
                './monitoring/prometheus.yml:/etc/prometheus/prometheus.yml',
                'prometheus_data:/prometheus'
            ],
            'container_name': 'prometheus',
            'networks': ['lgcse']
        }
        
        # Grafana
        services['grafana'] = {
            'image': 'grafana/grafana:latest',
            'ports': ['3000:3000'],
            'environment': [
                'GF_SECURITY_ADMIN_PASSWORD=admin'
            ],
            'volumes': [
                'grafana_data:/var/lib/grafana',
                './monitoring/grafana/provisioning:/etc/grafana/provisioning'
            ],
            'container_name': 'grafana',
            'networks': ['lgcse']
        }
        
        # PostgreSQL for Grafana
        services['postgres'] = {
            'image': 'postgres:14',
            'environment': [
                'POSTGRES_DB=fabricexplorer',
                'POSTGRES_USER=postgres',
                'POSTGRES_PASSWORD=postgrespw'
            ],
            'ports': ['5432:5432'],
            'volumes': [
                'pgdata:/var/lib/postgresql/data'
            ],
            'container_name': 'postgres',
            'networks': ['lgcse']
        }
        
        # Blockchain Explorer
        services['explorer'] = {
            'image': 'ghcr.io/hyperledger-labs/explorer:latest',
            'environment': [
                'DATABASE_HOST=postgres',
                'DATABASE_USERNAME=postgres',
                'DATABASE_PASSWORD=postgrespw',
                'DATABASE_NAME=fabricexplorer',
                'BLOCKCHAIN_NETWORK_TYPE=fabric',
                'LOG_LEVEL_APP=info',
                'LOG_LEVEL_DB=info',
                'LOG_LEVEL_CONSOLE=debug',
                'DISCOVERY_AS_localhost=true',
                'SYNC_BLOCKS_LCINMILSEC=10000',
                'TLS_CERTFILES=/hyperledger/explorer/app/platform/fabric/blocks',
                'TLS_PRIVATEKEY=/hyperledger/explorer/app/platform/fabric/crypto-config',
                '/tmp/hyperledger:/tmp/hyperledger'
            ],
            'ports': ['8080:8080'],
            'volumes': [
                '../explorer/config:/hyperledger/explorer/app/platform/fabric/blocks',
                '../explorer/crypto:/hyperledger/explorer/app/platform/fabric/crypto-config',
                '/tmp/hyperledger:/tmp/hyperledger'
            ],
            'container_name': 'explorer',
            'depends_on': ['postgres'],
            'networks': ['lgcse']
        }
        
        docker_compose['volumes'].update({
            'prometheus_data': None,
            'grafana_data': None,
            'pgdata': None
        })
    
    def _generate_cli_service(self, docker_compose: Dict[str, Any], config: Dict[str, Any]):
        """Generate CLI service"""
        services = docker_compose['services']
        
        # Get first organization for CLI
        first_org = config['organizations'][0] if config['organizations'] else 'EcolOrgMSP'
        
        services['cli'] = {
            'image': 'hyperledger/fabric-tools:latest',
            'tty': True,
            'stdin_open': True,
            'environment': [
                'GOPATH=/opt/gopath',
                'CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock',
                'FABRIC_LOGGING_SPEC=INFO',
                'FABRIC_CFG_PATH=/etc/hyperledger/fabric',
                'CORE_PEER_TLS_ENABLED=true',
                f'CORE_PEER_LOCALMSPID={first_org}',
                f'CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/{first_org.lower().replace('orgmsp', '')}.example.com/peers/peer0.{first_org.lower().replace('orgmsp', '')}.example.com/tls/ca.crt',
                f'CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/{first_org.lower().replace('orgmsp', '')}.example.com/users/Admin@{first_org.lower().replace('orgmsp', '')}.example.com/msp',
                f'CORE_PEER_ADDRESS=peer0.{first_org.lower().replace('orgmsp', '')}.example.com:7051'
            ],
            'working_dir': '/opt/gopath/src/github.com/hyperledger/fabric/peer',
            'command': '/bin/bash',
            'volumes': [
                '../organizations:/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations',
                '../scripts:/opt/gopath/src/github.com/hyperledger/fabric/peer/scripts/',
                '../config:/opt/gopath/src/github.com/hyperledger/fabric/peer/config/',
                '/var/run/docker.sock:/host/var/run/docker.sock'
            ],
            'container_name': 'cli',
            'networks': ['lgcse']
        }
    
    def _generate_volumes(self, docker_compose: Dict[str, Any], config: Dict[str, Any]):
        """Generate volume definitions"""
        volumes = docker_compose['volumes']
        
        # Service volumes
        for i in range(config.get('orderers', 1)):
            orderer_name = f'orderer{i}.example.com' if i > 0 else 'orderer.example.com'
            volumes[orderer_name] = None
        
        # Peer volumes
        org_msp_mapping = {
            'EcolOrgMSP': 'ecol',
            'LimkokwingOrgMSP': 'limkokwing',
            'BothoOrgMSP': 'botho',
            'NulOrgMSP': 'nul'
        }
        
        peers_per_org = config.get('peers_per_org', 1)
        
        for org_msp in config['organizations']:
            org_name = org_msp_mapping.get(org_msp, org_msp.lower())
            
            for i in range(peers_per_org):
                peer_name = f'peer{i}.{org_name}.example.com'
                volumes[peer_name] = None
    
    def save_docker_compose(self, output_path: str = "docker-compose.yaml"):
        """Save docker-compose.yaml file"""
        try:
            docker_compose = self.generate_docker_compose()
            
            # Convert to YAML
            yaml_content = yaml.dump(docker_compose, default_flow_style=False, sort_keys=False)
            
            # Save to file
            with open(output_path, 'w') as f:
                f.write(yaml_content)
            
            logger.info(f"Docker compose configuration saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save docker-compose: {e}")
            raise

def main():
    """Main function for testing"""
    generator = DockerComposeGenerator()
    generator.save_docker_compose()

if __name__ == "__main__":
    main()
