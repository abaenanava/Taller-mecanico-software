import { createApp } from 'vue'
import './style.css'

const API = 'http://localhost:8000/api'
const emptyClient = () => ({ workshop_id: '', full_name: '', alternate_contact_name: '', age: '', birth_date: '', personal_phone: '', work_phone: '', street: '', neighborhood: '', municipality: '', state: '', postal_code: '', personal_email: '', work_email: '', photo: null, _neighborhoods: [] })
const emptyWorkshop = () => ({ name: '', street: '', neighborhood: '', municipality: '', state: '', postal_code: '', business_name: '', phone: '', rfc: '', contact_email: '', photo: null, _neighborhoods: [] })

createApp({
  data: () => ({
    username: '', password: '', registerName: '', registerUsername: '', registerPassword: '', loading: false, error: '',
    user: null, authMode: 'login', activeView: 'dashboard', menuExpanded: true, menuPinned: true,
    clientForm: emptyClient(), clientErrors: {}, clientNotice: '', duplicateClient: null,
    clients: [], clientsLoading: false, selectedClient: null, editingClientId: null,
    clientPage: 1, clientPages: 1, clientTotal: 0, clientFilterWorkshop: '', clientFilterStatus: '', clientOrder: 'full_name', clientDirection: 'asc',
    workshops: [], workshopForm: emptyWorkshop(), workshopErrors: {}, workshopNotice: '', postalNotice: ''
  }),
  computed: {
    initials () { return this.user?.name?.split(' ').map(word => word[0]).join('').slice(0, 2) || 'MT' },
    canManageClients () { return ['ADMIN', 'RECEPCION'].includes(this.user?.role) },
    isAdmin () { return this.user?.role === 'ADMIN' },
    isEditingClient () { return this.editingClientId !== null },
    noticeClass () { return /exitosamente|verificada/i.test(this.clientNotice) ? 'success' : 'error' }
  },
  async mounted () {
    await fetch(`${API}/auth/csrf/`, { credentials: 'include' })
    const response = await fetch(`${API}/auth/me/`, { credentials: 'include' })
    if (response.ok) {
      this.user = (await response.json()).user
      if (this.canManageClients) await this.loadWorkshops()
    }
    if (window.matchMedia('(max-width: 760px)').matches) {
      this.menuExpanded = false
      this.menuPinned = false
    }
  },
  methods: {
    csrfToken () { return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '' },
    toggleMenu () { this.menuPinned = !this.menuPinned; this.menuExpanded = this.menuPinned },
    expandMenu () { this.menuExpanded = true },
    collapseMenu () { if (!this.menuPinned) this.menuExpanded = false },
    switchAuth (mode) { this.authMode = mode; this.error = '' },
    goHome () { this.activeView = 'dashboard'; this.clientNotice = ''; this.workshopNotice = '' },
    async signIn () {
      this.loading = true; this.error = ''
      try {
        const response = await fetch(`${API}/auth/login/`, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken() }, body: JSON.stringify({ username: this.username, password: this.password }) })
        const data = await response.json(); if (!response.ok) throw Error(data.detail)
        this.user = data.user; await this.loadWorkshops()
      } catch (error) { this.error = error.message || 'No fue posible iniciar sesión.' } finally { this.loading = false }
    },
    async register () {
      this.loading = true; this.error = ''
      try {
        const response = await fetch(`${API}/auth/register/`, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken() }, body: JSON.stringify({ first_name: this.registerName, username: this.registerUsername, password: this.registerPassword }) })
        const data = await response.json(); if (!response.ok) throw Error(data.detail)
        this.user = data.user
      } catch (error) { this.error = error.message || 'No fue posible crear la cuenta.' } finally { this.loading = false }
    },
    async signOut () {
      await fetch(`${API}/auth/logout/`, { method: 'POST', credentials: 'include', headers: { 'X-CSRFToken': this.csrfToken() } })
      this.user = null; this.activeView = 'dashboard'; this.clients = []
    },
    requireClientAccess () {
      if (this.canManageClients) return true
      this.clientNotice = 'Acceso no autorizado.'; this.activeView = 'dashboard'; return false
    },
    async loadWorkshops () {
      const response = await fetch(`${API}/talleres/`, { credentials: 'include' })
      if (response.ok) this.workshops = (await response.json()).workshops
    },
    async openRegister () {
      if (!this.requireClientAccess()) return
      await this.loadWorkshops(); this.clientForm = emptyClient(); this.clientErrors = {}; this.clientNotice = ''; this.postalNotice = ''; this.editingClientId = null; this.activeView = 'client-register'
    },
    async openClients (page = 1) {
      if (!this.requireClientAccess()) return
      this.clientPage = page; this.activeView = 'client-list'; await this.loadClients()
    },
    async loadClients () {
      this.clientsLoading = true
      try {
        const query = new URLSearchParams({ page: this.clientPage, order: this.clientOrder, direction: this.clientDirection })
        if (this.clientFilterWorkshop) query.set('workshop_id', this.clientFilterWorkshop)
        if (this.clientFilterStatus) query.set('status', this.clientFilterStatus)
        const response = await fetch(`${API}/clients/?${query}`, { credentials: 'include' })
        const data = await response.json()
        if (response.status === 401) { this.user = null; return }
        if (!response.ok) throw Error(data.detail)
        this.clients = data.clients; this.clientPages = data.pages; this.clientTotal = data.total
      } catch (error) { this.clientNotice = error.message } finally { this.clientsLoading = false }
    },
    async openClientDetail (client) {
      const response = await fetch(`${API}/clients/${client.id}/`, { credentials: 'include' })
      const data = await response.json()
      if (!response.ok) { this.clientNotice = data.detail; return }
      this.selectedClient = data.client; this.clientNotice = ''; this.activeView = 'client-detail'
    },
    async editClient () {
      this.clientForm = { ...this.selectedClient, photo: null, _neighborhoods: [] }
      this.editingClientId = this.selectedClient.id; this.clientErrors = {}; this.postalNotice = ''; this.activeView = 'client-register'
      await this.lookupPostal(this.clientForm)
    },
    selectPhoto (event) { this.clientForm.photo = event.target.files[0] || null },
    selectWorkshopPhoto (event) { this.workshopForm.photo = event.target.files[0] || null },
    async lookupPostal (form) {
      if (!/^\d{5}$/.test(form.postal_code)) return
      const response = await fetch(`${API}/codigos-postales/${form.postal_code}/`, { credentials: 'include' })
      const data = await response.json()
      if (!data.verified) { form._neighborhoods = []; this.postalNotice = 'CP no verificada: puedes capturar la dirección manualmente.'; return }
      form.state = data.data.state; form.municipality = data.data.municipality; form.neighborhood = data.data.neighborhoods[0]?.name || ''; form._neighborhoods = data.data.neighborhoods
      this.postalNotice = 'Dirección verificada por SEPOMEX.'
    },
    async saveClient () {
      this.clientErrors = {}; this.clientNotice = ''; this.duplicateClient = null
      const body = new FormData()
      Object.entries(this.clientForm).forEach(([key, value]) => { if (!['_neighborhoods', 'id', 'photo_url', 'created_at', 'status', 'workshop_name'].includes(key) && value !== null && value !== '') body.append(key, value) })
      const updating = this.isEditingClient
      const response = await fetch(updating ? `${API}/clients/${this.editingClientId}/` : `${API}/clients/register/`, { method: updating ? 'PUT' : 'POST', credentials: 'include', headers: { 'X-CSRFToken': this.csrfToken() }, body })
      const data = await response.json()
      if (response.status === 422) { this.clientErrors = data.fields || {}; this.clientNotice = 'Revisa los campos señalados antes de continuar.'; return }
      if (response.status === 409) { this.duplicateClient = data.client; this.clientNotice = data.detail; return }
      if (!response.ok) { this.clientNotice = data.detail; return }
      this.clientNotice = data.detail
      if (updating) { this.selectedClient = data.client; this.activeView = 'client-detail'; await this.loadClients() } else { this.clientForm = emptyClient() }
    },
    async changeClientStatus (action) {
      if (!this.isAdmin || !this.selectedClient) return
      const response = await fetch(`${API}/clients/${this.selectedClient.id}/${action}/`, { method: 'POST', credentials: 'include', headers: { 'X-CSRFToken': this.csrfToken() } })
      const data = await response.json(); this.clientNotice = data.detail
      if (response.ok) { this.selectedClient = data.client; await this.loadClients() }
    },
    async openWorkshopRegister () {
      if (!this.isAdmin) { this.clientNotice = 'Acceso no autorizado.'; return }
      this.workshopForm = emptyWorkshop(); this.workshopErrors = {}; this.workshopNotice = ''; this.postalNotice = ''; this.activeView = 'workshop-register'
    },
    async saveWorkshop () {
      this.workshopErrors = {}; this.workshopNotice = ''
      const body = new FormData()
      Object.entries(this.workshopForm).forEach(([key, value]) => { if (key !== '_neighborhoods' && value !== null && value !== '') body.append(key, value) })
      const response = await fetch(`${API}/talleres/`, { method: 'POST', credentials: 'include', headers: { 'X-CSRFToken': this.csrfToken() }, body })
      const data = await response.json()
      if (response.status === 422) { this.workshopErrors = data.fields || {}; this.workshopNotice = 'Revisa los campos señalados antes de continuar.'; return }
      this.workshopNotice = data.detail
      if (response.ok) { this.workshopForm = emptyWorkshop(); await this.loadWorkshops() }
    }
  },
  template: `
  <main v-if="!user" class="login-shell">
    <section class="login-brand"><div class="brand"><span class="mark">M</span><span>MOTORA</span></div><div class="hero-copy"><span class="eyebrow light">GESTIÓN DE TALLER</span><h1>Control simple.<br><em>Servicio extraordinario.</em></h1><p>Organiza clientes y talleres desde una experiencia clara, segura y profesional.</p><div class="trust-row"><span>◉ Acceso seguro</span><span>◈ Datos protegidos</span></div></div><div class="hero-orb orb-one"></div><div class="hero-orb orb-two"></div></section>
    <section class="login-panel"><div class="auth-card" v-if="authMode==='login'"><span class="section-kicker">ACCESO AL SISTEMA</span><h2>Bienvenido de nuevo</h2><p>Ingresa tus datos para continuar.</p><form @submit.prevent="signIn"><label>Usuario<input v-model="username" autocomplete="username" required placeholder="Escribe tu usuario"></label><label>Contraseña<input v-model="password" type="password" autocomplete="current-password" required placeholder="Tu contraseña"></label><p v-if="error" class="inline-error">{{ error }}</p><button class="button primary" :disabled="loading">{{ loading ? 'Verificando…' : 'Iniciar sesión' }} <span>→</span></button></form><div class="auth-divider"><span>o</span></div><button class="button ghost" @click="switchAuth('register')">Crear una cuenta</button></div><div class="auth-card" v-else><span class="section-kicker">NUEVO ACCESO</span><h2>Crea tu cuenta</h2><p>La cuenta creada inicia con permisos de consulta.</p><form @submit.prevent="register"><label>Nombre<input v-model="registerName" required placeholder="Tu nombre"></label><label>Usuario<input v-model="registerUsername" required placeholder="Elige un usuario"></label><label>Contraseña<input v-model="registerPassword" type="password" minlength="12" required placeholder="Mínimo 12 caracteres"></label><p v-if="error" class="inline-error">{{ error }}</p><button class="button primary" :disabled="loading">{{ loading ? 'Creando…' : 'Crear cuenta' }} <span>→</span></button></form><button class="text-button" @click="switchAuth('login')">← Volver a iniciar sesión</button></div></section>
  </main>
  <main v-else class="app-shell" :class="{collapsed: !menuExpanded}">
    <div class="mobile-backdrop" v-if="menuExpanded && !menuPinned" @click="toggleMenu"></div>
    <aside class="sidebar" @mouseenter="expandMenu" @mouseleave="collapseMenu"><div class="sidebar-head"><button class="menu-button" @click="toggleMenu" :title="menuExpanded ? 'Contraer menú' : 'Abrir menú'">☰</button><div class="brand sidebar-brand"><span class="mark">M</span><span class="brand-name">MOTORA</span></div></div><div class="sidebar-label">NAVEGACIÓN</div><nav><button class="nav-item" :class="{active: activeView==='dashboard'}" @click="goHome" title="Inicio"><span>⌂</span><b>Inicio</b></button><button v-if="canManageClients" class="nav-item" :class="{active: activeView==='client-register'}" @click="openRegister" title="Registrar cliente"><span>＋</span><b>Registrar cliente</b></button><button v-if="canManageClients" class="nav-item" :class="{active: activeView==='client-list'||activeView==='client-detail'}" @click="openClients()" title="Consultar clientes"><span>▦</span><b>Consultar clientes</b></button><button v-if="isAdmin" class="nav-item" :class="{active: activeView==='workshop-register'}" @click="openWorkshopRegister" title="Registrar taller"><span>⌘</span><b>Registrar taller</b></button></nav><div class="sidebar-footer"><div class="user-chip"><b>{{ initials }}</b><span><strong>{{ user.name }}</strong><small>{{ user.role }}</small></span></div><button class="logout-button" @click="signOut"><span>↪</span><b>Salir</b></button></div></aside>
    <section class="content-area"><header class="topbar"><div><span class="section-kicker">PANEL OPERATIVO</span><strong>{{ activeView==='dashboard' ? 'Centro de control' : activeView==='client-list' ? 'Directorio de clientes' : activeView==='workshop-register' ? 'Administración de talleres' : 'Gestión de clientes' }}</strong></div><div class="topbar-user"><span class="pulse"></span> Sesión activa</div></header>
      <section v-if="activeView==='dashboard'" class="page dashboard-page"><div class="welcome"><div><span class="section-kicker">BIENVENIDO</span><h1>Hola, {{ user.name }} <span>✦</span></h1><p>Administra la atención de tus clientes con rapidez y visibilidad.</p><div class="hero-actions"><button v-if="canManageClients" class="button primary" @click="openRegister">Registrar cliente <span>→</span></button><button v-if="canManageClients" class="button ghost dark" @click="openClients()">Ver clientes</button></div></div><div class="welcome-visual"><div class="dashboard-emblem">⚙</div><span>Todo bajo control</span></div></div><div class="metric-grid"><article><span class="metric-icon blue">◉</span><div><small>CLIENTES VISIBLES</small><strong>{{ clientTotal || '—' }}</strong><p>Consulta el directorio</p></div></article><article><span class="metric-icon violet">⌘</span><div><small>TALLERES</small><strong>{{ workshops.length }}</strong><p>Centros registrados</p></div></article><article><span class="metric-icon green">✓</span><div><small>PERMISOS</small><strong>{{ user.role }}</strong><p>Rol de sesión</p></div></article></div><div class="quick-panel"><div><span class="section-kicker">ACCESOS RÁPIDOS</span><h2>¿Qué deseas hacer?</h2></div><button v-if="canManageClients" @click="openRegister"><span>＋</span> Alta de cliente <i>→</i></button><button v-if="canManageClients" @click="openClients()"><span>▦</span> Consultar directorio <i>→</i></button><button v-if="isAdmin" @click="openWorkshopRegister"><span>⌘</span> Registrar taller <i>→</i></button></div><p v-if="clientNotice" class="alert" :class="noticeClass">{{ clientNotice }}</p></section>
      <section v-else-if="activeView==='workshop-register'" class="page"><div class="page-heading"><div><span class="section-kicker">ADMINISTRACIÓN</span><h1>Registrar taller</h1><p>Agrega un centro de servicio y asócialo con nuevos clientes.</p></div><span class="heading-icon">⌘</span></div><form class="surface form-surface" @submit.prevent="saveWorkshop"><div class="form-section-title"><span>01</span><div><strong>Información del negocio</strong><small>Los campos con * son obligatorios.</small></div></div><div class="form-grid"><label>Nombre *<input v-model="workshopForm.name" placeholder="Nombre del taller"><small>{{ workshopErrors.name }}</small></label><label>Razón social *<input v-model="workshopForm.business_name" placeholder="Razón social"></label><label>RFC *<input v-model="workshopForm.rfc" maxlength="13" placeholder="RFC mexicano"><small>{{ workshopErrors.rfc }}</small></label><label>Teléfono *<input v-model="workshopForm.phone" placeholder="10 dígitos"></label><label>Correo *<input v-model="workshopForm.contact_email" type="email" placeholder="correo@empresa.com"></label><label>Fotografía *<input type="file" accept="image/png,image/jpeg" @change="selectWorkshopPhoto"></label></div><div class="form-section-title"><span>02</span><div><strong>Ubicación</strong><small>El catálogo completa la dirección cuando reconoce el CP.</small></div></div><div class="form-grid"><label>CP *<input v-model="workshopForm.postal_code" maxlength="5" @change="lookupPostal(workshopForm)" placeholder="00000"></label><label>Estado *<input v-model="workshopForm.state" :readonly="(workshopForm._neighborhoods||[]).length>0"></label><label>Municipio *<input v-model="workshopForm.municipality" :readonly="(workshopForm._neighborhoods||[]).length>0"></label><label>Colonia *<select v-if="(workshopForm._neighborhoods||[]).length" v-model="workshopForm.neighborhood"><option v-for="item in workshopForm._neighborhoods" :value="item.name">{{ item.name }}</option></select><input v-else v-model="workshopForm.neighborhood"></label><label>Calle *<input v-model="workshopForm.street" placeholder="Calle y número"></label></div><p v-if="postalNotice" class="alert success">{{ postalNotice }}</p><div v-if="Object.keys(workshopErrors).length" class="field-errors"><strong>Corrige estos campos:</strong><ul><li v-for="(message, field) in workshopErrors" :key="field"><b>{{ field }}:</b> {{ message }}</li></ul></div><p v-if="workshopNotice" class="alert" :class="/exitosamente/i.test(workshopNotice) ? 'success' : 'error'">{{ workshopNotice }}</p><button class="button primary submit-button">Guardar taller <span>→</span></button></form></section>
      <section v-else-if="activeView==='client-list'" class="page"><div class="page-heading"><div><span class="section-kicker">DIRECTORIO</span><h1>Consultar clientes</h1><p>Explora clientes por taller y estado.</p></div><button class="button primary" @click="openRegister">＋ Nuevo cliente</button></div><div class="surface filter-bar"><label>Taller<select v-model="clientFilterWorkshop" @change="openClients(1)"><option value="">Todos los talleres</option><option v-for="workshop in workshops" :value="workshop.id">{{ workshop.name }}</option></select></label><label>Estatus<select v-model="clientFilterStatus" @change="openClients(1)"><option value="">Todos los estatus</option><option value="ACTIVO">Activos</option><option value="SUSPENDIDO">Suspendidos</option></select></label><button class="button ghost dark" @click="clientDirection=clientDirection==='asc'?'desc':'asc';loadClients()">Orden: {{ clientDirection==='asc' ? 'A → Z' : 'Z → A' }}</button></div><div class="list-caption"><div><strong>{{ clientTotal }}</strong> clientes encontrados <span v-if="clientsLoading">· Actualizando…</span></div><span>Página {{ clientPage }} de {{ clientPages }}</span></div><div v-if="clients.length" class="client-grid"><button v-for="client in clients" :key="client.id" class="client-card" :class="{suspended: client.status==='SUSPENDIDO'}" @click="openClientDetail(client)"><div class="client-photo"><img v-if="client.photo_url" :src="client.photo_url" :alt="client.full_name"><span v-else>{{ client.full_name.slice(0,1) }}</span><em :class="client.status==='ACTIVO' ? 'active' : 'suspended'">{{ client.status }}</em></div><div class="client-card-body"><small>{{ client.workshop_name }}</small><strong>{{ client.full_name }}</strong><span>Ver detalle <i>→</i></span></div></button></div><div v-else class="empty-state"><span>▦</span><h2>No hay clientes para este filtro</h2><p>Cambia los filtros o registra un nuevo cliente.</p></div><div class="pagination"><button class="button ghost dark" :disabled="clientPage===1" @click="openClients(clientPage-1)">← Anterior</button><span>{{ clientPage }} / {{ clientPages }}</span><button class="button ghost dark" :disabled="clientPage===clientPages" @click="openClients(clientPage+1)">Siguiente →</button></div></section>
      <section v-else-if="activeView==='client-detail'" class="page"><div class="detail-top"><button class="back-link" @click="openClients()">← Volver al directorio</button><div class="detail-actions"><button class="button ghost dark" @click="editClient">Editar</button><button v-if="isAdmin && selectedClient.status==='ACTIVO'" class="button danger" @click="changeClientStatus('suspend')">Suspender</button><button v-if="isAdmin && selectedClient.status==='SUSPENDIDO'" class="button activate" @click="changeClientStatus('activate')">✓ Activar cliente</button></div></div><article class="surface profile-detail"><div class="profile-photo"><img v-if="selectedClient.photo_url" :src="selectedClient.photo_url" :alt="selectedClient.full_name"><span v-else>{{ selectedClient.full_name.slice(0,1) }}</span></div><div class="profile-summary"><div><span class="status-pill" :class="selectedClient.status==='ACTIVO' ? 'active' : 'suspended'">{{ selectedClient.status }}</span><h1>{{ selectedClient.full_name }}</h1><p>{{ selectedClient.workshop_name }}</p></div><div class="contact-line"><span>☎ {{ selectedClient.personal_phone }}</span><span>✉ {{ selectedClient.personal_email }}</span></div></div></article><div class="detail-grid"><article class="surface info-block"><span class="section-kicker">INFORMACIÓN PERSONAL</span><dl><div><dt>Contacto alternativo</dt><dd>{{ selectedClient.alternate_contact_name }}</dd></div><div><dt>Edad</dt><dd>{{ selectedClient.age }} años</dd></div><div><dt>Fecha de nacimiento</dt><dd>{{ selectedClient.birth_date }}</dd></div><div><dt>Teléfono laboral</dt><dd>{{ selectedClient.work_phone }}</dd></div><div v-if="selectedClient.work_email"><dt>Correo laboral</dt><dd>{{ selectedClient.work_email }}</dd></div></dl></article><article class="surface info-block"><span class="section-kicker">DIRECCIÓN</span><dl><div><dt>Calle</dt><dd>{{ selectedClient.street }}</dd></div><div><dt>Colonia</dt><dd>{{ selectedClient.neighborhood }}</dd></div><div><dt>Municipio y estado</dt><dd>{{ selectedClient.municipality }}, {{ selectedClient.state }}</dd></div><div><dt>Código postal</dt><dd>{{ selectedClient.postal_code }}</dd></div></dl></article></div><p v-if="clientNotice" class="alert" :class="noticeClass">{{ clientNotice }}</p></section>
      <section v-else class="page"><div class="page-heading"><div><span class="section-kicker">{{ isEditingClient ? 'ACTUALIZACIÓN' : 'ALTA DE CLIENTE' }}</span><h1>{{ isEditingClient ? 'Modificar cliente' : 'Registrar cliente' }}</h1><p>{{ isEditingClient ? 'Actualiza los datos y guarda los cambios.' : 'Captura los datos para crear un expediente de cliente.' }}</p></div><span class="heading-icon">{{ isEditingClient ? '✎' : '＋' }}</span></div><form class="surface form-surface" @submit.prevent="saveClient"><div class="form-section-title"><span>01</span><div><strong>Datos de contacto</strong><small>Identificación y medio de comunicación del cliente.</small></div></div><div class="form-grid"><label>Taller *<select v-model="clientForm.workshop_id"><option value="">Selecciona un taller</option><option v-for="workshop in workshops" :value="workshop.id">{{ workshop.name }}</option></select><small>{{ clientErrors.workshop_id }}</small></label><label>Nombre completo *<input v-model="clientForm.full_name" placeholder="Nombre y apellidos"><small>{{ clientErrors.full_name }}</small></label><label>Contacto alternativo *<input v-model="clientForm.alternate_contact_name" placeholder="Nombre de contacto"></label><label>Edad *<input v-model="clientForm.age" type="number" min="0" max="120"></label><label>Fecha de nacimiento *<input v-model="clientForm.birth_date" type="date"></label><label>Teléfono personal *<input v-model="clientForm.personal_phone" placeholder="10 dígitos"></label><label>Teléfono laboral *<input v-model="clientForm.work_phone" placeholder="10 dígitos"></label><label>Correo personal *<input v-model="clientForm.personal_email" type="email" placeholder="correo@ejemplo.com"></label><label>Correo laboral<input v-model="clientForm.work_email" type="email" placeholder="Opcional"></label><label>Fotografía {{ isEditingClient ? '(opcional)' : '*' }}<input type="file" accept="image/png,image/jpeg" @change="selectPhoto"><small>{{ clientErrors.photo }}</small></label></div><div class="form-section-title"><span>02</span><div><strong>Dirección</strong><small>Ingresa cinco dígitos para consultar el catálogo SEPOMEX.</small></div></div><div class="form-grid"><label>CP *<input v-model="clientForm.postal_code" maxlength="5" @change="lookupPostal(clientForm)" placeholder="00000"><small>{{ clientErrors.postal_code }}</small></label><label>Estado *<input v-model="clientForm.state" :readonly="(clientForm._neighborhoods||[]).length>0"><small>{{ clientErrors.state }}</small></label><label>Municipio *<input v-model="clientForm.municipality" :readonly="(clientForm._neighborhoods||[]).length>0"><small>{{ clientErrors.municipality }}</small></label><label>Colonia *<select v-if="(clientForm._neighborhoods||[]).length" v-model="clientForm.neighborhood"><option v-for="item in clientForm._neighborhoods" :value="item.name">{{ item.name }}</option></select><input v-else v-model="clientForm.neighborhood" placeholder="Colonia"><small>{{ clientErrors.neighborhood }}</small></label><label>Calle *<input v-model="clientForm.street" placeholder="Calle y número"><small>{{ clientErrors.street }}</small></label></div><p v-if="postalNotice" class="alert success">{{ postalNotice }}</p><div v-if="Object.keys(clientErrors).length" class="field-errors"><strong>Corrige estos campos:</strong><ul><li v-for="(message, field) in clientErrors" :key="field"><b>{{ field }}:</b> {{ message }}</li></ul></div><aside v-if="duplicateClient" class="duplicate-box"><strong>Registro existente</strong><span>{{ duplicateClient.full_name }} · {{ duplicateClient.personal_email }}</span></aside><p v-if="clientNotice" class="alert" :class="noticeClass">{{ clientNotice }}</p><button class="button primary submit-button">{{ isEditingClient ? 'Guardar cambios' : 'Registrar cliente' }} <span>→</span></button></form></section>
    </section>
  </main>`
}).mount('#app')
