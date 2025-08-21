# 🔗 FASE 1: INTEGRACIÓN DEL WEB DASHBOARD (Días 1-2)

## SMS Marketing Platform v2.0 - Migración Sistema Actual

---

## 🎯 OBJETIVO DE LA FASE

Conectar el Web Dashboard ya desarrollado con el backend FastAPI existente, implementar endpoints faltantes y establecer la base para futuras expansiones con validación multi-plataforma.

**Duración:** 2 días
**Complejidad:** MEDIA
**Riesgo:** BAJO - No afecta sistema existente
**Prioridad:** CRÍTICA

---

## 📊 ESTADO INICIAL

### **✅ YA TENEMOS (Web Dashboard):**

- ✅ React 18 + TypeScript + Vite configurado
- ✅ Redux Toolkit con contactsSlice
- ✅ Componentes profesionales (Header, Sidebar, MetricsCards, Charts)
- ✅ Sistema de filtros avanzado
- ✅ Paginación inteligente
- ✅ Modal de extracciones
- ✅ Responsive design completo
- ✅ API client configurado con fallbacks a mock data

### **✅ YA TENEMOS (Backend):**

- ✅ FastAPI con endpoints básicos
- ✅ PostgreSQL con 31.8M contactos
- ✅ Modelos SQLAlchemy definidos
- ✅ Sistema de autenticación
- ✅ Endpoints: `/health`, `/auth`, `/contacts/stats`, `/contacts/search`

### **❌ NECESITAMOS IMPLEMENTAR:**

- ❌ Endpoints faltantes para el dashboard
- ❌ Paginación en backend
- ❌ Sistema de extracciones via API
- ❌ Integración real dashboard ↔ backend
- ❌ CORS y configuración para desarrollo

---

## 📅 DÍA 1: BACKEND API EXPANSION

### 🌅 **MAÑANA (4 horas): Endpoints Faltantes**

#### ✅ **BLOQUE 1: Endpoint de Contactos Paginado (1.5 horas)**

**Tarea 1.1: Implementar `/contacts` con paginación**

```python
# app/api/v1/endpoints/contacts.py - AGREGAR
@router.get("/", response_model=PaginatedContactResponse)
async def get_contacts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    search_query: Optional[str] = Query(None, description="Search in phone numbers"),
    state: Optional[str] = Query(None, description="Filter by state name"),
    municipality: Optional[str] = Query(None, description="Filter by municipality"),
    lada: Optional[str] = Query(None, description="Filter by LADA code"),
    date_start: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    date_end: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get paginated contacts with filters"""

    # Build base query
    query = select(Contact).where(Contact.opt_out_at.is_(None))

    # Apply filters
    if search_query:
        query = query.where(
            or_(
                Contact.phone_national.ilike(f"%{search_query}%"),
                Contact.phone_e164.ilike(f"%{search_query}%"),
                Contact.full_name.ilike(f"%{search_query}%")
            )
        )

    if state:
        query = query.where(Contact.state_name.ilike(f"%{state}%"))

    if municipality:
        query = query.where(Contact.municipality.ilike(f"%{municipality}%"))

    if lada:
        query = query.where(Contact.lada == lada)

    if date_start:
        start_date = datetime.strptime(date_start, "%Y-%m-%d")
        query = query.where(Contact.created_at >= start_date)

    if date_end:
        end_date = datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1)
        query = query.where(Contact.created_at < end_date)

    # Get total count
    count_query = select(func.count(Contact.id)).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_contacts = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    paginated_query = query.offset(offset).limit(page_size).order_by(Contact.created_at.desc())

    result = await db.execute(paginated_query)
    contacts = result.scalars().all()

    # Calculate pagination info
    total_pages = math.ceil(total_contacts / page_size) if total_contacts > 0 else 1

    return PaginatedContactResponse(
        data=contacts,
        total=total_contacts,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
```

**Tarea 1.2: Actualizar esquemas Pydantic**

```python
# app/schemas/contact.py - AGREGAR
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class PaginatedContactResponse(BaseModel):
    data: List[ContactResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class ContactStatsEnhanced(BaseModel):
    total_contacts: int
    active_contacts: int
    mobile_contacts: int
    contacts_by_state: dict[str, int]
    contacts_by_lada: dict[str, int]
    recent_extractions: int
    growth_rate: float = 0.0

class ContactFilters(BaseModel):
    search_query: Optional[str] = None
    state: Optional[str] = None
    municipality: Optional[str] = None
    lada: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
```

