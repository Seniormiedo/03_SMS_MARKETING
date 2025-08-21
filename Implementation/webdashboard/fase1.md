# 📋 FASE 1: SETUP Y ARQUITECTURA (Días 1-2)

## SMS Marketing Platform v2.0 - Web Dashboard

---

## 🎯 OBJETIVO DE LA FASE

Establecer la base sólida del proyecto React con TypeScript, configurar todas las herramientas de desarrollo y crear la estructura arquitectónica del dashboard.

**Duración:** 2 días
**Complejidad:** MEDIA
**Prioridad:** CRÍTICA

---

## 📅 DÍA 1: SETUP DEL PROYECTO

### 🌅 **MAÑANA (4 horas): Inicialización y Setup**

#### ✅ **BLOQUE 1: Creación del Proyecto (1 hora)**

- [ ] **1.1** Crear branch de trabajo

  ```bash
  git checkout -b feature/web-dashboard
  ```

- [ ] **1.2** Crear proyecto React con Vite

  ```bash
  npm create vite@latest WebDashboard -- --template react-ts
  cd WebDashboard
  ```

- [ ] **1.3** Verificar estructura inicial generada
  - [ ] Confirmar archivos base: `src/`, `public/`, `package.json`
  - [ ] Validar TypeScript configurado correctamente
  - [ ] Probar comando `npm run dev` funciona

#### ✅ **BLOQUE 2: Instalación de Dependencias (1.5 horas)**

- [ ] **2.1** Instalar dependencias principales

  ```bash
  npm install @reduxjs/toolkit react-redux react-router-dom
  npm install @headlessui/react @heroicons/react
  npm install chart.js react-chartjs-2
  npm install date-fns clsx tailwind-merge
  npm install react-hook-form @hookform/resolvers yup
  npm install axios react-query
  npm install react-hot-toast react-loading-skeleton
  ```

- [ ] **2.2** Instalar dependencias de desarrollo

  ```bash
  npm install -D tailwindcss postcss autoprefixer
  npm install -D @types/node @vitejs/plugin-react
  npm install -D eslint @typescript-eslint/eslint-plugin
  npm install -D prettier eslint-config-prettier
  ```

- [ ] **2.3** Configurar Tailwind CSS

  ```bash
  npx tailwindcss init -p
  ```

- [ ] **2.4** Verificar todas las instalaciones
  - [ ] Revisar `package.json` para dependencias correctas
  - [ ] Confirmar que no hay conflictos de versiones
  - [ ] Ejecutar `npm audit` para verificar seguridad

#### ✅ **BLOQUE 3: Estructura de Directorios (1 hora)**

- [ ] **3.1** Crear estructura completa de carpetas

  ```
  src/
  ├── components/
  │   ├── common/
  │   ├── contacts/
  │   ├── campaigns/
  │   ├── validation/
  │   └── analytics/
  ├── pages/
  │   ├── Dashboard/
  │   ├── Contacts/
  │   ├── Campaigns/
  │   ├── Validation/
  │   └── Analytics/
  ├── services/
  │   ├── api/
  │   └── utils/
  ├── hooks/
  ├── store/
  │   ├── slices/
  │   └── middleware/
  ├── types/
  ├── utils/
  └── styles/
  ```

- [ ] **3.2** Crear archivos README.md en cada carpeta principal
  - [ ] Documentar propósito de cada directorio
  - [ ] Incluir ejemplos de uso esperado
  - [ ] Definir convenciones de nomenclatura

#### ✅ **BLOQUE 4: Configuración Git y Calidad (30 min)**

- [ ] **4.1** Configurar `.gitignore` apropiado

  - [ ] Agregar `node_modules/`, `dist/`, `.env*`
  - [ ] Incluir archivos específicos de IDE
  - [ ] Agregar logs y archivos temporales

- [ ] **4.2** Configurar scripts de calidad en `package.json`
  ```json
  {
    "scripts": {
      "lint": "eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
      "lint:fix": "eslint src --ext ts,tsx --fix",
      "format": "prettier --write src/**/*.{ts,tsx}",
      "type-check": "tsc --noEmit"
    }
  }
  ```

### 🌆 **TARDE (4 horas): Configuración Base**

#### ✅ **BLOQUE 5: Configuración Vite (1 hora)**

- [ ] **5.1** Crear `vite.config.ts` completo

  - [ ] Configurar aliases de importación (@, @/components, etc.)
  - [ ] Configurar proxy para API backend (puerto 8000)
  - [ ] Configurar optimizaciones de build
  - [ ] Configurar code splitting con `manualChunks`

- [ ] **5.2** Probar configuración
  - [ ] Verificar que aliases funcionan
  - [ ] Confirmar que proxy está configurado
  - [ ] Testear build de producción

#### ✅ **BLOQUE 6: Configuración Tailwind (1 hora)**

