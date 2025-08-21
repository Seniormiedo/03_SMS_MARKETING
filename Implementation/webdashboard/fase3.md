# 📋 FASE 3: GESTIÓN DE CONTACTOS Y EXTRACCIONES (Días 5-6)

## SMS Marketing Platform v2.0 - Web Dashboard

---

## 🎯 OBJETIVO DE LA FASE

Desarrollar la funcionalidad completa de gestión de contactos con filtros avanzados, sistema de extracciones profesional y experiencia de usuario optimizada.

**Duración:** 2 días
**Complejidad:** ALTA
**Prioridad:** CRÍTICA

---

## 📅 DÍA 5: PÁGINA DE CONTACTOS Y FILTROS

### 🌅 **MAÑANA (4 horas): Estructura de la Página de Contactos**

#### ✅ **BLOQUE 1: Componente ContactsPage Principal (1.5 horas)**

- [ ] **1.1** Crear estructura de ContactsPage

  - [ ] `src/pages/Contacts/ContactsPage.tsx` completo
  - [ ] Header con título, descripción y botón "New Extraction"
  - [ ] Layout responsive con áreas definidas
  - [ ] Integración con Redux para estado de contactos

- [ ] **1.2** Configurar estado y efectos

  - [ ] `useAppSelector` para obtener contactos, filtros, paginación
  - [ ] `useAppDispatch` para acciones de contactos
  - [ ] `useEffect` para cargar datos inicial y cambios de filtros
  - [ ] Estado local para modal de extracción

- [ ] **1.3** Implementar handlers de eventos
  - [ ] `handleFiltersChange` para actualizar filtros
  - [ ] `handlePageChange` para navegación de páginas
  - [ ] `handleExtractionModal` para mostrar/ocultar modal
  - [ ] `handleRefresh` para recargar datos

#### ✅ **BLOQUE 2: Componente ContactStats (1 hora)**

- [ ] **2.1** Crear ContactStats

  - [ ] `src/components/contacts/ContactStats.tsx`
  - [ ] Métricas rápidas: Total, Por Estado, Por LADA
  - [ ] Cards pequeñas con iconos y números
  - [ ] Colores diferenciados para cada métrica

- [ ] **2.2** Implementar cálculos dinámicos

  - [ ] Contar contactos totales
  - [ ] Calcular distribución por estado
  - [ ] Mostrar LADAs más frecuentes
  - [ ] Porcentajes y tendencias

- [ ] **2.3** Agregar interactividad
  - [ ] Click en stats para aplicar filtros automáticamente
  - [ ] Hover effects con tooltips informativos
  - [ ] Animaciones para cambios de números
  - [ ] Loading skeletons durante carga

#### ✅ **BLOQUE 3: Sistema de Filtros Base (1.5 horas)**

- [ ] **3.1** Crear ContactFilters estructura

  - [ ] `src/components/contacts/ContactFilters.tsx`
  - [ ] Panel colapsable con filtros avanzados
  - [ ] React Hook Form para manejo de formulario
  - [ ] Validación con Yup schema

- [ ] **3.2** Implementar campos de filtro

  - [ ] **Search Query:** Input con búsqueda por número
  - [ ] **State:** Dropdown con estados disponibles
  - [ ] **Municipality:** Dropdown dependiente del estado
  - [ ] **LADA:** Input numérico con validación
  - [ ] **Date Range:** Date pickers para rango de fechas

- [ ] **3.3** Configurar funcionalidad
  - [ ] Botón "Apply Filters" que actualiza Redux
  - [ ] Botón "Clear All" que resetea filtros
  - [ ] Auto-submit con debounce en search query
  - [ ] Indicadores visuales de filtros activos

### 🌆 **TARDE (4 horas): Lista de Contactos y Paginación**

#### ✅ **BLOQUE 4: Componente ContactList (2 horas)**

- [ ] **4.1** Crear estructura de ContactList

  - [ ] `src/components/contacts/ContactList.tsx`
  - [ ] Tabla responsive con headers fijos
  - [ ] Columnas: Phone, State, Municipality, LADA, Created
  - [ ] Loading states y empty states

- [ ] **4.2** Implementar formateo de datos

  - [ ] Formateo de números telefónicos
  - [ ] Formateo de fechas con date-fns
  - [ ] Truncado de texto largo
  - [ ] Indicadores de estado (nuevo, validado, etc.)

- [ ] **4.3** Agregar funcionalidades avanzadas
  - [ ] Sorting por columnas (click en headers)
  - [ ] Selection multiple con checkboxes
  - [ ] Actions en hover (view, edit, delete)
  - [ ] Context menu con opciones rápidas

#### ✅ **BLOQUE 5: Componente ContactCard (1 hora)**

- [ ] **5.1** Crear ContactCard para vista mobile

  - [ ] `src/components/contacts/ContactCard.tsx`
  - [ ] Layout de card optimizado para touch
  - [ ] Información principal visible
  - [ ] Botones de acción accesibles

