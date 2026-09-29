import { createApp } from 'vue'
import './style.css'

const API = 'http://localhost:8000/api'
const emptyClient = () => ({ full_name: '', alternate_contact_name: '', age: '', birth_date: '', personal_phone: '', work_phone: '', street: '', neighborhood: '', municipality: '', state: '', postal_code: '', personal_email: '', work_email: '', photo: null })

const app = createApp({
  data: () => ({
    username: '', password: '', registerName: '', registerUsername: '', registerPassword: '',
    loading: false, error: '', user: null, showPassword: false, authMode: 'login', activeView: 'dashboard',
    clientForm: emptyClient(), clientErrors: {}, clientNotice: '', duplicateClient: null,
    clients: [], clientsLoading: false, selectedClient: null, editingClientId: null,
  }),
  computed: {
    initials() { return this.user?.name?.split(' ').map((part) => part[0]).join('').slice(0, 2) || 'MT' },
    canManageClients() { return ['ADMIN', 'RECEPCION'].includes(this.user?.role) },
    isEditingClient() { return this.editingClientId !== null },
  },
  async mounted() {
    await fetch(`${API}/auth/csrf/`, { credentials: 'include' })
    const response = await fetch(`${API}/auth/me/`, { credentials: 'include' })
    if (response.ok) this.user = (await response.json()).user
  },
  methods: {
    csrfToken() { return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '' },
    switchAuth(mode) { this.authMode = mode; this.error = ''; this.showPassword = false },
    async signIn() {
      this.loading = true; this.error = ''
      try {
        const response = await fetch(`${API}/auth/login/`, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken() }, body: JSON.stringify({ username: this.username, password: this.password }) })
        const data = await response.json(); if (!response.ok) throw new Error(data.detail); this.user = data.user
      } catch (error) { this.error = error.message || 'No fue posible iniciar sesión.' } finally { this.loading = false }
    },
    async register() {
      this.loading = true; this.error = ''
      try {
        const response = await fetch(`${API}/auth/register/`, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken() }, body: JSON.stringify({ first_name: this.registerName, username: this.registerUsername, password: this.registerPassword }) })
        const data = await response.json(); if (!response.ok) throw new Error(data.detail); this.user = data.user
      } catch (error) { this.error = error.message || 'No fue posible crear la cuenta.' } finally { this.loading = false }
    },
    async signOut() { await fetch(`${API}/auth/logout/`, { method: 'POST', credentials: 'include', headers: { 'X-CSRFToken': this.csrfToken() } }); this.user = null; this.password = ''; this.activeView = 'dashboard'; this.selectedClient = null },
    requireClientAccess() {
      if (this.canManageClients) return true
      this.clientNotice = 'Acceso no autorizado. Sólo Administración y Recepción pueden gestionar clientes.'; this.activeView = 'dashboard'; return false
    },
    async openRegister() { if (!this.requireClientAccess()) return; this.clientForm = emptyClient(); this.clientErrors = {}; this.clientNotice = ''; this.duplicateClient = null; this.editingClientId = null; this.activeView = 'client-register' },
    async openClients() { if (!this.requireClientAccess()) return; this.activeView = 'client-list'; this.clientNotice = ''; this.duplicateClient = null; await this.loadClients() },
    async loadClients() {
      this.clientsLoading = true
      try { const response = await fetch(`${API}/clients/`, { credentials: 'include' }); const data = await response.json(); if (response.status === 401) { this.user = null; return }; if (!response.ok) throw new Error(data.detail); this.clients = data.clients }
      catch (error) { this.clientNotice = error.message || 'No fue posible consultar los clientes.' } finally { this.clientsLoading = false }
    },
    async openClientDetail(client) {
      if (!this.requireClientAccess()) return; this.loading = true; this.clientNotice = ''
      try { const response = await fetch(`${API}/clients/${client.id}/`, { credentials: 'include' }); const data = await response.json(); if (!response.ok) throw new Error(data.detail); this.selectedClient = data.client; this.activeView = 'client-detail' }
      catch (error) { this.clientNotice = error.message || 'No fue posible abrir el cliente.' } finally { this.loading = false }
    },
    editClient() { this.clientForm = { ...this.selectedClient, photo: null }; this.editingClientId = this.selectedClient.id; this.clientErrors = {}; this.clientNotice = ''; this.duplicateClient = null; this.activeView = 'client-register' },
    selectPhoto(event) { this.clientForm.photo = event.target.files[0] || null; delete this.clientErrors.photo },
    async saveClient() {
      this.clientErrors = {}; this.clientNotice = ''; this.duplicateClient = null; const body = new FormData()
      Object.entries(this.clientForm).forEach(([key, value]) => { if (!['id', 'photo_url', 'created_at'].includes(key) && value !== null && value !== '') body.append(key, value) })
      const updating = this.isEditingClient; this.loading = true
      try {
        const response = await fetch(updating ? `${API}/clients/${this.editingClientId}/` : `${API}/clients/register/`, { method: updating ? 'PUT' : 'POST', credentials: 'include', headers: { 'X-CSRFToken': this.csrfToken() }, body }); const data = await response.json()
        if (response.status === 401) { this.user = null; this.activeView = 'dashboard'; return }; if (response.status === 403) { this.clientNotice = data.detail; return }; if (response.status === 422) { this.clientErrors = data.fields || {}; this.clientNotice = data.detail; return }; if (response.status === 409) { this.duplicateClient = data.client; this.clientNotice = data.detail; return }; if (!response.ok) throw new Error(data.detail)
        this.clientNotice = data.detail
        if (updating) { this.selectedClient = data.client; this.activeView = 'client-detail'; await this.loadClients() } else { this.clients.unshift(data.client); this.clientForm = emptyClient(); const input = document.querySelector('#client-photo'); if (input) input.value = '' }
      } catch (error) { this.clientNotice = error.message || 'No fue posible guardar el cliente.' } finally { this.loading = false }
    },
  },
  template: `
  <main v-if="!user" class="login-page"><section class="brand-panel"><div class="brand"><span class="mark">M</span><span>MOTORA</span></div><div class="hero-copy"><p class="eyebrow">GESTIÓN INTELIGENTE DE TALLER</p><h1>El control de cada reparación, en buenas manos.</h1><p>Accede a órdenes, diagnósticos y operaciones según las responsabilidades de tu equipo.</p></div><div class="status"><i></i> Plataforma operativa y protegida</div></section><section class="form-panel"><div class="form-wrap" v-if="authMode === 'login'"><p class="eyebrow orange">ACCESO SEGURO</p><h2>Bienvenida de vuelta.</h2><p class="sub">Ingresa con tus credenciales para continuar.</p><form @submit.prevent="signIn"><label>Usuario<input v-model="username" autocomplete="username" placeholder="Tu usuario" required></label><label>Contraseña<div class="password"><input v-model="password" :type="showPassword ? 'text' : 'password'" autocomplete="current-password" placeholder="••••••••" required><button type="button" @click="showPassword=!showPassword">{{ showPassword ? 'Ocultar' : 'Ver' }}</button></div></label><p v-if="error" class="error">{{ error }}</p><button class="submit" :disabled="loading">{{ loading ? 'Verificando…' : 'Iniciar sesión' }} <span>→</span></button></form><p class="notice">Tu acceso está protegido y registrado.</p><div class="auth-switch"><p>¿Aún no tienes cuenta?</p><button class="secondary" @click="switchAuth('register')">Crear una cuenta</button></div></div><div class="form-wrap" v-else><p class="eyebrow orange">NUEVA CUENTA</p><h2>Crea tu acceso.</h2><p class="sub">Las cuentas nuevas comienzan con acceso de consulta.</p><form @submit.prevent="register"><label>Nombre<input v-model="registerName" autocomplete="name" placeholder="Tu nombre" required></label><label>Usuario<input v-model="registerUsername" autocomplete="username" placeholder="Elige un usuario" required></label><label>Contraseña<input v-model="registerPassword" type="password" autocomplete="new-password" placeholder="Mínimo 12 caracteres" minlength="12" required></label><p v-if="error" class="error">{{ error }}</p><button class="submit" :disabled="loading">{{ loading ? 'Creando…' : 'Crear cuenta' }} <span>→</span></button></form><div class="auth-switch"><p>¿Ya tienes una cuenta?</p><button class="secondary" @click="switchAuth('login')">Volver al inicio de sesión</button></div></div></section></main>
  <main v-else class="dashboard"><nav><div class="brand"><span class="mark">M</span><span>MOTORA</span></div><div class="nav-actions"><button class="nav-link" @click="activeView='dashboard'">Inicio</button><template v-if="canManageClients"><button class="nav-link" @click="openRegister">Registrar cliente</button><button class="nav-link" @click="openClients">Consultar clientes</button></template><div class="profile"><b>{{ initials }}</b><span>{{ user.name }}<small>{{ user.role }}</small></span><button @click="signOut">Salir</button></div></div></nav>
  <section v-if="activeView === 'dashboard'"><p class="eyebrow orange">PANEL DE CONTROL</p><h1>Hola, {{ user.name }}.</h1><p class="sub">Tu sesión determina las herramientas y la información a las que puedes acceder.</p><p v-if="clientNotice" class="form-message">{{ clientNotice }}</p><div class="cards"><article><span>ÓRDENES ACTIVAS</span><strong>—</strong><p>Consulta el estado de las reparaciones asignadas.</p></article><article><span>TU ROL</span><strong>{{ user.role }}</strong><p>Permisos aplicados desde el servidor.</p></article><article><span>CLIENTES</span><strong v-if="canManageClients">Disponible</strong><strong v-else>Restringido</strong><p v-if="canManageClients">Registra, consulta y modifica clientes.</p><p v-else>Tu rol no puede gestionar clientes.</p></article></div></section>
  <section v-else-if="activeView === 'client-list'" class="client-section"><p class="eyebrow orange">RECEPCIÓN · CLIENTES</p><h1>Consultar clientes</h1><p class="sub">Datos consultados desde la base de datos del taller.</p><p v-if="clientNotice" class="form-message">{{ clientNotice }}</p><p v-if="clientsLoading">Cargando clientes…</p><p v-else-if="!clients.length">Aún no hay clientes registrados.</p><div v-else class="client-grid"><button v-for="client in clients" :key="client.id" class="client-card" @click="openClientDetail(client)"><img v-if="client.photo_url" :src="client.photo_url" :alt="'Fotografía de ' + client.full_name"><strong>{{ client.full_name }}</strong><span>{{ client.personal_phone }}</span></button></div></section>
  <section v-else-if="activeView === 'client-detail' && selectedClient" class="client-section"><p class="eyebrow orange">RECEPCIÓN · CLIENTES</p><h1>Detalle del cliente</h1><div class="detail-actions"><button class="secondary" @click="openClients">Volver a clientes</button><button class="submit" @click="editClient">Modificar cliente</button></div><article class="client-detail"><img v-if="selectedClient.photo_url" :src="selectedClient.photo_url" :alt="'Fotografía de ' + selectedClient.full_name"><div><h2>{{ selectedClient.full_name }}</h2><p><b>Contacto alternativo:</b> {{ selectedClient.alternate_contact_name }}</p><p><b>Edad / nacimiento:</b> {{ selectedClient.age }} años · {{ selectedClient.birth_date }}</p><p><b>Teléfonos:</b> {{ selectedClient.personal_phone }} · {{ selectedClient.work_phone }}</p><p><b>Correos:</b> {{ selectedClient.personal_email }}<span v-if="selectedClient.work_email"> · {{ selectedClient.work_email }}</span></p><p><b>Dirección:</b> {{ selectedClient.street }}, {{ selectedClient.neighborhood }}, {{ selectedClient.municipality }}, {{ selectedClient.state }}, CP {{ selectedClient.postal_code }}</p><p v-if="clientNotice" class="form-message">{{ clientNotice }}</p></div></article></section>
  <section v-else class="client-section"><p class="eyebrow orange">RECEPCIÓN · CLIENTES</p><h1>{{ isEditingClient ? 'Modificar cliente' : 'Registrar cliente' }}</h1><p class="sub">La información se valida en el servidor antes de guardarse.</p><form class="client-form" @submit.prevent="saveClient" novalidate><h2>{{ isEditingClient ? 'Editar datos' : 'Nuevo cliente' }}</h2><p class="form-note">Todos los campos son obligatorios excepto el correo laboral. La fotografía es opcional al editar.</p><div class="form-grid"><label>Nombre completo *<input v-model="clientForm.full_name" required><small v-if="clientErrors.full_name" class="field-error">{{ clientErrors.full_name }}</small></label><label>Contacto alternativo *<input v-model="clientForm.alternate_contact_name" required><small v-if="clientErrors.alternate_contact_name" class="field-error">{{ clientErrors.alternate_contact_name }}</small></label><label>Edad *<input v-model="clientForm.age" type="number" min="0" max="120" required><small v-if="clientErrors.age" class="field-error">{{ clientErrors.age }}</small></label><label>Fecha de nacimiento *<input v-model="clientForm.birth_date" type="date" required><small v-if="clientErrors.birth_date" class="field-error">{{ clientErrors.birth_date }}</small></label><label>Teléfono personal *<input v-model="clientForm.personal_phone" type="tel" placeholder="10 dígitos o +52" required><small v-if="clientErrors.personal_phone" class="field-error">{{ clientErrors.personal_phone }}</small></label><label>Teléfono laboral *<input v-model="clientForm.work_phone" type="tel" placeholder="10 dígitos o +52" required><small v-if="clientErrors.work_phone" class="field-error">{{ clientErrors.work_phone }}</small></label><label>Correo personal *<input v-model="clientForm.personal_email" type="email" required><small v-if="clientErrors.personal_email" class="field-error">{{ clientErrors.personal_email }}</small></label><label>Correo laboral<input v-model="clientForm.work_email" type="email"><small v-if="clientErrors.work_email" class="field-error">{{ clientErrors.work_email }}</small></label><label>Fotografía {{ isEditingClient ? '' : '*' }}<input id="client-photo" @change="selectPhoto" type="file" accept="image/png,image/jpeg" :required="!isEditingClient"><small v-if="clientErrors.photo" class="field-error">{{ clientErrors.photo }}</small></label><label>Calle *<input v-model="clientForm.street" required><small v-if="clientErrors.street" class="field-error">{{ clientErrors.street }}</small></label><label>Colonia *<input v-model="clientForm.neighborhood" required><small v-if="clientErrors.neighborhood" class="field-error">{{ clientErrors.neighborhood }}</small></label><label>Municipio *<input v-model="clientForm.municipality" required><small v-if="clientErrors.municipality" class="field-error">{{ clientErrors.municipality }}</small></label><label>Estado *<input v-model="clientForm.state" required><small v-if="clientErrors.state" class="field-error">{{ clientErrors.state }}</small></label><label>Código postal *<input v-model="clientForm.postal_code" inputmode="numeric" maxlength="5" required><small v-if="clientErrors.postal_code" class="field-error">{{ clientErrors.postal_code }}</small></label></div><p v-if="clientNotice" class="form-message">{{ clientNotice }}</p><button class="submit" :disabled="loading">{{ loading ? 'Guardando…' : (isEditingClient ? 'Guardar cambios' : 'Registrar cliente') }} <span>→</span></button></form><article v-if="duplicateClient" class="duplicate-card"><span>REGISTRO EXISTENTE</span><strong>{{ duplicateClient.full_name }}</strong><p>{{ duplicateClient.personal_phone }} · {{ duplicateClient.personal_email }}</p><button class="secondary" @click="openClientDetail(duplicateClient)">Ver registro existente</button></article></section></main>`,
})

app.mount('#app')