- [ ] **6.1** Configurar `tailwind.config.js` personalizado

  - [ ] Definir paleta de colores del proyecto
  - [ ] Configurar tipografía (Inter font)
  - [ ] Agregar animaciones personalizadas
  - [ ] Configurar plugins (@tailwindcss/forms, @tailwindcss/typography)

- [ ] **6.2** Crear archivos CSS base

  - [ ] `src/styles/globals.css` con imports de Tailwind
  - [ ] `src/styles/components.css` para componentes custom
  - [ ] `src/styles/themes.css` para temas y variables

- [ ] **6.3** Probar Tailwind
  - [ ] Crear componente de prueba con clases Tailwind
  - [ ] Verificar que responsive design funciona
  - [ ] Confirmar que colores personalizados están disponibles

#### ✅ **BLOQUE 7: Configuración TypeScript (1 hora)**

- [ ] **7.1** Configurar `tsconfig.json` estricto

  - [ ] Habilitar `strict: true`
  - [ ] Configurar `noUncheckedIndexedAccess`
  - [ ] Agregar `exactOptionalPropertyTypes`
  - [ ] Configurar paths para aliases

- [ ] **7.2** Crear tipos base del proyecto

  - [ ] `src/types/index.ts` con exports principales
  - [ ] `src/types/api.ts` para respuestas de API
  - [ ] `src/types/common.ts` para tipos compartidos

- [ ] **7.3** Configurar ESLint y Prettier
  - [ ] Crear `.eslintrc.json` con reglas TypeScript estrictas
  - [ ] Crear `.prettierrc` con formato consistente
  - [ ] Probar que linting funciona sin errores

#### ✅ **BLOQUE 8: Setup Inicial de Routing (1 hora)**

- [ ] **8.1** Configurar React Router básico

  - [ ] Crear `src/App.tsx` con router setup
  - [ ] Definir rutas principales: `/`, `/contacts`, `/campaigns`, etc.
  - [ ] Crear componentes placeholder para cada ruta

- [ ] **8.2** Crear layout base

  - [ ] Componente `Layout` con estructura básica
  - [ ] Placeholder para Header y Sidebar
  - [ ] Configurar área de contenido principal

- [ ] **8.3** Probar navegación
  - [ ] Verificar que todas las rutas cargan
  - [ ] Confirmar que navegación funciona
  - [ ] Testear que no hay errores en consola

---

## 📅 DÍA 2: COMPONENTES BASE Y STORE

### 🌅 **MAÑANA (4 horas): Redux Store y Types**

#### ✅ **BLOQUE 9: Configuración Redux (1.5 horas)**

- [ ] **9.1** Configurar Redux Toolkit store

  - [ ] Crear `src/store/index.ts` con configuración base
  - [ ] Configurar middleware personalizado si necesario
  - [ ] Configurar DevTools para desarrollo

- [ ] **9.2** Crear tipos principales del dominio

  - [ ] `src/types/Contact.ts` con interfaces completas
  - [ ] `src/types/Campaign.ts` para futuras funcionalidades
  - [ ] `src/types/Validation.ts` preparado para multi-plataforma
  - [ ] `src/types/Api.ts` para requests/responses

- [ ] **9.3** Configurar hooks de Redux
  - [ ] `src/hooks/redux.ts` con `useAppDispatch` y `useAppSelector`
  - [ ] Configurar tipos correctos para TypeScript
  - [ ] Probar que hooks funcionan sin errores

#### ✅ **BLOQUE 10: Slice de Contactos (2 horas)**

- [ ] **10.1** Crear `contactsSlice.ts` completo

  - [ ] Definir `ContactsState` interface
  - [ ] Configurar `initialState` con valores por defecto
  - [ ] Implementar reducers síncronos: `setFilters`, `clearFilters`, etc.

- [ ] **10.2** Implementar async thunks

  - [ ] `fetchContacts` con filtros y paginación
  - [ ] `fetchContactStats` para métricas del dashboard
  - [ ] `createExtraction` para generar archivos
  - [ ] `fetchExtractions` para historial

- [ ] **10.3** Configurar extraReducers

  - [ ] Manejar estados pending/fulfilled/rejected
  - [ ] Actualizar loading states correctamente
  - [ ] Gestionar errores de forma consistente

- [ ] **10.4** Probar slice completo
  - [ ] Crear tests unitarios básicos
  - [ ] Verificar que actions se dispatch correctamente
  - [ ] Confirmar que state se actualiza como esperado

#### ✅ **BLOQUE 11: API Services (30 min)**

- [ ] **11.1** Crear cliente API base

  - [ ] `src/services/api/ApiClient.ts` con configuración Axios
  - [ ] Configurar interceptors para headers y errores
  - [ ] Configurar base URL y timeouts

- [ ] **11.2** Crear service específico de contactos
  - [ ] `src/services/api/ContactsApi.ts` con métodos CRUD
  - [ ] Implementar métodos para filtros y paginación
  - [ ] Agregar métodos para extracciones

### 🌆 **TARDE (4 horas): Componentes Base**

#### ✅ **BLOQUE 12: Componentes Layout (2 horas)**