#### ✅ **BLOQUE 2: Endpoint de Estadísticas Mejorado (1 hora)**

**Tarea 2.1: Expandir `/contacts/stats`**

```python
# app/api/v1/endpoints/contacts.py - MODIFICAR
@router.get("/stats", response_model=ContactStatsEnhanced)
async def get_contacts_stats_enhanced(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get enhanced contacts statistics for dashboard"""

    # Total contacts
    total_query = select(func.count(Contact.id))
    total_result = await db.execute(total_query)
    total_contacts = total_result.scalar() or 0

    # Active contacts (not opted out)
    active_query = select(func.count(Contact.id)).where(Contact.opt_out_at.is_(None))
    active_result = await db.execute(active_query)
    active_contacts = active_result.scalar() or 0

    # Mobile contacts
    mobile_query = select(func.count(Contact.id)).where(Contact.is_mobile == True)
    mobile_result = await db.execute(mobile_query)
    mobile_contacts = mobile_result.scalar() or 0

    # Contacts by state (top 15 for charts)
    state_query = select(
        Contact.state_name,
        func.count(Contact.id).label("count")
    ).where(
        Contact.state_name.is_not(None)
    ).group_by(Contact.state_name).order_by(func.count(Contact.id).desc()).limit(15)

    state_result = await db.execute(state_query)
    contacts_by_state = {
        row.state_name: row.count
        for row in state_result.fetchall()
    }

    # Contacts by LADA (top 10 for charts)
    lada_query = select(
        Contact.lada,
        func.count(Contact.id).label("count")
    ).where(
        Contact.lada.is_not(None)
    ).group_by(Contact.lada).order_by(func.count(Contact.id).desc()).limit(10)

    lada_result = await db.execute(lada_query)
    contacts_by_lada = {
        row.lada: row.count
        for row in lada_result.fetchall()
    }

    # Recent extractions (placeholder - will be real in Phase 2)
    recent_extractions = 23  # Mock data for now

    # Calculate growth rate (mock for now)
    growth_rate = 12.3

    return ContactStatsEnhanced(
        total_contacts=total_contacts,
        active_contacts=active_contacts,
        mobile_contacts=mobile_contacts,
        contacts_by_state=contacts_by_state,
        contacts_by_lada=contacts_by_lada,
        recent_extractions=recent_extractions,
        growth_rate=growth_rate
    )
```

#### ✅ **BLOQUE 3: Endpoints de Ubicaciones (1 hora)**

**Tarea 3.1: Estados y municipios**

```python
# app/api/v1/endpoints/contacts.py - AGREGAR
@router.get("/states", response_model=List[str])
async def get_states(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get list of available states"""
    query = select(Contact.state_name).distinct().where(
        Contact.state_name.is_not(None)
    ).order_by(Contact.state_name)

    result = await db.execute(query)
    states = [row.state_name for row in result.fetchall()]

    return states

@router.get("/municipalities", response_model=List[str])
async def get_municipalities(
    state: Optional[str] = Query(None, description="Filter by state"),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get list of municipalities, optionally filtered by state"""
    query = select(Contact.municipality).distinct().where(
        Contact.municipality.is_not(None)
    )

    if state:
        query = query.where(Contact.state_name.ilike(f"%{state}%"))

    query = query.order_by(Contact.municipality)

    result = await db.execute(query)
    municipalities = [row.municipality for row in result.fetchall()]

    return municipalities

@router.get("/ladas", response_model=List[str])
async def get_ladas(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get list of available LADA codes"""
    query = select(Contact.lada).distinct().where(
        Contact.lada.is_not(None)
    ).order_by(Contact.lada)

    result = await db.execute(query)
    ladas = [row.lada for row in result.fetchall()]

    return ladas
```

#### ✅ **BLOQUE 4: CORS y Configuración (30 min)**

**Tarea 4.1: Configurar CORS para desarrollo**