- [ ] **5.2** Implementar responsive behavior
  - [ ] Mostrar tabla en desktop
  - [ ] Mostrar cards en mobile/tablet
  - [ ] Transiciones suaves entre vistas
  - [ ] Mantener funcionalidad en ambas vistas

#### ✅ **BLOQUE 6: Sistema de Paginación (1 hora)**

- [ ] **6.1** Crear componente Pagination

  - [ ] `src/components/common/Pagination.tsx`
  - [ ] Controles: First, Previous, Numbers, Next, Last
  - [ ] Información: "Showing X to Y of Z results"
  - [ ] Selector de items per page

- [ ] **6.2** Integrar con ContactList

  - [ ] Conectar con Redux pagination state
  - [ ] Manejar cambios de página
  - [ ] Preservar filtros al cambiar página
  - [ ] Loading states durante navegación

- [ ] **6.3** Optimizar UX
  - [ ] Disabled states para botones no disponibles
  - [ ] Keyboard navigation (arrow keys)
  - [ ] URL sync para deep linking
  - [ ] Smooth scrolling al cambiar página

---

## 📅 DÍA 6: SISTEMA DE EXTRACCIONES

### 🌅 **MAÑANA (4 horas): Formulario de Extracción**

#### ✅ **BLOQUE 7: Modal Base de Extracción (1 hora)**

- [ ] **7.1** Crear estructura de ExtractionForm

  - [ ] `src/components/contacts/ExtractionForm.tsx`
  - [ ] Modal overlay con backdrop
  - [ ] Header con título y botón close
  - [ ] Footer con botones de acción

- [ ] **7.2** Configurar comportamiento del modal

  - [ ] Abrir/cerrar con animaciones
  - [ ] Click outside para cerrar
  - [ ] Escape key para cerrar
  - [ ] Focus management para accessibility

- [ ] **7.3** Integrar con página principal
  - [ ] Trigger desde botón "New Extraction"
  - [ ] Estado local para controlar visibilidad
  - [ ] Callbacks para success/error
  - [ ] Cleanup al cerrar

#### ✅ **BLOQUE 8: Formulario de Extracción Avanzado (2 horas)**

- [ ] **8.1** Implementar campos del formulario

  - [ ] **Extraction Type:** Radio buttons (State, Municipality, LADA)
  - [ ] **Value:** Input dinámico según tipo seleccionado
  - [ ] **Amount:** Number input con validación (1-100,000)
  - [ ] **Format:** Radio buttons (XLSX, TXT)
  - [ ] **Include Validation:** Checkbox con explicación

- [ ] **8.2** Configurar validación con Yup

  - [ ] Schema de validación completo
  - [ ] Mensajes de error personalizados
  - [ ] Validación en tiempo real
  - [ ] Indicadores visuales de campos válidos/inválidos

- [ ] **8.3** Implementar lógica dinámica
  - [ ] Placeholder dinámico según tipo seleccionado
  - [ ] Autocomplete para valores comunes
  - [ ] Estimación de tiempo de procesamiento
  - [ ] Preview de resultados esperados

#### ✅ **BLOQUE 9: Integración con Backend (1 hora)**

- [ ] **9.1** Configurar API call

  - [ ] `createExtraction` async thunk
  - [ ] Manejo de estados loading/success/error
  - [ ] Progress tracking para extracciones grandes
  - [ ] Timeout handling para requests largos

- [ ] **9.2** Implementar feedback al usuario

  - [ ] Loading spinner durante procesamiento
  - [ ] Success toast con información de la extracción
  - [ ] Error handling con mensajes específicos
  - [ ] Botón disabled durante procesamiento

- [ ] **9.3** Configurar seguimiento
  - [ ] Agregar extracción a lista de historial
  - [ ] Actualizar métricas del dashboard
  - [ ] Notificación cuando extracción completa
  - [ ] Link para descargar resultado

### 🌆 **TARDE (4 horas): Historial y Gestión de Extracciones**

#### ✅ **BLOQUE 10: Lista de Extracciones (1.5 horas)**

- [ ] **10.1** Crear componente ExtractionList

  - [ ] `src/components/contacts/ExtractionList.tsx`
  - [ ] Tabla con historial de extracciones
  - [ ] Columnas: Date, Type, Value, Amount, Status, Actions
  - [ ] Filtros por estado y fecha

- [ ] **10.2** Implementar estados de extracción

  - [ ] **Pending:** Waiting to start
  - [ ] **Processing:** In progress con progress bar
  - [ ] **Completed:** Success con download link
  - [ ] **Failed:** Error con retry option

- [ ] **10.3** Agregar funcionalidades
  - [ ] Download button para extracciones completadas
  - [ ] Retry button para extracciones fallidas
  - [ ] Delete button para limpiar historial
  - [ ] Auto-refresh cada 30 segundos

