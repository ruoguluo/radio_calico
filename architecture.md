# RadioCalico System Architecture

```mermaid
graph TB
    %% External Services
    subgraph "External Services"
        CDN[CloudFront CDN<br/>Audio Stream & Metadata]
        HLS[HLS Stream<br/>d3d4yli4hf5bmh.cloudfront.net/hls/live.m3u8]
        META[Metadata API<br/>metadatav2.json]
        COVER[Album Art<br/>cover.jpg]
    end
    
    %% Client Layer
    subgraph "Client Layer"
        BROWSER[Web Browser]
        subgraph "Frontend Components"
            HTML[index.html<br/>UI Layout]
            CSS[styles.css<br/>Brand Styling]
            JS[script.js<br/>Audio Player Logic]
            HLSJS[HLS.js Library<br/>Streaming Support]
        end
    end
    
    %% Development Environment
    subgraph "Development Environment"
        DEV_COMPOSE[radio-russell-dev<br/>:3000]
        DEV_DB[(SQLite<br/>database.db)]
        DEV_VOL[/app/data Volume]
    end
    
    %% Production Environment
    subgraph "Production Environment"
        subgraph "Reverse Proxy Layer"
            NGINX[Nginx<br/>:80, :443<br/>Load Balancer<br/>Rate Limiting<br/>SSL Termination]
        end
        
        subgraph "Application Layer"
            APP[Flask Application<br/>radio-russell-prod:8000<br/>Gunicorn WSGI]
        end
        
        subgraph "Database Layer"
            POSTGRES[(PostgreSQL 15<br/>radio_db<br/>:5432)]
        end
        
        subgraph "Storage"
            PG_VOL[postgres-data Volume]
            NGINX_CACHE[nginx-cache Volume]
            SSL_CERTS[SSL Certificates]
        end
    end
    
    %% API Endpoints
    subgraph "Flask API Endpoints"
        API_USERS[/api/users<br/>GET/POST<br/>User Management]
        API_RATINGS[/api/ratings/&lt;song_id&gt;<br/>GET/POST<br/>Song Ratings]
        HEALTH[/health<br/>Health Checks]
        STATIC_FILES[/static/*<br/>Static Assets]
        HOME[/<br/>Main Interface]
    end
    
    %% Data Models
    subgraph "Database Schema"
        USERS_TBL[(users table<br/>id, name, email, created_at)]
        RATINGS_TBL[(song_ratings table<br/>id, song_id, user_fingerprint<br/>rating, created_at)]
    end
    
    %% Docker Network
    subgraph "Docker Network: radio-russell-network"
        DEV_NET[Development Services]
        PROD_NET[Production Services]
    end
    
    %% Connections
    %% Client to External Services
    BROWSER --> CDN
    CDN --> HLS
    CDN --> META
    CDN --> COVER
    
    %% Client Frontend Components
    BROWSER --> HTML
    HTML --> CSS
    HTML --> JS
    JS --> HLSJS
    
    %% Client to Application
    BROWSER -->|HTTP/HTTPS| NGINX
    BROWSER -->|Development| DEV_COMPOSE
    
    %% Production Flow
    NGINX -->|Load Balance| APP
    APP --> API_USERS
    APP --> API_RATINGS
    APP --> HEALTH
    APP --> STATIC_FILES
    APP --> HOME
    
    %% Database Connections
    APP -->|Production| POSTGRES
    DEV_COMPOSE -->|Development| DEV_DB
    
    %% Database Schema
    POSTGRES --> USERS_TBL
    POSTGRES --> RATINGS_TBL
    DEV_DB --> USERS_TBL
    DEV_DB --> RATINGS_TBL
    
    %% Storage Connections
    POSTGRES --> PG_VOL
    NGINX --> NGINX_CACHE
    NGINX --> SSL_CERTS
    DEV_COMPOSE --> DEV_VOL
    
    %% Metadata Flow
    JS -->|Fetch Every 10s| META
    JS -->|Load Ratings| API_RATINGS
    JS -->|Submit Ratings| API_RATINGS
    JS -->|User Management| API_USERS
    
    %% Audio Streaming
    HLSJS -->|Stream Audio| HLS
    JS -->|Control| HLSJS
    
    %% Network Grouping
    DEV_COMPOSE --> DEV_NET
    NGINX --> PROD_NET
    APP --> PROD_NET
    POSTGRES --> PROD_NET
    
    %% Styling
    classDef external fill:#E8F4FD,stroke:#1E88E5,stroke-width:2px
    classDef frontend fill:#E8F5E8,stroke:#4CAF50,stroke-width:2px
    classDef backend fill:#FFF3E0,stroke:#FF9800,stroke-width:2px
    classDef database fill:#F3E5F5,stroke:#9C27B0,stroke-width:2px
    classDef infrastructure fill:#FFEBEE,stroke:#F44336,stroke-width:2px
    classDef storage fill:#F1F8E9,stroke:#8BC34A,stroke-width:2px
    
    class CDN,HLS,META,COVER external
    class BROWSER,HTML,CSS,JS,HLSJS frontend
    class APP,DEV_COMPOSE,API_USERS,API_RATINGS,HEALTH,STATIC_FILES,HOME backend
    class POSTGRES,DEV_DB,USERS_TBL,RATINGS_TBL database
    class NGINX,DEV_NET,PROD_NET infrastructure
    class PG_VOL,NGINX_CACHE,SSL_CERTS,DEV_VOL storage
```

## Architecture Overview

### System Components

#### External Services
- **CloudFront CDN**: Delivers HLS audio streams, metadata, and album artwork
- **HLS Stream**: High-quality FLAC lossless audio streaming endpoint
- **Metadata API**: Real-time track information updated every 10 seconds
- **Album Art**: Dynamic cover art with cache-busting

#### Frontend Layer
- **Web Browser**: Client interface for audio playback and interaction
- **HTML/CSS**: Responsive UI with brand-compliant design
- **JavaScript**: Audio player controls, metadata fetching, rating system
- **HLS.js**: Browser-compatible HLS streaming library

#### Backend Services
- **Flask Application**: Python REST API server with CORS support
- **User Management API**: Registration and user data endpoints
- **Rating System**: Anonymous fingerprint-based song rating system
- **Static File Serving**: CSS, JS, and asset delivery

#### Database Layer
- **Development**: SQLite for local development with hot-reload
- **Production**: PostgreSQL 15 with persistent volumes and health checks

#### Infrastructure
- **Development Environment**: Single container with development tools
- **Production Environment**: Multi-container setup with Nginx reverse proxy
- **Docker Networks**: Isolated container communication
- **Security Features**: Rate limiting, SSL support, security headers

### Key Features
- **Lossless Audio**: 48kHz FLAC streaming via HLS
- **Real-time Metadata**: Live track updates with release year display
- **Community Ratings**: Thumbs up/down system with anonymous fingerprinting
- **Responsive Design**: Mobile-friendly interface with brand colors
- **Production Ready**: Health checks, monitoring, caching, and security hardening