```python
# app/main.py - MODIFICAR
from fastapi.middleware.cors import CORSMiddleware

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 🌆 **TARDE (4 horas): Integración Dashboard**

#### ✅ **BLOQUE 5: Conexión Real Dashboard (2 horas)**

**Tarea 5.1: Actualizar API client para usar backend real**

```typescript
// WebDashboard/src/services/api/ApiClient.ts - MODIFICAR
constructor(baseURL: string = 'http://localhost:8000/api/v1') {
  // Cambiar base URL para apuntar al backend real
}
```

**Tarea 5.2: Actualizar ContactsApi para endpoints reales**

```typescript
// WebDashboard/src/services/api/ContactsApi.ts - MODIFICAR
async getContacts(
  filters: ContactFilters,
  page: number = 1,
  pageSize: number = 50
): Promise<ApiResponse<PaginatedResponse<Contact>>> {
  const params = new URLSearchParams();
  params.append('page', page.toString());
  params.append('page_size', pageSize.toString());

  // Map filters to backend parameters
  if (filters.searchQuery) params.append('search_query', filters.searchQuery);
  if (filters.state) params.append('state', filters.state);
  if (filters.municipality) params.append('municipality', filters.municipality);
  if (filters.lada) params.append('lada', filters.lada);
  if (filters.dateRange?.start) params.append('date_start', filters.dateRange.start);
  if (filters.dateRange?.end) params.append('date_end', filters.dateRange.end);

  return apiClient.get(`/contacts?${params}`);
}

async getStats(): Promise<ApiResponse<ContactStatsEnhanced>> {
  return apiClient.get('/contacts/stats');
}
```

#### ✅ **BLOQUE 6: Testing de Integración (1.5 horas)**

**Tarea 6.1: Probar conexión dashboard ↔ backend**

- [ ] Verificar que dashboard carga datos reales de PostgreSQL
- [ ] Probar filtros con datos reales
- [ ] Verificar paginación con 31.8M contactos
- [ ] Confirmar que métricas reflejan datos reales
- [ ] Testing de performance con volumen real

**Tarea 6.2: Optimizar queries para performance**

```python
# app/api/v1/endpoints/contacts.py - OPTIMIZAR
# Agregar índices específicos para dashboard
# Optimizar queries para evitar timeouts
# Implementar caching en Redis para stats
```

#### ✅ **BLOQUE 7: Configuración de Producción (30 min)**

**Tarea 7.1: Variables de entorno**

```bash
# .env - AGREGAR
# Dashboard Configuration
DASHBOARD_ENABLED=true
DASHBOARD_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# API Configuration
API_V1_PREFIX=/api/v1
API_PAGINATION_MAX_SIZE=1000
API_CACHE_TTL=300

# Performance
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
REDIS_CACHE_DEFAULT_TTL=3600
```

---

## 📅 DÍA 2: OPTIMIZACIÓN Y TESTING

### 🌅 **MAÑANA (4 horas): Performance y Caching**

#### ✅ **BLOQUE 8: Implementar Caching (1.5 horas)**

**Tarea 8.1: Cache de estadísticas**

```python
# app/core/cache.py - NUEVO ARCHIVO
import redis.asyncio as redis
from typing import Optional, Any
import json
from datetime import timedelta

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def get_cached_stats(self) -> Optional[dict]:
        """Get cached contact stats"""
        cached = await self.redis.get("contacts:stats")
        if cached:
            return json.loads(cached)
        return None

    async def cache_stats(self, stats: dict, ttl: int = 300):
        """Cache contact stats for 5 minutes"""
        await self.redis.setex(
            "contacts:stats",
            ttl,
            json.dumps(stats, default=str)
        )

    async def invalidate_stats_cache(self):
        """Invalidate stats cache when data changes"""
        await self.redis.delete("contacts:stats")
```

**Tarea 8.2: Integrar cache en endpoints**

```python
# app/api/v1/endpoints/contacts.py - MODIFICAR get_contacts_stats_enhanced
async def get_contacts_stats_enhanced(
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache_manager),
    current_user: str = Depends(get_current_user)
):
    # Try cache first
    cached_stats = await cache.get_cached_stats()
    if cached_stats:
        return ContactStatsEnhanced(**cached_stats)

    # Calculate stats (existing code)
    # ...

    # Cache results
    stats_dict = stats.dict()
    await cache.cache_stats(stats_dict)

    return stats