#### ✅ **BLOQUE 11: Gestión de Archivos (1 hora)**

- [ ] **11.1** Implementar download de archivos

  - [ ] `src/services/utils/FileDownloader.ts`
  - [ ] Manejo de diferentes formatos (XLSX, TXT)
  - [ ] Progress tracking para downloads grandes
  - [ ] Error handling para archivos no disponibles

- [ ] **11.2** Configurar preview de archivos
  - [ ] Preview modal para archivos pequeños
  - [ ] Información del archivo (size, rows, format)
  - [ ] Sample data preview
  - [ ] Metadata de la extracción

#### ✅ **BLOQUE 12: Optimizaciones UX (1.5 horas)**

- [ ] **12.1** Implementar búsqueda avanzada

  - [ ] Debounced search en lista de contactos
  - [ ] Highlight de términos buscados
  - [ ] Search suggestions
  - [ ] Recent searches history

- [ ] **12.2** Agregar bulk operations

  - [ ] Select all checkbox
  - [ ] Bulk export de contactos seleccionados
  - [ ] Bulk delete (con confirmación)
  - [ ] Bulk validation (preparado para futuro)

- [ ] **12.3** Mejorar responsive design
  - [ ] Mobile-optimized filters (drawer style)
  - [ ] Touch-friendly pagination
  - [ ] Swipe gestures en cards
  - [ ] Optimized modals para mobile

---

## 🎯 CRITERIOS DE ACEPTACIÓN

### **✅ Al Final del Día 5:**

- [ ] Página de contactos completamente funcional
- [ ] Sistema de filtros operativo
- [ ] Lista de contactos con paginación
- [ ] Responsive design funcionando
- [ ] Performance optimizada para listas grandes
- [ ] Loading states apropiados

### **✅ Al Final del Día 6:**

- [ ] Sistema de extracciones completamente funcional
- [ ] Modal de extracción con validación completa
- [ ] Historial de extracciones operativo
- [ ] Download de archivos funcionando
- [ ] Bulk operations implementadas
- [ ] UX optimizada para mobile

---

## 🚨 TROUBLESHOOTING COMÚN

### **Problema: Filtros no actualizan la lista**

- **Solución:** Verificar que `useEffect` escucha cambios en filtros
- **Debug:** Redux DevTools para ver si actions se disparan
- **Confirmar:** API endpoint acepta parámetros de filtro

### **Problema: Paginación pierde filtros**

- **Solución:** Incluir filtros en el state de paginación
- **Verificar:** URL params se actualizan correctamente
- **Mantener:** Filtros en localStorage para persistencia

### **Problema: Modal no se cierra correctamente**

- **Solución:** Verificar event handlers y state management
- **Cleanup:** useEffect cleanup para event listeners
- **Focus:** Restaurar focus al elemento que abrió el modal

### **Problema: Performance lenta con muchos contactos**

- **Solución:** Implementar virtualization para listas grandes
- **Optimizar:** Pagination server-side
- **Memoizar:** Componentes pesados con React.memo

---

## 📊 MÉTRICAS DE PROGRESO

- **Página de Contactos:** 35% del total
- **Sistema de Filtros:** 25% del total
- **Sistema de Extracciones:** 30% del total
- **UX y Optimizaciones:** 10% del total

**Total Fase 3:** 100% → **Preparado para Fase Final**

---

## 🔍 VALIDACIÓN DE CALIDAD

### **Funcionalidad Core:**

- [ ] Todos los filtros funcionan correctamente
- [ ] Paginación navega sin errores
- [ ] Extracciones se procesan exitosamente
- [ ] Downloads funcionan en todos los formatos
- [ ] Bulk operations operan correctamente

### **UX/UI Quality:**

- [ ] Loading states en todas las operaciones
- [ ] Error messages claros y accionables
- [ ] Responsive design en todos los breakpoints
- [ ] Accessibility compliant (keyboard, screen readers)
- [ ] Performance optimizada (< 3s para 1000+ contactos)

### **Data Integrity:**

- [ ] Filtros preservan integridad de datos
- [ ] Extracciones contienen datos correctos
- [ ] Paginación no duplica/omite registros
- [ ] Search results son precisos
- [ ] Bulk operations afectan registros correctos

---

## 🚀 SIGUIENTE PASO

Una vez completada esta fase, tendrás:

- ✅ Sistema completo de gestión de contactos
- ✅ Filtros avanzados funcionando
- ✅ Sistema profesional de extracciones
- ✅ UX optimizada para productividad
- ✅ Performance escalable

**→ Continuar con [Fase Final: Optimización y Deploy](./fase-final.md)**

---

_TODO List - Fase 3: Gestión de Contactos y Extracciones_
_SMS Marketing Platform v2.0 - Web Dashboard_
_Implementación Detallada_
