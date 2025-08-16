# Editorial Engine Deployment Guide

## Local Development

### Quick Start
```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 2. Start platform
./start.sh

# 3. Test platform
python test_platform.py
```

### Manual Setup
```bash
# Start services
cd deploy
docker compose up --build

# Check logs
docker compose logs -f

# Stop services
docker compose down
```

## Production Deployment

### Prerequisites
- Docker Swarm or Kubernetes cluster
- Load balancer (nginx, HAProxy, or cloud LB)
- Persistent storage for Redis, Prometheus, and Grafana
- SSL certificates for HTTPS endpoints

### Environment Configuration

Create production `.env`:
```bash
# API Keys (required)
TAVILY_API_KEY=tvly-your-production-key
OPENAI_API_KEY=sk-your-production-key
SEVEN011_API_KEY=your-0711-production-key

# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview

# 0711 Integration
SEVEN011_BASE_URL=https://your-0711-production-host
COLLECTION=production_collection

# Redis Configuration
REDIS_URL=redis://redis-cluster:6379/0
REDIS_PASSWORD=your-secure-password

# Vertical Configuration
VERTICAL_CONFIG=./configs/verticals/tax_de.yaml

# Security
SECRET_KEY=your-very-secure-secret-key
ALLOWED_HOSTS=your-domain.com,api.your-domain.com

# Monitoring
PROMETHEUS_RETENTION=30d
GRAFANA_ADMIN_PASSWORD=secure-admin-password
```

### Docker Swarm Deployment

1. **Initialize Swarm**:
```bash
docker swarm init
```

2. **Create production compose file** (`docker-compose.prod.yml`):
```yaml
version: "3.9"
services:
  redis:
    image: redis:7-alpine
    deploy:
      replicas: 1
      placement:
        constraints: [node.role == manager]
    volumes:
      - redis_data:/data
    networks:
      - editorial_network

  orchestrator:
    image: editorial-engine/orchestrator:latest
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
    environment:
      - REDIS_URL=redis://redis:6379/0
    networks:
      - editorial_network
      - traefik_public
    labels:
      - traefik.enable=true
      - traefik.http.routers.orchestrator.rule=Host(`api.your-domain.com`)
      - traefik.http.services.orchestrator.loadbalancer.server.port=8080

  worker-discovery:
    image: editorial-engine/worker-discovery:latest
    deploy:
      replicas: 2
    networks:
      - editorial_network

  worker-intake:
    image: editorial-engine/worker-intake:latest
    deploy:
      replicas: 4
    networks:
      - editorial_network

  worker-understanding:
    image: editorial-engine/worker-understanding:latest
    deploy:
      replicas: 2
    networks:
      - editorial_network

  worker-editorial:
    image: editorial-engine/worker-editorial:latest
    deploy:
      replicas: 2
    networks:
      - editorial_network

  worker-ingestion:
    image: editorial-engine/worker-ingestion:latest
    deploy:
      replicas: 3
    networks:
      - editorial_network

  ui-search:
    image: editorial-engine/ui-search:latest
    deploy:
      replicas: 2
    networks:
      - editorial_network
      - traefik_public
    labels:
      - traefik.enable=true
      - traefik.http.routers.search.rule=Host(`search.your-domain.com`)
      - traefik.http.services.search.loadbalancer.server.port=3000

networks:
  editorial_network:
    driver: overlay
  traefik_public:
    external: true

volumes:
  redis_data:
```

3. **Deploy stack**:
```bash
docker stack deploy -c docker-compose.prod.yml editorial-engine
```

### Kubernetes Deployment

1. **Create namespace**:
```bash
kubectl create namespace editorial-engine
```

2. **Apply configurations**:
```bash
# ConfigMaps and Secrets
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Services
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/orchestrator.yaml
kubectl apply -f k8s/workers.yaml
kubectl apply -f k8s/ui-search.yaml

# Ingress
kubectl apply -f k8s/ingress.yaml
```

### Load Balancer Configuration

#### Nginx Configuration
```nginx
upstream orchestrator {
    server orchestrator-1:8080;
    server orchestrator-2:8080;
}

upstream search-ui {
    server ui-search-1:3000;
    server ui-search-2:3000;
}

server {
    listen 443 ssl http2;
    server_name api.your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://orchestrator;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl http2;
    server_name search.your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://search-ui;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring & Alerting

### Prometheus Alerts
Create `alerts.yml`:
```yaml
groups:
  - name: editorial-engine
    rules:
      - alert: WorkerDown
        expr: up{job=~"worker-.*"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Editorial Engine worker is down"
          
      - alert: HighTaskFailureRate
        expr: rate(celery_task_failed_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High task failure rate detected"
```

### Grafana Dashboards
Import dashboard templates from `deploy/grafana/dashboards/`:
- Editorial Engine Overview
- Worker Performance
- Content Quality Metrics
- 0711 Integration Health

## Security Considerations

### Network Security
- Use private networks for internal communication
- Implement firewall rules to restrict access
- Enable TLS for all external endpoints

### API Security
- Rotate API keys regularly
- Use strong authentication for admin endpoints
- Implement rate limiting on public endpoints

### Data Security
- Encrypt sensitive data at rest
- Use secure secrets management (Vault, K8s secrets)
- Regular security audits and updates

## Backup & Recovery

### Data Backup
```bash
# Redis backup
docker exec redis redis-cli BGSAVE
docker cp redis:/data/dump.rdb ./backups/

# Grafana backup
docker exec grafana tar -czf - /var/lib/grafana | gzip > ./backups/grafana-$(date +%Y%m%d).tar.gz

# Configuration backup
tar -czf ./backups/configs-$(date +%Y%m%d).tar.gz configs/
```

### Disaster Recovery
1. Restore Redis data from backup
2. Redeploy services with same configuration
3. Verify 0711 Agent System connectivity
4. Run platform tests to ensure functionality

## Scaling Guidelines

### Horizontal Scaling
- **Discovery Workers**: Scale based on query volume
- **Intake Workers**: Scale based on content fetch rate
- **Understanding Workers**: Scale based on LLM processing needs
- **Editorial Workers**: Scale based on fact-checking requirements
- **Ingestion Workers**: Scale based on 0711 API throughput

### Vertical Scaling
- Increase memory for workers processing large documents
- Increase CPU for compute-intensive tasks (embeddings, NLP)
- Use GPU instances for local LLM deployments

### Performance Tuning
- Adjust Celery concurrency based on workload
- Optimize Redis memory usage and persistence
- Tune 0711 API request batching
- Implement caching for frequently accessed data

## Troubleshooting

### Common Issues
1. **Worker stuck**: Check Redis connection and restart worker
2. **0711 API errors**: Verify API key and endpoint availability
3. **Memory issues**: Reduce worker concurrency or increase memory limits
4. **Slow processing**: Check LLM provider rate limits and response times

### Debug Commands
```bash
# Check service status
docker service ls
kubectl get pods -n editorial-engine

# View logs
docker service logs editorial-engine_worker-discovery
kubectl logs -f deployment/worker-discovery -n editorial-engine

# Connect to Redis
docker exec -it redis redis-cli
kubectl exec -it redis-0 -n editorial-engine -- redis-cli

# Monitor tasks
# Access Flower dashboard at http://flower.your-domain.com
```

## Maintenance

### Regular Tasks
- Monitor disk usage and clean up old logs
- Update Docker images and security patches
- Review and rotate API keys
- Backup configuration and data
- Performance monitoring and optimization

### Updates
1. Test updates in staging environment
2. Use rolling updates to minimize downtime
3. Verify functionality after updates
4. Rollback plan in case of issues