```

#### ✅ **BLOQUE 9: Optimización de Queries (1.5 horas)**

**Tarea 9.1: Índices específicos para dashboard**

```sql
-- migrations/versions/002_dashboard_optimization.py
-- Índices optimizados para el dashboard

-- Para filtros del dashboard
CREATE INDEX CONCURRENTLY idx_contacts_dashboard_filters
ON contacts(state_name, municipality, lada, created_at)
WHERE opt_out_at IS NULL;

-- Para búsquedas de texto
CREATE INDEX CONCURRENTLY idx_contacts_search_text
ON contacts USING gin((
    setweight(to_tsvector('spanish', COALESCE(full_name, '')), 'A') ||
    setweight(to_tsvector('simple', COALESCE(phone_national, '')), 'B')
));

-- Para estadísticas rápidas
CREATE INDEX CONCURRENTLY idx_contacts_stats_state
ON contacts(state_name)
WHERE state_name IS NOT NULL AND opt_out_at IS NULL;

CREATE INDEX CONCURRENTLY idx_contacts_stats_lada
ON contacts(lada)
WHERE lada IS NOT NULL AND opt_out_at IS NULL;
```

**Tarea 9.2: Query optimization**

```python
# app/api/v1/endpoints/contacts.py - OPTIMIZAR
# Usar EXPLAIN ANALYZE para optimizar queries lentas
# Implementar query hints para PostgreSQL
# Configurar connection pooling específico para dashboard
```

#### ✅ **BLOQUE 10: Sistema de Extracciones API (1 hora)**

**Tarea 10.1: Endpoint de extracciones**

```python
# app/api/v1/endpoints/extractions.py - NUEVO ARCHIVO
from fastapi import APIRouter, Depends, BackgroundTasks
from app.services.extraction_service import ExtractionService

router = APIRouter()

@router.post("/", response_model=ExtractionResponse)
async def create_extraction(
    request: ExtractionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create new extraction job"""

    extraction_service = ExtractionService(db)

    # Validate request
    validation_result = await extraction_service.validate_request(request)
    if not validation_result.is_valid:
        raise HTTPException(400, detail=validation_result.errors)

    # Create extraction job
    job = await extraction_service.create_job(request, created_by=current_user)

    # Start background processing
    background_tasks.add_task(
        extraction_service.process_extraction,
        job.id
    )

    return ExtractionResponse(
        id=job.id,
        status="pending",
        estimated_duration=job.estimated_duration_minutes,
        created_at=job.created_at
    )

@router.get("/", response_model=List[ExtractionResponse])
async def get_extractions(
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get user's extraction history"""
    # Implementation for extraction history
    pass
```

### 🌆 **TARDE (4 horas): Testing y Validación**

#### ✅ **BLOQUE 11: Testing Completo (2 horas)**

**Tarea 11.1: Testing de endpoints**

```python
# tests/api/test_contacts_integration.py - NUEVO
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_get_contacts_paginated():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/contacts?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert len(data["data"]) <= 10

@pytest.mark.asyncio
async def test_get_stats_enhanced():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/contacts/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_contacts" in data
        assert "contacts_by_state" in data
        assert "contacts_by_lada" in data

@pytest.mark.asyncio
async def test_dashboard_filters():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Test state filter
        response = await ac.get("/api/v1/contacts?state=SINALOA")
        assert response.status_code == 200

        # Test LADA filter
        response = await ac.get("/api/v1/contacts?lada=667")
        assert response.status_code == 200

        # Test search
        response = await ac.get("/api/v1/contacts?search_query=667")
        assert response.status_code == 200
```

**Tarea 11.2: Testing de integración dashboard**

```typescript
// WebDashboard/src/test/integration/DashboardIntegration.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import { Provider } from "react-redux";
import { store } from "../../store";
import { DashboardPage } from "../../pages/Dashboard/DashboardPage";

describe("Dashboard Integration", () => {
  it("loads real data from backend", async () => {
    render(
      <Provider store={store}>
        <DashboardPage />
      </Provider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Total Contacts/)).toBeInTheDocument();
    });

    // Verify real data is loaded (not mock)
    const totalContacts = screen.getByText(/31,/); // Should show real count
    expect(totalContacts).toBeInTheDocument();
  });
});
```

#### ✅ **BLOQUE 12: Optimización Final (2 horas)**

**Tarea 12.1: Performance monitoring**

```python
# app/middleware/performance.py - NUEVO
from fastapi import Request, Response
import time
import logging