- [ ] **12.1** Crear componente Header

  - [ ] `src/components/common/Header.tsx` funcional
  - [ ] Mostrar título del dashboard y contador de contactos
  - [ ] Agregar botones de notificaciones y configuración
  - [ ] Implementar área de usuario con placeholder

- [ ] **12.2** Crear componente Sidebar

  - [ ] `src/components/common/Sidebar.tsx` con navegación
  - [ ] Configurar items de menú con iconos de Heroicons
  - [ ] Implementar estado activo con React Router
  - [ ] Agregar logo y branding del proyecto

- [ ] **12.3** Integrar Layout completo
  - [ ] Combinar Header y Sidebar en Layout principal
  - [ ] Configurar responsive design para mobile
  - [ ] Probar navegación entre todas las páginas
  - [ ] Verificar que layout se ve profesional

#### ✅ **BLOQUE 13: Componentes Utilitarios (1 hora)**

- [ ] **13.1** Crear LoadingSpinner

  - [ ] `src/components/common/LoadingSpinner.tsx`
  - [ ] Configurar diferentes tamaños (sm, md, lg)
  - [ ] Implementar con animaciones Tailwind
  - [ ] Probar en diferentes contextos

- [ ] **13.2** Crear ErrorBoundary

  - [ ] `src/components/common/ErrorBoundary.tsx`
  - [ ] Manejar errores de React gracefully
  - [ ] Mostrar UI amigable para errores
  - [ ] Configurar logging de errores

- [ ] **13.3** Crear componente Toast
  - [ ] Configurar react-hot-toast
  - [ ] Personalizar estilos para el proyecto
  - [ ] Probar notificaciones success/error/info

#### ✅ **BLOQUE 14: Hooks Personalizados (1 hora)**

- [ ] **14.1** Crear hooks de negocio

  - [ ] `src/hooks/useContacts.ts` para lógica de contactos
  - [ ] `src/hooks/useFilters.ts` para manejo de filtros
  - [ ] `src/hooks/usePagination.ts` para paginación

- [ ] **14.2** Crear hooks utilitarios

  - [ ] `src/hooks/useDebounce.ts` para search inputs
  - [ ] `src/hooks/useLocalStorage.ts` para persistencia
  - [ ] `src/hooks/useAsync.ts` para operaciones asíncronas

- [ ] **14.3** Probar hooks
  - [ ] Crear componentes de prueba para cada hook
  - [ ] Verificar que funcionan correctamente
  - [ ] Documentar uso y parámetros

---

## 🎯 CRITERIOS DE ACEPTACIÓN

### **✅ Al Final del Día 1:**

- [ ] Proyecto React + TypeScript funcionando
- [ ] Todas las dependencias instaladas correctamente
- [ ] Estructura de carpetas completa
- [ ] Configuraciones base (Vite, Tailwind, TypeScript) funcionando
- [ ] Routing básico operativo
- [ ] Sin errores en consola del navegador

### **✅ Al Final del Día 2:**

- [ ] Redux store configurado y funcionando
- [ ] Tipos TypeScript completos y sin errores
- [ ] Slice de contactos implementado con async thunks
- [ ] API client configurado
- [ ] Header y Sidebar funcionales y responsive
- [ ] Componentes utilitarios (Loading, Error, Toast) operativos
- [ ] Hooks personalizados creados y probados
- [ ] Navegación entre páginas sin errores

---

## 🚨 TROUBLESHOOTING COMÚN

### **Problema: Errores de TypeScript**

- **Solución:** Verificar `tsconfig.json` y tipos importados
- **Comando:** `npm run type-check` para diagnóstico

### **Problema: Tailwind no aplica estilos**

- **Solución:** Verificar import en `globals.css` y configuración
- **Comando:** Inspeccionar elemento para ver clases aplicadas

### **Problema: Redux no actualiza componentes**

- **Solución:** Verificar que componente está wrapeado con Provider
- **Verificar:** Hooks `useAppSelector` están importados correctamente

### **Problema: Routing no funciona**

- **Solución:** Verificar que `BrowserRouter` está configurado
- **Verificar:** Rutas están definidas correctamente en `App.tsx`

---

## 📊 MÉTRICAS DE PROGRESO

- **Setup del Proyecto:** 25% del total
- **Configuraciones:** 25% del total
- **Estructura de Datos:** 25% del total
- **Componentes Base:** 25% del total

**Total Fase 1:** 100% → **Preparado para Fase 2**

---

## 🚀 SIGUIENTE PASO

Una vez completada esta fase, tendrás:

- ✅ Base sólida del proyecto configurada
- ✅ Redux store operativo con tipos
- ✅ Layout profesional funcionando
- ✅ Componentes base listos para usar

**→ Continuar con [Fase 2: Dashboard Principal](./fase2.md)**

---

_TODO List - Fase 1: Setup y Arquitectura_
_SMS Marketing Platform v2.0 - Web Dashboard_
_Implementación Detallada_