async def performance_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Log slow queries (> 2 seconds)
    if process_time > 2.0:
        logging.warning(f"Slow query: {request.url} took {process_time:.2f}s")

    return response
```

**Tarea 12.2: Health checks específicos**

```python
# app/api/v1/endpoints/health.py - EXPANDIR
@router.get("/dashboard")
async def dashboard_health_check(db: AsyncSession = Depends(get_db)):
    """Health check específico para dashboard"""
    try:
        # Test database connection
        result = await db.execute(text("SELECT 1"))
        db_healthy = result.scalar() == 1

        # Test contacts table
        contacts_count = await db.execute(text("SELECT COUNT(*) FROM contacts LIMIT 1"))
        contacts_accessible = contacts_count.scalar() > 0

        # Test Redis connection (if available)
        redis_healthy = True  # Implement Redis check

        return {
            "status": "healthy" if all([db_healthy, contacts_accessible, redis_healthy]) else "unhealthy",
            "database": "ok" if db_healthy else "error",
            "contacts_table": "ok" if contacts_accessible else "error",
            "redis": "ok" if redis_healthy else "error",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }
```

---

## 🎯 CRITERIOS DE ACEPTACIÓN

### **✅ Al Final del Día 1:**

- [ ] Endpoints de contactos paginados funcionando
- [ ] Estadísticas mejoradas para dashboard
- [ ] Endpoints de ubicaciones (estados, municipios, LADAs)
- [ ] CORS configurado para desarrollo
- [ ] Backend respondiendo sin errores

### **✅ Al Final del Día 2:**

- [ ] Dashboard conectado con datos reales de PostgreSQL
- [ ] Filtros funcionando con 31.8M contactos
- [ ] Paginación optimizada para gran volumen
- [ ] Caching implementado para performance
- [ ] Testing de integración pasando
- [ ] Performance < 2 segundos para queries típicas

---

## 🚨 TROUBLESHOOTING

### **Problema: Queries lentas con 31.8M contactos**

- **Solución:** Implementar índices específicos y LIMIT queries
- **Comando:** `EXPLAIN ANALYZE` para identificar cuellos de botella
- **Optimización:** Usar pagination server-side siempre

### **Problema: CORS errors en desarrollo**

- **Solución:** Verificar configuración de CORS en FastAPI
- **Verificar:** URL del frontend en allow_origins
- **Debug:** Browser DevTools Network tab

### **Problema: Dashboard no carga datos**

- **Solución:** Verificar que backend está corriendo en puerto 8000
- **Verificar:** `/api/v1/health` responde correctamente
- **Debug:** Redux DevTools para ver API calls

---

## 📊 MÉTRICAS DE PROGRESO

- **Backend API Expansion:** 40% del total
- **Dashboard Integration:** 35% del total
- **Performance Optimization:** 15% del total
- **Testing & Validation:** 10% del total

**Total Fase 1:** 100% → **Preparado para Fase 2**

---

## 🚀 RESULTADO ESPERADO

### **Al Completar Fase 1:**

- ✅ **Dashboard funcional** con datos reales de 31.8M contactos
- ✅ **API REST expandida** con endpoints optimizados
- ✅ **Performance escalable** para gran volumen
- ✅ **Caching inteligente** para responsividad
- ✅ **Testing robusto** para estabilidad
- ✅ **Base sólida** para validadores multi-plataforma

### **🎉 Valor Inmediato:**

- **Interface moderna** reemplaza bot básico para visualización
- **Datos reales** desde día 1
- **Performance optimizada** para 31.8M contactos
- **Base preparada** para expansión multi-plataforma

**→ Continuar con [Fase 2: Expansión de Base de Datos](./fase2-expansion-database.md)**

---

_Fase 1: Integración del Web Dashboard_
_SMS Marketing Platform v2.0 - Migración Sistema Actual_
_Implementación Detallada_
