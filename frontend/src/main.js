import { createApp } from 'vue'
import './style.css'
import { lookupVehicle } from './services/vehicleLookup.js'
import { editVehicle } from './services/vehicleEdit.js'

const API = import.meta.env.PROD ? '/api' : 'http://localhost:8000/api'
const emptyClient = () => ({ workshop_id: '', full_name: '', alternate_contact_name: '', age: '', birth_date: '', personal_phone: '', work_phone: '', street: '', neighborhood: '', municipality: '', state: '', postal_code: '', personal_email: '', work_email: '', photo: null, _neighborhoods: [] })
const emptyWorkshop = () => ({ name: '', street: '', neighborhood: '', municipality: '', state: '', postal_code: '', business_name: '', phone: '', rfc: '', contact_email: '', photo: null, _neighborhoods: [] })

createApp({
  data: () => ({
    username: '', password: '', registerName: '', registerUsername: '', registerPassword: '', loading: false, error: '',
    vehicleLookupField: 'vin', vehicleLookupValue: '', vehicleLookupLoading: false, vehicleLookupResult: null, vehicleLookupError: '', vehicleLookupErrors: {}, vehicleLookupNotFound: false, vehicleLookupRequestId: 0,
    user: null, authMode: 'login', activeView: 'dashboard', menuExpanded: true, menuPinned: true,
    clientForm: emptyClient(), clientErrors: {}, clientNotice: '', duplicateClient: null,
    clients: [], clientsLoading: false, selectedClient: null, editingClientId: null,
    clientPage: 1, clientPages: 1, clientTotal: 0, clientFilterWorkshop: '', clientFilterStatus: '', clientOrder: 'full_name', clientDirection: 'asc',
    workshops: [], workshopForm: emptyWorkshop(), workshopErrors: {}, workshopNotice: '', postalNotice: '',
    selectedWorkshop: null, workshopClients: [], workshopClientsLoading: false, workshopClientPage: 1, workshopClientPages: 1, workshopClientTotal: 0, workshopClientDirection: 'asc', clientDetailOrigin: 'client-list',
    editingModal: false, vehicleModal: false, vehicleForm: { plate: '', brand: '', model: '', vin: '', year: '', version: '', color: '', mileage: '' }, vehicleErrors: {}, vehicleNotice: '', vehicles: [], vehiclePage: 1, vehiclePages: 1, vehicleTotal: 0,
    vehicleEditModal: false, vehicleEditRecord: null, vehicleEditForm: {}, vehicleEditErrors: {}, vehicleEditError: '', vehicleEditSuccess: '', vehicleEditLoading: false, vehicleEditRequestId: 0, vehicleEditOrigin: '',
    associatedVehiclesModal: false, associatedVehicles: [], associatedVehicle: null, associatedVehiclesLoading: false, associatedVehiclesError: '', associatedVehiclesPage: 1, associatedVehiclesPages: 1, associatedVehiclesTotal: 0,
    statusModal: false, statuses: [], statusForm: { name: '', description: '' }, statusEditingId: null, statusErrors: {}, statusNotice: '', statusPage: 1, statusPages: 1
  }),
  computed: {
    initials () { return this.user?.name?.split(' ').map(word => word[0]).join('').slice(0, 2) || 'MT' },
    canManageClients () { return ['ADMIN', 'RECEPCION'].includes(this.user?.role) },

    vehicleLookupLabel () { return { vin: 'VIN', plate: 'Placa', id: 'ID del vehículo' }[this.vehicleLookupField] || 'Valor' },
    vehicleLookupMaxLength () { return { vin: 17, plate: 9, id: 19 }[this.vehicleLookupField] || 32 },
    isEditingClient () { return this.editingClientId !== null },
    noticeClass () { return /exitosamente|verificada/i.test(this.clientNotice) ? 'success' : 'error' }
  },
  watch: {
    vehicleLookupField: { handler () { this.vehicleLookupValue = ''; this.resetVehicleLookup() }, flush: 'sync' },
    vehicleLookupValue: { handler () { this.resetVehicleLookup() }, flush: 'sync' },
    activeView: { handler (next, previous) { if (next !== previous) this.closeVehicleEdit(true, false); if (previous === 'vehicle-search' && next !== previous) this.resetVehicleLookup() }, flush: 'sync' },
    user: { handler (next, previous) { if (next?.id !== previous?.id || next?.role !== previous?.role) { this.closeVehicleEdit(true, false); this.vehicleEditSuccess = ''; this.vehicleLookupValue = ''; this.resetVehicleLookup() } }, flush: 'sync' }
  },
  beforeUnmount () { this.closeVehicleEdit(true, false); this.resetVehicleLookup() },
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
    toggleMenu () { this.menuExpanded = !this.menuExpanded; this.menuPinned = this.menuExpanded && !window.matchMedia('(max-width: 760px)').matches },
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
      this.closeVehicleEdit(true, false); this.vehicleEditSuccess = ''
      this.resetVehicleLookup(); this.vehicleLookupValue = ''
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
    async openWorkshops () {
      if (!this.requireClientAccess()) return
      await this.loadWorkshops(); this.selectedWorkshop = null; this.workshopNotice = ''; this.activeView = 'workshop-list'
    },
    async openWorkshopDetail (workshop, page = 1) {
      if (!this.requireClientAccess()) return
      this.selectedWorkshop = workshop; this.workshopClientPage = page; this.activeView = 'workshop-detail'; await this.loadWorkshopClients()
    },
    async loadWorkshopClients () {
      if (!this.selectedWorkshop) return
      this.workshopClientsLoading = true
      try {
        const query = new URLSearchParams({ workshop_id: this.selectedWorkshop.id, page: this.workshopClientPage, order: 'full_name', direction: this.workshopClientDirection })
        const response = await fetch(`${API}/clients/?${query}`, { credentials: 'include' })
        const data = await response.json()
        if (response.status === 401) { this.user = null; return }
        if (!response.ok) throw Error(data.detail)
        this.workshopClients = data.clients; this.workshopClientPages = data.pages; this.workshopClientTotal = data.total
      } catch (error) { this.workshopNotice = error.message } finally { this.workshopClientsLoading = false }
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
      this.selectedClient = data.client; this.clientNotice = ''; this.clientDetailOrigin = this.activeView; this.activeView = 'client-detail'
    },
    async returnFromClientDetail () {
      if (this.clientDetailOrigin === 'workshop-detail' && this.selectedWorkshop) return this.openWorkshopDetail(this.selectedWorkshop, this.workshopClientPage)
      return this.openClients(this.clientPage)
    },
    async editClient () {
      this.clientForm = { ...this.selectedClient, photo: null, _neighborhoods: [] }
      this.editingClientId = this.selectedClient.id; this.clientErrors = {}; this.postalNotice = ''; this.editingModal = true
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
      if (updating) { this.selectedClient = data.client; this.editingModal = false; await this.loadClients(); if (this.clientDetailOrigin === 'workshop-detail') await this.loadWorkshopClients() } else { this.clientForm = emptyClient() }
    },
    async changeClientStatus (action) {
      if (!this.canManageClients || !this.selectedClient) return
      const response = await fetch(`${API}/clients/${this.selectedClient.id}/${action}/`, { method: 'POST', credentials: 'include', headers: { 'X-CSRFToken': this.csrfToken() } })
      const data = await response.json(); this.clientNotice = data.detail
      if (response.ok) { this.selectedClient = data.client; await this.loadClients(); if (this.clientDetailOrigin === 'workshop-detail') await this.loadWorkshopClients() }
    },
    async openAssociatedVehicles () {
      this.vehicleEditSuccess = ''
      if (!this.requireClientAccess() || !this.selectedClient) return
      this._vehicleReturnFocus = document.activeElement
      this.associatedVehicle = null; this.associatedVehicles = []; this.associatedVehiclesError = ''; this.associatedVehiclesTotal = 0
      this.associatedVehiclesPage = 1; this.associatedVehiclesPages = 1; this.associatedVehiclesModal = true
      this.$nextTick(() => this.$refs.associatedVehiclesDialog?.focus())
      await this.loadAssociatedVehicles()
    },
    closeAssociatedVehicles () {
      this.associatedVehiclesModal = false; this.associatedVehicle = null
      this._vehicleReturnFocus?.focus()
    },
    associatedVehiclesKeys (event) {
      if (event.key === 'Escape') { event.preventDefault(); this.closeAssociatedVehicles(); return }
      if (event.key !== 'Tab') return
      const controls = [...this.$refs.associatedVehiclesDialog.querySelectorAll('button:not(:disabled), [tabindex="0"]')]
      const first = controls[0]; const last = controls[controls.length - 1]
      if (event.shiftKey && (document.activeElement === first || document.activeElement === this.$refs.associatedVehiclesDialog)) { event.preventDefault(); last?.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
    },
    async loadAssociatedVehicles (page = 1) {
      if (!this.selectedClient || this.associatedVehiclesLoading) return
      this.associatedVehiclesLoading = true; this.associatedVehiclesError = ''; this.associatedVehicle = null
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 15000)
      try {
        const response = await fetch(`${API}/clients/${this.selectedClient.id}/vehicles/?page=${page}`, { credentials: 'include', signal: controller.signal })
        if (response.status === 401) { this.closeAssociatedVehicles(); this.user = null; this.activeView = 'dashboard'; return }
        if (response.status === 403) throw Error('No tienes permiso para consultar estos vehículos.')
        if (!response.ok) throw Error('No fue posible consultar los vehículos asociados.')
        const data = await response.json()
        this.associatedVehicles = data.vehicles; this.associatedVehiclesTotal = data.total
        this.associatedVehiclesPage = data.page; this.associatedVehiclesPages = data.pages
      } catch (error) {
        this.associatedVehiclesError = error.name === 'AbortError' ? 'La consulta tardó demasiado. Intenta nuevamente.' : (error.message === 'No tienes permiso para consultar estos vehículos.' ? error.message : 'No fue posible consultar los vehículos. Intenta nuevamente.')
      } finally { clearTimeout(timeout); this.associatedVehiclesLoading = false }
    },
    selectAssociatedVehicle (vehicle) {
      this.associatedVehicle = vehicle
      this.$nextTick(() => this.$refs.associatedVehicleHeading?.focus())
    },
    backToAssociatedVehicles () {
      this.associatedVehicle = null
      this.$nextTick(() => this.$refs.associatedVehiclesDialog?.focus())
    },
    // Invalidar antes de abortar impide que una respuesta tardía repueble la ficha.
    resetVehicleLookup () {
      this.vehicleEditSuccess = ''
      this.vehicleLookupRequestId += 1
      this._vehicleLookupController?.abort()
      this._vehicleLookupController = null
      this.vehicleLookupResult = null; this.vehicleLookupError = ''; this.vehicleLookupErrors = {}; this.vehicleLookupNotFound = false; this.vehicleLookupLoading = false
    },
    openVehicleLookup () {
      if (!this.requireClientAccess()) return
      this.resetVehicleLookup(); this.vehicleLookupValue = ''; this.activeView = 'vehicle-search'
      this.$nextTick(() => this.$refs.vehicleLookupInput?.focus())
    },
    async searchVehicle () {
      if (!this.requireClientAccess()) return
      this.resetVehicleLookup()
      const field = this.vehicleLookupField
      const value = field === 'id' ? this.vehicleLookupValue.trim() : this.vehicleLookupValue.trim().toUpperCase()
      if (!value) { this.vehicleLookupErrors = { value: 'Escribe el dato del vehículo que deseas consultar.' }; return }
      const requestId = this.vehicleLookupRequestId
      const userId = this.user?.id
      const controller = new AbortController()
      this._vehicleLookupController = controller; this.vehicleLookupLoading = true
      let timedOut = false
      const timeout = setTimeout(() => { timedOut = true; controller.abort() }, 15000)
      try {
        const { status, data } = await lookupVehicle(API, field, value, controller.signal)
        if (requestId !== this.vehicleLookupRequestId || this.activeView !== 'vehicle-search' || this.user?.id !== userId) return
        if (status === 401) { this.user = null; this.activeView = 'dashboard'; return }
        if (status === 403) { this.vehicleLookupError = 'No tienes permiso para consultar vehículos.'; return }
        if (status === 404) { this.vehicleLookupNotFound = true; return }
        if (status === 422) { this.vehicleLookupErrors = data?.fields || {}; this.vehicleLookupError = 'Revisa el criterio y el dato de búsqueda.'; return }
        if (status !== 200 || !data?.vehicle) throw Error('invalid-response')
        this.vehicleLookupResult = data.vehicle
      } catch (error) {
        if (requestId !== this.vehicleLookupRequestId || this.activeView !== 'vehicle-search' || this.user?.id !== userId) return
        this.vehicleLookupError = timedOut ? 'La consulta tardó demasiado. Intenta nuevamente.' : 'No fue posible consultar el vehículo. Intenta nuevamente.'
      } finally {
        clearTimeout(timeout)
        if (requestId === this.vehicleLookupRequestId) { this.vehicleLookupLoading = false; this._vehicleLookupController = null }
      }
    },
    // El formulario mantiene una copia: Cancelar nunca muta el vehículo mostrado.
    openVehicleEdit (vehicle, origin) {
      if (!this.canManageClients || !vehicle || this.vehicleEditLoading) return
      this._vehicleEditReturnFocus = document.activeElement
      this.vehicleEditRequestId += 1; this.vehicleEditRecord = { ...vehicle }; this.vehicleEditOrigin = origin
      this.vehicleEditForm = { plate: vehicle.plate, brand: vehicle.brand, model: vehicle.model, year: vehicle.year, version: vehicle.version, color: vehicle.color, mileage: vehicle.mileage ?? '' }
      this.vehicleEditErrors = {}; this.vehicleEditError = ''; this.vehicleEditSuccess = ''; this.vehicleEditModal = true
      this.$nextTick(() => this.$refs.vehicleEditDialog?.focus())
    },
    closeVehicleEdit (force = false, restoreFocus = true) {
      if (this.vehicleEditLoading && !force) return
      const origin = this.vehicleEditOrigin
      this.vehicleEditRequestId += 1; this._vehicleEditController?.abort(); this._vehicleEditController = null
      this.vehicleEditModal = false; this.vehicleEditLoading = false; this.vehicleEditRecord = null; this.vehicleEditForm = {}; this.vehicleEditErrors = {}; this.vehicleEditError = ''
      if (restoreFocus) this.$nextTick(() => {
        if (this._vehicleEditReturnFocus?.isConnected) this._vehicleEditReturnFocus.focus()
        else if (origin === 'associated') this.$refs.associatedVehicleEditButton?.focus()
        else this.$refs.lookupVehicleEditButton?.focus()
      })
    },
    vehicleEditKeys (event) {
      if (event.key === 'Escape') { event.preventDefault(); this.closeVehicleEdit(); return }
      if (event.key !== 'Tab') return
      const dialog = this.$refs.vehicleEditDialog
      const controls = [...dialog.querySelectorAll('button:not(:disabled), input:not(:disabled), select:not(:disabled), [tabindex="0"]')]
      const first = controls[0]; const last = controls[controls.length - 1]
      if (!first) { event.preventDefault(); dialog.focus(); return }
      if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog)) { event.preventDefault(); last.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    },
    async saveVehicleEdit () {
      if (!this.vehicleEditModal || !this.vehicleEditRecord || this.vehicleEditLoading || !this.canManageClients) return
      this.vehicleEditErrors = {}; this.vehicleEditError = ''
      const requestId = ++this.vehicleEditRequestId
      const userId = this.user.id; const vehicleId = this.vehicleEditRecord.id
      const controller = new AbortController(); this._vehicleEditController = controller; this.vehicleEditLoading = true
      let timedOut = false
      const timeout = setTimeout(() => { timedOut = true; controller.abort() }, 15000)
      const form = this.vehicleEditForm
      // Solo enviar campos editables; ID, VIN, cliente, taller y estatus son inmutables aquí.
      const payload = { plate: String(form.plate).trim().toUpperCase(), brand: String(form.brand).trim(), model: String(form.model).trim(), year: form.year === '' ? '' : Number(form.year), version: String(form.version).trim(), color: String(form.color).trim(), mileage: form.mileage === '' || form.mileage == null ? null : Number(form.mileage) }
      try {
        const { status, data } = await editVehicle(API, vehicleId, payload, this.csrfToken(), controller.signal)
        if (requestId !== this.vehicleEditRequestId || !this.vehicleEditModal || this.user?.id !== userId || this.vehicleEditRecord?.id !== vehicleId) return
        if (status === 401) { this.closeVehicleEdit(true, false); this.user = null; this.activeView = 'dashboard'; return }
        if (status === 403) { this.vehicleEditError = 'No tienes permiso para editar este vehículo.'; return }
        if (status === 404) { this.vehicleEditError = 'Vehículo no encontrado. Cierra esta ventana y vuelve a consultar.'; return }
        if (status === 409) { this.vehicleEditError = 'Ya existe un vehículo con esa placa. Revisa el dato antes de guardar.'; return }
        if (status === 422) { this.vehicleEditErrors = data?.fields || {}; this.vehicleEditError = 'Revisa los campos señalados.'; return }
        if (status !== 200 || !data?.vehicle || data.vehicle.id !== vehicleId) throw Error('invalid-response')
        const updated = data.vehicle
        if (this.vehicleLookupResult?.id === vehicleId) this.vehicleLookupResult = { ...this.vehicleLookupResult, ...updated }
        if (this.associatedVehicle?.id === vehicleId) this.associatedVehicle = { ...this.associatedVehicle, ...updated }
        this.associatedVehicles = this.associatedVehicles.map(item => item.id === vehicleId ? { ...item, ...updated } : item)
        this.vehicles = this.vehicles.map(item => item.id === vehicleId ? { ...item, ...updated } : item)
        this.vehicleEditLoading = false; this.closeVehicleEdit()
        this.vehicleEditSuccess = 'Vehículo actualizado correctamente.'
      } catch (error) {
        if (requestId !== this.vehicleEditRequestId || !this.vehicleEditModal || this.user?.id !== userId) return
        this.vehicleEditError = timedOut ? 'La respuesta tardó demasiado. Vuelve a consultar el vehículo para confirmar si se guardaron los cambios.' : 'No fue posible confirmar el guardado. Vuelve a consultar el vehículo antes de intentarlo de nuevo.'
      } finally {
        clearTimeout(timeout)
        if (requestId === this.vehicleEditRequestId) { this.vehicleEditLoading = false; this._vehicleEditController = null }
      }
    },
    async openVehicleModal () {
      if (this.selectedClient?.status !== 'ACTIVO') { this.clientNotice = 'Sólo puedes registrar vehículos para clientes activos.'; return }
      this.vehicleForm = { plate: '', brand: '', model: '', vin: '', year: '', version: '', color: '', mileage: '' }; this.vehicleErrors = {}; this.vehicleNotice = ''; this.vehicleModal = true; await this.loadVehicles()
    },
    async loadVehicles (page = 1) {
      if (!this.selectedClient) return
      this.vehiclePage = page
      const response = await fetch(`${API}/clients/${this.selectedClient.id}/vehicles/?page=${page}`, { credentials: 'include' })
      const data = await response.json(); if (!response.ok) { this.vehicleNotice = data.detail; return }
      this.vehicles = data.vehicles; this.vehiclePages = data.pages; this.vehicleTotal = data.total
    },
    async saveVehicle () {
      this.vehicleErrors = {}; this.vehicleNotice = ''
      const response = await fetch(`${API}/clients/${this.selectedClient.id}/vehicles/`, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken() }, body: JSON.stringify(this.vehicleForm) })
      const data = await response.json()
      if (response.status === 422) { this.vehicleErrors = data.fields || {}; this.vehicleNotice = 'Revisa los campos señalados.'; return }
      if (response.status === 409) { this.vehicleNotice = data.detail; return }
      if (!response.ok) { this.vehicleNotice = data.detail; return }
      this.vehicleNotice = `${data.detail} ID del vehículo: ${data.vehicle.id}.`; await this.loadVehicles(); this.vehicleForm = { plate: '', brand: '', model: '', vin: '', year: '', version: '', color: '', mileage: '' }
    },
    async openStatuses () { this.statusModal = true; this.statusForm = { name: '', description: '' }; this.statusEditingId = null; this.statusErrors = {}; this.statusNotice = ''; await this.loadStatuses() },
    async loadStatuses (page = 1) { const response = await fetch(`${API}/estatus/?page=${page}`, { credentials: 'include' }); const data = await response.json(); if (response.ok) { this.statuses = data.statuses; this.statusPage = data.page; this.statusPages = data.pages } else this.statusNotice = data.detail },
    editStatus (status) { this.statusEditingId = status.id; this.statusForm = { name: status.name, description: status.description }; this.statusErrors = {}; this.statusNotice = '' },
    async saveStatus () { const url = this.statusEditingId ? `${API}/estatus/${this.statusEditingId}/` : `${API}/estatus/`; const response = await fetch(url, { method: this.statusEditingId ? 'PUT' : 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken() }, body: JSON.stringify(this.statusForm) }); const data = await response.json(); if (response.status === 422) { this.statusErrors = data.fields || {}; return } this.statusNotice = data.detail; if (response.ok) { this.statusForm = { name: '', description: '' }; this.statusEditingId = null; await this.loadStatuses(this.statusPage) } },
    async deleteStatus (status) { if (!window.confirm(`¿Eliminar el estatus ${status.name}?`)) return; const response = await fetch(`${API}/estatus/${status.id}/`, { method: 'DELETE', credentials: 'include', headers: { 'X-CSRFToken': this.csrfToken() } }); const data = await response.json(); this.statusNotice = data.detail; if (response.ok) await this.loadStatuses(this.statusPage) },
    async openWorkshopRegister () {
      if (!this.requireClientAccess()) return
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
    <div v-if="editingModal" class="modal-backdrop" @click.self="editingModal=false"><form class="modal-card" @submit.prevent="saveClient"><div class="modal-head"><h2>Editar cliente</h2><button type="button" @click="editingModal=false">×</button></div><div class="form-grid"><label>Nombre completo *<input v-model="clientForm.full_name"><small>{{ clientErrors.full_name }}</small></label><label>Contacto alternativo *<input v-model="clientForm.alternate_contact_name"></label><label>Edad *<input v-model="clientForm.age" type="number"></label><label>Fecha de nacimiento *<input v-model="clientForm.birth_date" type="date"></label><label>Teléfono personal *<input v-model="clientForm.personal_phone"><small>{{ clientErrors.personal_phone }}</small></label><label>Teléfono laboral *<input v-model="clientForm.work_phone"></label><label>Correo personal *<input v-model="clientForm.personal_email" type="email"><small>{{ clientErrors.personal_email }}</small></label><label>Correo laboral<input v-model="clientForm.work_email" type="email"></label><label>CP *<input v-model="clientForm.postal_code" maxlength="5" @change="lookupPostal(clientForm)"></label><label>Estado *<input v-model="clientForm.state" :readonly="(clientForm._neighborhoods||[]).length>0"></label><label>Municipio *<input v-model="clientForm.municipality" :readonly="(clientForm._neighborhoods||[]).length>0"></label><label>Colonia *<select v-if="(clientForm._neighborhoods||[]).length" v-model="clientForm.neighborhood"><option v-for="item in clientForm._neighborhoods" :value="item.name">{{ item.name }}</option></select><input v-else v-model="clientForm.neighborhood"></label><label>Calle *<input v-model="clientForm.street"></label><label>Foto nueva (opcional)<input type="file" accept="image/png,image/jpeg" @change="selectPhoto"></label></div><p v-if="clientNotice" class="alert" :class="noticeClass">{{ clientNotice }}</p><button class="button primary">Guardar cambios</button></form></div>
    <div v-if="associatedVehiclesModal && !vehicleEditModal" class="modal-backdrop" @click.self="closeAssociatedVehicles">
      <section ref="associatedVehiclesDialog" class="modal-card associated-vehicles-dialog" role="dialog" aria-modal="true" aria-labelledby="associated-vehicles-title" tabindex="-1" @keydown="associatedVehiclesKeys">
        <div class="modal-head"><div><span class="section-kicker">PERFIL DEL CLIENTE</span><h2 id="associated-vehicles-title">Vehículo(s) asociados</h2><p class="associated-client-name">{{ selectedClient.full_name }}</p></div><button type="button" aria-label="Cerrar vehículos asociados" @click="closeAssociatedVehicles">×</button></div>
        <template v-if="associatedVehicle">
          <button type="button" class="back-link" @click="backToAssociatedVehicles">← Volver a la lista</button>
          <div class="associated-vehicle-heading"><div><span class="section-kicker">VEHÍCULO SELECCIONADO</span><h3 ref="associatedVehicleHeading" tabindex="-1">{{ associatedVehicle.brand }} {{ associatedVehicle.model }}</h3><p>{{ associatedVehicle.plate }}</p></div><span class="status-pill">{{ associatedVehicle.status }}</span></div>
          <div class="vehicle-edit-entry"><button v-if="canManageClients" ref="associatedVehicleEditButton" type="button" class="button primary" @click="openVehicleEdit(associatedVehicle, 'associated')">Editar vehículo</button><p v-if="vehicleEditSuccess" class="alert success" role="status">{{ vehicleEditSuccess }}</p></div>
          <dl class="associated-vehicle-fields">
            <div><dt>ID del vehículo</dt><dd>{{ associatedVehicle.id }}</dd></div><div><dt>Placa</dt><dd>{{ associatedVehicle.plate }}</dd></div><div><dt>VIN</dt><dd>{{ associatedVehicle.vin }}</dd></div>
            <div><dt>Marca</dt><dd>{{ associatedVehicle.brand }}</dd></div><div><dt>Modelo</dt><dd>{{ associatedVehicle.model }}</dd></div>
            <div><dt>Año</dt><dd>{{ associatedVehicle.year }}</dd></div><div><dt>Versión</dt><dd>{{ associatedVehicle.version }}</dd></div>
            <div><dt>Color</dt><dd>{{ associatedVehicle.color }}</dd></div><div><dt>Kilometraje</dt><dd>{{ associatedVehicle.mileage == null ? 'No registrado' : associatedVehicle.mileage.toLocaleString('es-MX') + ' km' }}</dd></div>
            <div><dt>Estatus</dt><dd>{{ associatedVehicle.status }}</dd></div><div><dt>Fecha de registro</dt><dd>{{ new Date(associatedVehicle.created_at).toLocaleString('es-MX') }}</dd></div>
          </dl>
        </template>
        <template v-else>
          <p v-if="associatedVehiclesLoading" role="status" class="associated-state">Cargando vehículos asociados…</p>
          <div v-else-if="associatedVehiclesError" role="alert"><p class="alert error">{{ associatedVehiclesError }}</p><button type="button" class="button ghost dark" @click="loadAssociatedVehicles(associatedVehiclesPage)">Reintentar</button></div>
          <div v-else-if="!associatedVehicles.length" class="empty-state"><h3>Sin vehículos asociados</h3><p>Este cliente todavía no tiene vehículos registrados en esta página.</p></div>
          <div v-else><p class="associated-caption">{{ associatedVehiclesTotal }} vehículo(s) registrados. Selecciona uno para ver su información.</p><div class="associated-vehicles-list"><button v-for="vehicle in associatedVehicles" :key="vehicle.id" type="button" class="associated-vehicle-row" @click="selectAssociatedVehicle(vehicle)"><span class="associated-plate">{{ vehicle.plate }}</span><span><strong>{{ vehicle.brand }} {{ vehicle.model }}</strong><small>{{ vehicle.year }} · {{ vehicle.color }} · {{ vehicle.status }}</small></span><span aria-hidden="true">→</span></button></div></div>
          <div v-if="!associatedVehiclesError && associatedVehiclesPages > 1" class="pagination"><button type="button" class="button ghost dark" :disabled="associatedVehiclesLoading || associatedVehiclesPage <= 1" @click="loadAssociatedVehicles(associatedVehiclesPage-1)">← Anterior</button><span>Página {{ associatedVehiclesPage }} de {{ associatedVehiclesPages }}</span><button type="button" class="button ghost dark" :disabled="associatedVehiclesLoading || associatedVehiclesPage >= associatedVehiclesPages" @click="loadAssociatedVehicles(associatedVehiclesPage+1)">Siguiente →</button></div>
        </template>
      </section>
    </div>
    <div v-if="vehicleEditModal" class="modal-backdrop vehicle-edit-backdrop" @click.self="closeVehicleEdit()">
      <section ref="vehicleEditDialog" class="modal-card vehicle-edit-dialog" role="dialog" aria-modal="true" aria-labelledby="vehicle-edit-title" tabindex="-1" @keydown="vehicleEditKeys" :aria-busy="vehicleEditLoading">
        <div class="modal-head"><div><span class="section-kicker">DATOS DEL VEHÍCULO</span><h2 id="vehicle-edit-title">Editar vehículo</h2><p class="associated-client-name">El ID y el VIN se conservan sin cambios.</p></div><button type="button" :disabled="vehicleEditLoading" aria-label="Cerrar edición de vehículo" @click="closeVehicleEdit()">×</button></div>
        <form @submit.prevent="saveVehicleEdit" novalidate>
          <fieldset :disabled="vehicleEditLoading" class="vehicle-edit-fields"><div class="form-grid">
            <label>ID del vehículo<input :value="vehicleEditRecord.id" readonly aria-readonly="true"></label>
            <label>VIN<input :value="vehicleEditRecord.vin" readonly aria-readonly="true"></label>
            <label>Placa *<input v-model="vehicleEditForm.plate" maxlength="9" placeholder="ABC-123-D" :aria-invalid="!!vehicleEditErrors.plate" aria-describedby="vehicle-edit-plate-error"><small id="vehicle-edit-plate-error">{{ vehicleEditErrors.plate }}</small></label>
            <label>Marca *<input v-model="vehicleEditForm.brand" maxlength="50" :aria-invalid="!!vehicleEditErrors.brand" aria-describedby="vehicle-edit-brand-error"><small id="vehicle-edit-brand-error">{{ vehicleEditErrors.brand }}</small></label>
            <label>Modelo *<input v-model="vehicleEditForm.model" maxlength="50" :aria-invalid="!!vehicleEditErrors.model" aria-describedby="vehicle-edit-model-error"><small id="vehicle-edit-model-error">{{ vehicleEditErrors.model }}</small></label>
            <label>Año *<input v-model="vehicleEditForm.year" type="number" min="1950" :max="new Date().getFullYear()+1" :aria-invalid="!!vehicleEditErrors.year" aria-describedby="vehicle-edit-year-error"><small id="vehicle-edit-year-error">{{ vehicleEditErrors.year }}</small></label>
            <label>Versión *<input v-model="vehicleEditForm.version" maxlength="50" :aria-invalid="!!vehicleEditErrors.version" aria-describedby="vehicle-edit-version-error"><small id="vehicle-edit-version-error">{{ vehicleEditErrors.version }}</small></label>
            <label>Color *<input v-model="vehicleEditForm.color" maxlength="50" :aria-invalid="!!vehicleEditErrors.color" aria-describedby="vehicle-edit-color-error"><small id="vehicle-edit-color-error">{{ vehicleEditErrors.color }}</small></label>
            <label>Kilometraje<input v-model="vehicleEditForm.mileage" type="number" min="0" step="1" :aria-invalid="!!vehicleEditErrors.mileage" aria-describedby="vehicle-edit-mileage-error"><small id="vehicle-edit-mileage-error">{{ vehicleEditErrors.mileage }}</small></label>
          </div></fieldset>
          <p v-if="vehicleEditError" class="alert error" role="alert">{{ vehicleEditError }}</p>
          <p v-if="vehicleEditLoading" class="associated-state" role="status">Guardando cambios del vehículo…</p>
          <div class="vehicle-edit-actions"><button type="button" class="button ghost dark" :disabled="vehicleEditLoading" @click="closeVehicleEdit()">Cancelar</button><button type="submit" class="button primary" :disabled="vehicleEditLoading">{{ vehicleEditLoading ? 'Guardando…' : 'Guardar cambios' }}</button></div>
        </form>
      </section>
    </div>
    <div v-if="vehicleModal" class="modal-backdrop" @click.self="vehicleModal=false"><form class="modal-card" @submit.prevent="saveVehicle"><div class="modal-head"><h2>Registrar vehículo</h2><button type="button" @click="vehicleModal=false">×</button></div><div class="form-grid"><label>Placa *<input v-model="vehicleForm.plate" placeholder="ABC-123-D"><small>{{ vehicleErrors.plate }}</small></label><label>VIN *<input v-model="vehicleForm.vin" maxlength="17"><small>{{ vehicleErrors.vin }}</small></label><label>Marca *<input v-model="vehicleForm.brand"></label><label>Modelo *<input v-model="vehicleForm.model"></label><label>Año *<input v-model="vehicleForm.year" type="number"></label><label>Versión *<input v-model="vehicleForm.version"></label><label>Color *<input v-model="vehicleForm.color"></label><label>Kilometraje<input v-model="vehicleForm.mileage" type="number" min="0"></label></div><p v-if="vehicleNotice" class="alert error">{{ vehicleNotice }}</p><button class="button primary">Registrar vehículo</button><div class="modal-list"><strong>{{ vehicleTotal }} vehículo(s) asociados</strong><div v-for="vehicle in vehicles" :key="vehicle.id">{{ vehicle.plate }} · {{ vehicle.brand }} {{ vehicle.model }} · {{ vehicle.status }}</div><div class="pagination"><button type="button" class="button ghost dark" :disabled="vehiclePage===1" @click="loadVehicles(vehiclePage-1)">←</button><span>{{ vehiclePage }}/{{ vehiclePages }}</span><button type="button" class="button ghost dark" :disabled="vehiclePage===vehiclePages" @click="loadVehicles(vehiclePage+1)">→</button></div></div></form></div>
    <button v-if="activeView==='client-detail' && selectedClient" class="vehicle-floating button primary" :disabled="selectedClient.status!=='ACTIVO'" @click="openVehicleModal">Registrar vehículo</button>
    <div v-if="statusModal" class="modal-backdrop" @click.self="statusModal=false"><section class="modal-card"><div class="modal-head"><h2>Administrar estatus</h2><button @click="statusModal=false">×</button></div><form @submit.prevent="saveStatus"><div class="form-grid"><label>Nombre *<input v-model="statusForm.name"><small>{{ statusErrors.name }}</small></label><label>Descripción *<input v-model="statusForm.description"><small>{{ statusErrors.description }}</small></label></div><button class="button primary">{{ statusEditingId ? 'Guardar estatus' : 'Agregar estatus' }}</button></form><p v-if="statusNotice" class="alert">{{ statusNotice }}</p><div class="modal-list"><div v-for="status in statuses" :key="status.id"><strong>{{ status.name }}</strong> — {{ status.description }} <button class="text-button" @click="editStatus(status)">Editar</button> <button class="text-button" @click="deleteStatus(status)">Eliminar</button></div><div class="pagination"><button class="button ghost dark" :disabled="statusPage===1" @click="loadStatuses(statusPage-1)">←</button><span>{{ statusPage }}/{{ statusPages }}</span><button class="button ghost dark" :disabled="statusPage===statusPages" @click="loadStatuses(statusPage+1)">→</button></div></div></section></div>
    <div class="mobile-backdrop" v-if="menuExpanded && !menuPinned" @click="toggleMenu"></div>
    <aside class="sidebar"><div class="sidebar-head"><button class="menu-button" @click="toggleMenu" :title="menuExpanded ? 'Contraer menú' : 'Abrir menú'">☰</button><div class="brand sidebar-brand"><span class="mark">M</span><span class="brand-name">MOTORA</span></div></div><div class="sidebar-label">NAVEGACIÓN</div><nav><button class="nav-item" :class="{active: activeView==='dashboard'}" @click="goHome" title="Inicio"><span>⌂</span><b>Inicio</b></button><button v-if="canManageClients" class="nav-item" :class="{active: activeView==='client-register'}" @click="openRegister" title="Registrar cliente"><span>＋</span><b>Registrar cliente</b></button><button v-if="canManageClients" class="nav-item" :class="{active: activeView==='client-list'||activeView==='client-detail'}" @click="openClients()" title="Consultar clientes"><span>▦</span><b>Consultar clientes</b></button><button v-if="canManageClients" class="nav-item" :class="{active: activeView==='vehicle-search'}" @click="openVehicleLookup" title="Consultar vehículo"><span>⌕</span><b>Consultar vehículo</b></button><button v-if="canManageClients" class="nav-item" :class="{active: activeView==='workshop-list'||activeView==='workshop-detail'}" @click="openWorkshops" title="Consultar talleres"><span>⌘</span><b>Consultar talleres</b></button><button v-if="canManageClients" class="nav-item" :class="{active: activeView==='workshop-register'}" @click="openWorkshopRegister" title="Registrar taller"><span>＋</span><b>Registrar taller</b></button></nav><div class="sidebar-footer"><div class="user-chip"><b>{{ initials }}</b><span><strong>{{ user.name }}</strong><small>{{ user.role }}</small></span></div><button class="logout-button" @click="signOut"><span>↪</span><b>Salir</b></button></div></aside>
    <section class="content-area"><header class="topbar"><div><span class="section-kicker">PANEL OPERATIVO</span><strong>{{ activeView==='dashboard' ? 'Centro de control' : activeView==='client-list' ? 'Directorio de clientes' : activeView==='workshop-register' ? 'Administración de talleres' : activeView==='vehicle-search' ? 'Consulta de vehículos' : 'Gestión de clientes' }}</strong></div><div class="topbar-user"><span class="pulse"></span> Sesión activa</div></header>
      <section v-if="activeView==='dashboard'" class="page dashboard-page"><div class="welcome"><div><span class="section-kicker">BIENVENIDO</span><h1>Hola, {{ user.name }} <span>✦</span></h1><p>Administra la atención de tus clientes con rapidez y visibilidad.</p><div class="hero-actions"><button v-if="canManageClients" class="button primary" @click="openRegister">Registrar cliente <span>→</span></button><button v-if="canManageClients" class="button ghost dark" @click="openClients()">Ver clientes</button></div></div><div class="welcome-visual"><div class="dashboard-emblem">⚙</div><span>Todo bajo control</span></div></div><div class="metric-grid"><article><span class="metric-icon blue">◉</span><div><small>CLIENTES VISIBLES</small><strong>{{ clientTotal || '—' }}</strong><p>Consulta el directorio</p></div></article><article><span class="metric-icon violet">⌘</span><div><small>TALLERES</small><strong>{{ workshops.length }}</strong><p>Centros registrados</p></div></article><article><span class="metric-icon green">✓</span><div><small>PERMISOS</small><strong>{{ user.role }}</strong><p>Rol de sesión</p></div></article></div><div class="quick-panel"><div><span class="section-kicker">ACCESOS RÁPIDOS</span><h2>¿Qué deseas hacer?</h2></div><button v-if="canManageClients" @click="openRegister"><span>＋</span> Alta de cliente <i>→</i></button><button v-if="canManageClients" @click="openClients()"><span>▦</span> Consultar directorio <i>→</i></button><button v-if="canManageClients" @click="openWorkshopRegister"><span>⌘</span> Registrar taller <i>→</i></button><button v-if="canManageClients" @click="openVehicleLookup"><span>⌕</span> Consultar vehículo <i>→</i></button></div><p v-if="clientNotice" class="alert" :class="noticeClass">{{ clientNotice }}</p></section>
      <section v-else-if="activeView==='vehicle-search'" class="page vehicle-lookup-page">
        <div class="page-heading"><div><span class="section-kicker">CONSULTA DE VEHÍCULOS</span><h1>Consultar vehículo</h1><p>Busca por VIN, placa o ID para consultar su información, cliente y taller.</p></div><span class="heading-icon" aria-hidden="true">⌕</span></div>
        <form class="surface vehicle-lookup-form" @submit.prevent="searchVehicle" :aria-busy="vehicleLookupLoading">
          <div class="form-grid"><label>Buscar por<select v-model="vehicleLookupField" :aria-invalid="!!vehicleLookupErrors.field" aria-describedby="vehicle-lookup-field-error"><option value="vin">VIN</option><option value="plate">Placa</option><option value="id">ID del vehículo</option></select><small id="vehicle-lookup-field-error">{{ vehicleLookupErrors.field }}</small></label>
          <label>{{ vehicleLookupLabel }}<input ref="vehicleLookupInput" v-model="vehicleLookupValue" :maxlength="vehicleLookupMaxLength" :inputmode="vehicleLookupField === 'id' ? 'numeric' : 'text'" :placeholder="vehicleLookupField === 'vin' ? 'VIN de 17 caracteres' : vehicleLookupField === 'plate' ? 'ABC-123-D' : 'ID asignado al registrar'" :aria-invalid="!!vehicleLookupErrors.value" aria-describedby="vehicle-lookup-value-error" autocomplete="off" spellcheck="false"><small id="vehicle-lookup-value-error">{{ vehicleLookupErrors.value }}</small></label></div>
          <div class="vehicle-lookup-form-footer"><p>La consulta busca una coincidencia exacta. El ID se asigna automáticamente al registrar el vehículo.</p><button type="submit" class="button primary" :disabled="vehicleLookupLoading || !vehicleLookupValue.trim()">{{ vehicleLookupLoading ? 'Consultando…' : 'Consultar vehículo' }} <span aria-hidden="true">→</span></button></div>
        </form>
        <p v-if="vehicleLookupLoading" class="vehicle-lookup-message" role="status">Buscando vehículo…</p>
        <p v-else-if="vehicleLookupError" class="alert error vehicle-lookup-message" role="alert">{{ vehicleLookupError }}</p>
        <div v-else-if="vehicleLookupNotFound" class="empty-state vehicle-lookup-message" role="status"><h2>Vehículo no encontrado</h2><p>Revisa el dato ingresado o consulta mediante otro criterio.</p></div>
        <article v-else-if="vehicleLookupResult" class="surface vehicle-lookup-result" aria-labelledby="vehicle-lookup-result-title">
          <div class="vehicle-lookup-result-heading"><div><span class="section-kicker">VEHÍCULO ENCONTRADO</span><h2 id="vehicle-lookup-result-title">{{ vehicleLookupResult.brand }} {{ vehicleLookupResult.model }}</h2><p>ID {{ vehicleLookupResult.id }} · {{ vehicleLookupResult.plate }}</p></div><span class="status-pill">{{ vehicleLookupResult.status }}</span></div>
          <div class="vehicle-edit-entry"><button v-if="canManageClients" ref="lookupVehicleEditButton" type="button" class="button primary" @click="openVehicleEdit(vehicleLookupResult, 'lookup')">Editar vehículo</button><p v-if="vehicleEditSuccess" class="alert success" role="status">{{ vehicleEditSuccess }}</p></div>
          <div class="vehicle-lookup-relations"><div><span>CLIENTE ASOCIADO</span><strong>{{ vehicleLookupResult.client.full_name }}</strong></div><div><span>TALLER REGISTRADO</span><strong>{{ vehicleLookupResult.workshop.name }}</strong></div></div>
          <dl class="associated-vehicle-fields"><div><dt>ID del vehículo</dt><dd>{{ vehicleLookupResult.id }}</dd></div><div><dt>VIN</dt><dd>{{ vehicleLookupResult.vin }}</dd></div><div><dt>Placa</dt><dd>{{ vehicleLookupResult.plate }}</dd></div><div><dt>Marca</dt><dd>{{ vehicleLookupResult.brand }}</dd></div><div><dt>Modelo</dt><dd>{{ vehicleLookupResult.model }}</dd></div><div><dt>Año</dt><dd>{{ vehicleLookupResult.year }}</dd></div><div><dt>Versión</dt><dd>{{ vehicleLookupResult.version }}</dd></div><div><dt>Color</dt><dd>{{ vehicleLookupResult.color }}</dd></div><div><dt>Kilometraje</dt><dd>{{ vehicleLookupResult.mileage == null ? 'No registrado' : vehicleLookupResult.mileage.toLocaleString('es-MX') + ' km' }}</dd></div><div><dt>Estatus</dt><dd>{{ vehicleLookupResult.status }}</dd></div><div><dt>Fecha de registro</dt><dd>{{ new Date(vehicleLookupResult.created_at).toLocaleString('es-MX') }}</dd></div></dl>
        </article>
        <div v-else class="empty-state vehicle-lookup-message"><h2>Encuentra un vehículo</h2><p>Elige un criterio e ingresa el VIN, la placa o el ID del registro.</p></div>
      </section>
      <section v-else-if="activeView==='workshop-register'" class="page"><div class="page-heading"><div><span class="section-kicker">ADMINISTRACIÓN</span><h1>Registrar taller</h1><p>Agrega un centro de servicio y asócialo con nuevos clientes.</p></div><span class="heading-icon">⌘</span></div><form class="surface form-surface" @submit.prevent="saveWorkshop"><div class="form-section-title"><span>01</span><div><strong>Información del negocio</strong><small>Los campos con * son obligatorios.</small></div></div><div class="form-grid"><label>Nombre *<input v-model="workshopForm.name" placeholder="Nombre del taller"><small>{{ workshopErrors.name }}</small></label><label>Razón social *<input v-model="workshopForm.business_name" placeholder="Razón social"></label><label>RFC *<input v-model="workshopForm.rfc" maxlength="13" placeholder="RFC mexicano"><small>{{ workshopErrors.rfc }}</small></label><label>Teléfono *<input v-model="workshopForm.phone" placeholder="10 dígitos"></label><label>Correo *<input v-model="workshopForm.contact_email" type="email" placeholder="correo@empresa.com"></label><label>Fotografía *<input type="file" accept="image/png,image/jpeg" @change="selectWorkshopPhoto"></label></div><div class="form-section-title"><span>02</span><div><strong>Ubicación</strong><small>El catálogo completa la dirección cuando reconoce el CP.</small></div></div><div class="form-grid"><label>CP *<input v-model="workshopForm.postal_code" maxlength="5" @change="lookupPostal(workshopForm)" placeholder="00000"></label><label>Estado *<input v-model="workshopForm.state" :readonly="(workshopForm._neighborhoods||[]).length>0"></label><label>Municipio *<input v-model="workshopForm.municipality" :readonly="(workshopForm._neighborhoods||[]).length>0"></label><label>Colonia *<select v-if="(workshopForm._neighborhoods||[]).length" v-model="workshopForm.neighborhood"><option v-for="item in workshopForm._neighborhoods" :value="item.name">{{ item.name }}</option></select><input v-else v-model="workshopForm.neighborhood"></label><label>Calle *<input v-model="workshopForm.street" placeholder="Calle y número"></label></div><p v-if="postalNotice" class="alert success">{{ postalNotice }}</p><div v-if="Object.keys(workshopErrors).length" class="field-errors"><strong>Corrige estos campos:</strong><ul><li v-for="(message, field) in workshopErrors" :key="field"><b>{{ field }}:</b> {{ message }}</li></ul></div><p v-if="workshopNotice" class="alert" :class="/exitosamente/i.test(workshopNotice) ? 'success' : 'error'">{{ workshopNotice }}</p><button class="button primary submit-button">Guardar taller <span>→</span></button></form></section>
      <section v-else-if="activeView==='workshop-list'" class="page"><div class="page-heading"><div><span class="section-kicker">CENTROS DE SERVICIO</span><h1>Consultar talleres</h1><p>Selecciona un taller para ver sus datos y los clientes asociados.</p></div><button v-if="canManageClients" class="button primary" @click="openWorkshopRegister">＋ Nuevo taller</button></div><div v-if="workshops.length" class="workshop-grid"><button v-for="workshop in workshops" :key="workshop.id" class="workshop-card" @click="openWorkshopDetail(workshop)"><div class="workshop-photo"><img v-if="workshop.photo_url" :src="workshop.photo_url" :alt="workshop.name"><span v-else>⌘</span></div><div><span class="section-kicker">TALLER</span><strong>{{ workshop.name }}</strong><small>{{ workshop.municipality }}, {{ workshop.state }}</small><span class="card-link">Ver clientes asociados →</span></div></button></div><div v-else class="empty-state"><span>⌘</span><h2>No hay talleres registrados</h2><p v-if="canManageClients">Registra el primer taller para poder asociar clientes.</p><p v-else>Un administrador debe registrar talleres primero.</p></div></section>
      <section v-else-if="activeView==='workshop-detail' && selectedWorkshop" class="page"><div class="detail-top"><button class="back-link" @click="openWorkshops">← Volver a talleres</button><button v-if="canManageClients" class="button ghost dark" @click="openWorkshopRegister">Registrar otro taller</button></div><article class="surface workshop-detail"><div class="workshop-photo large"><img v-if="selectedWorkshop.photo_url" :src="selectedWorkshop.photo_url" :alt="selectedWorkshop.name"><span v-else>⌘</span></div><div><span class="section-kicker">TALLER SELECCIONADO</span><h1>{{ selectedWorkshop.name }}</h1><p>{{ selectedWorkshop.business_name }}</p><div class="workshop-meta"><span>☎ {{ selectedWorkshop.phone }}</span><span>✉ {{ selectedWorkshop.contact_email }}</span><span>{{ selectedWorkshop.street }}, {{ selectedWorkshop.neighborhood }}, {{ selectedWorkshop.municipality }}, {{ selectedWorkshop.state }} · {{ selectedWorkshop.postal_code }}</span></div></div></article><div class="page-heading compact"><div><span class="section-kicker">CLIENTES ASOCIADOS</span><h2>{{ workshopClientTotal }} cliente{{ workshopClientTotal === 1 ? '' : 's' }} en este taller</h2></div><button class="button ghost dark" @click="workshopClientDirection=workshopClientDirection==='asc'?'desc':'asc';loadWorkshopClients()">Orden: {{ workshopClientDirection==='asc' ? 'A → Z' : 'Z → A' }}</button></div><div v-if="workshopClients.length" class="client-grid"><button v-for="client in workshopClients" :key="client.id" class="client-card" :class="{suspended: client.status==='SUSPENDIDO'}" @click="openClientDetail(client)"><div class="client-photo"><img v-if="client.photo_url" :src="client.photo_url" :alt="client.full_name"><span v-else>{{ client.full_name.slice(0,1) }}</span><em :class="client.status==='ACTIVO' ? 'active' : 'suspended'">{{ client.status }}</em></div><div class="client-card-body"><small>{{ client.workshop_name }}</small><strong>{{ client.full_name }}</strong><span>Ver detalle <i>→</i></span></div></button></div><div v-else class="empty-state"><span>▦</span><h2>No hay clientes asociados</h2><p>Los nuevos clientes pueden asociarse a este taller durante su registro.</p></div><div class="pagination"><button class="button ghost dark" :disabled="workshopClientPage===1" @click="openWorkshopDetail(selectedWorkshop, workshopClientPage-1)">← Anterior</button><span>{{ workshopClientPage }} / {{ workshopClientPages }}</span><button class="button ghost dark" :disabled="workshopClientPage===workshopClientPages" @click="openWorkshopDetail(selectedWorkshop, workshopClientPage+1)">Siguiente →</button></div><p v-if="workshopNotice" class="alert error">{{ workshopNotice }}</p></section>
      <section v-else-if="activeView==='client-list'" class="page"><div class="page-heading"><div><span class="section-kicker">DIRECTORIO</span><h1>Consultar clientes</h1><p>Explora clientes por taller y estado.</p></div><button class="button primary" @click="openRegister">＋ Nuevo cliente</button></div><div class="surface filter-bar"><label>Taller<select v-model="clientFilterWorkshop" @change="openClients(1)"><option value="">Todos los talleres</option><option v-for="workshop in workshops" :value="workshop.id">{{ workshop.name }}</option></select></label><label>Estatus<select v-model="clientFilterStatus" @change="openClients(1)"><option value="">Todos los estatus</option><option value="ACTIVO">Activos</option><option value="SUSPENDIDO">Suspendidos</option></select></label><button class="button ghost dark" @click="clientDirection=clientDirection==='asc'?'desc':'asc';loadClients()">Orden: {{ clientDirection==='asc' ? 'A → Z' : 'Z → A' }}</button></div><div class="list-caption"><div><strong>{{ clientTotal }}</strong> clientes encontrados <span v-if="clientsLoading">· Actualizando…</span></div><span>Página {{ clientPage }} de {{ clientPages }}</span></div><div v-if="clients.length" class="client-grid"><button v-for="client in clients" :key="client.id" class="client-card" :class="{suspended: client.status==='SUSPENDIDO'}" @click="openClientDetail(client)"><div class="client-photo"><img v-if="client.photo_url" :src="client.photo_url" :alt="client.full_name"><span v-else>{{ client.full_name.slice(0,1) }}</span><em :class="client.status==='ACTIVO' ? 'active' : 'suspended'">{{ client.status }}</em></div><div class="client-card-body"><small>{{ client.workshop_name }}</small><strong>{{ client.full_name }}</strong><span>Ver detalle <i>→</i></span></div></button></div><div v-else class="empty-state"><span>▦</span><h2>No hay clientes para este filtro</h2><p>Cambia los filtros o registra un nuevo cliente.</p></div><div class="pagination"><button class="button ghost dark" :disabled="clientPage===1" @click="openClients(clientPage-1)">← Anterior</button><span>{{ clientPage }} / {{ clientPages }}</span><button class="button ghost dark" :disabled="clientPage===clientPages" @click="openClients(clientPage+1)">Siguiente →</button></div></section>
      <section v-else-if="activeView==='client-detail'" class="page"><div class="detail-top"><button class="back-link" @click="openClients()">← Volver al directorio</button><div class="detail-actions"><button v-if="canManageClients" class="button primary" @click="openAssociatedVehicles">Vehículo(s) asociados</button><button class="button ghost dark" @click="editClient">Editar</button><button v-if="canManageClients && selectedClient.status==='ACTIVO'" class="button danger" @click="changeClientStatus('suspend')">Suspender</button><button v-if="canManageClients && selectedClient.status==='SUSPENDIDO'" class="button activate" @click="changeClientStatus('activate')">✓ Activar cliente</button></div></div><article class="surface profile-detail"><div class="profile-photo"><img v-if="selectedClient.photo_url" :src="selectedClient.photo_url" :alt="selectedClient.full_name"><span v-else>{{ selectedClient.full_name.slice(0,1) }}</span></div><div class="profile-summary"><div><span class="status-pill" :class="selectedClient.status==='ACTIVO' ? 'active' : 'suspended'">{{ selectedClient.status }}</span><h1>{{ selectedClient.full_name }}</h1><p>{{ selectedClient.workshop_name }}</p></div><div class="contact-line"><span>☎ {{ selectedClient.personal_phone }}</span><span>✉ {{ selectedClient.personal_email }}</span></div></div></article><div class="detail-grid"><article class="surface info-block"><span class="section-kicker">INFORMACIÓN PERSONAL</span><dl><div><dt>Contacto alternativo</dt><dd>{{ selectedClient.alternate_contact_name }}</dd></div><div><dt>Edad</dt><dd>{{ selectedClient.age }} años</dd></div><div><dt>Fecha de nacimiento</dt><dd>{{ selectedClient.birth_date }}</dd></div><div><dt>Teléfono laboral</dt><dd>{{ selectedClient.work_phone }}</dd></div><div v-if="selectedClient.work_email"><dt>Correo laboral</dt><dd>{{ selectedClient.work_email }}</dd></div></dl></article><article class="surface info-block"><span class="section-kicker">DIRECCIÓN</span><dl><div><dt>Calle</dt><dd>{{ selectedClient.street }}</dd></div><div><dt>Colonia</dt><dd>{{ selectedClient.neighborhood }}</dd></div><div><dt>Municipio y estado</dt><dd>{{ selectedClient.municipality }}, {{ selectedClient.state }}</dd></div><div><dt>Código postal</dt><dd>{{ selectedClient.postal_code }}</dd></div></dl></article></div><p v-if="clientNotice" class="alert" :class="noticeClass">{{ clientNotice }}</p></section>
      <section v-else class="page"><div class="page-heading"><div><span class="section-kicker">{{ isEditingClient ? 'ACTUALIZACIÓN' : 'ALTA DE CLIENTE' }}</span><h1>{{ isEditingClient ? 'Modificar cliente' : 'Registrar cliente' }}</h1><p>{{ isEditingClient ? 'Actualiza los datos y guarda los cambios.' : 'Captura los datos para crear un expediente de cliente.' }}</p></div><span class="heading-icon">{{ isEditingClient ? '✎' : '＋' }}</span></div><form class="surface form-surface" @submit.prevent="saveClient"><div class="form-section-title"><span>01</span><div><strong>Datos de contacto</strong><small>Identificación y medio de comunicación del cliente.</small></div></div><div class="form-grid"><label>Taller *<select v-model="clientForm.workshop_id"><option value="">Selecciona un taller</option><option v-for="workshop in workshops" :value="workshop.id">{{ workshop.name }}</option></select><small>{{ clientErrors.workshop_id }}</small></label><label>Nombre completo *<input v-model="clientForm.full_name" placeholder="Nombre y apellidos"><small>{{ clientErrors.full_name }}</small></label><label>Contacto alternativo *<input v-model="clientForm.alternate_contact_name" placeholder="Nombre de contacto"></label><label>Edad *<input v-model="clientForm.age" type="number" min="0" max="120"></label><label>Fecha de nacimiento *<input v-model="clientForm.birth_date" type="date"></label><label>Teléfono personal *<input v-model="clientForm.personal_phone" placeholder="10 dígitos"></label><label>Teléfono laboral *<input v-model="clientForm.work_phone" placeholder="10 dígitos"></label><label>Correo personal *<input v-model="clientForm.personal_email" type="email" placeholder="correo@ejemplo.com"></label><label>Correo laboral<input v-model="clientForm.work_email" type="email" placeholder="Opcional"></label><label>Fotografía {{ isEditingClient ? '(opcional)' : '*' }}<input type="file" accept="image/png,image/jpeg" @change="selectPhoto"><small>{{ clientErrors.photo }}</small></label></div><div class="form-section-title"><span>02</span><div><strong>Dirección</strong><small>Ingresa cinco dígitos para consultar el catálogo SEPOMEX.</small></div></div><div class="form-grid"><label>CP *<input v-model="clientForm.postal_code" maxlength="5" @change="lookupPostal(clientForm)" placeholder="00000"><small>{{ clientErrors.postal_code }}</small></label><label>Estado *<input v-model="clientForm.state" :readonly="(clientForm._neighborhoods||[]).length>0"><small>{{ clientErrors.state }}</small></label><label>Municipio *<input v-model="clientForm.municipality" :readonly="(clientForm._neighborhoods||[]).length>0"><small>{{ clientErrors.municipality }}</small></label><label>Colonia *<select v-if="(clientForm._neighborhoods||[]).length" v-model="clientForm.neighborhood"><option v-for="item in clientForm._neighborhoods" :value="item.name">{{ item.name }}</option></select><input v-else v-model="clientForm.neighborhood" placeholder="Colonia"><small>{{ clientErrors.neighborhood }}</small></label><label>Calle *<input v-model="clientForm.street" placeholder="Calle y número"><small>{{ clientErrors.street }}</small></label></div><p v-if="postalNotice" class="alert success">{{ postalNotice }}</p><div v-if="Object.keys(clientErrors).length" class="field-errors"><strong>Corrige estos campos:</strong><ul><li v-for="(message, field) in clientErrors" :key="field"><b>{{ field }}:</b> {{ message }}</li></ul></div><aside v-if="duplicateClient" class="duplicate-box"><strong>Registro existente</strong><span>{{ duplicateClient.full_name }} · {{ duplicateClient.personal_email }}</span></aside><p v-if="clientNotice" class="alert" :class="noticeClass">{{ clientNotice }}</p><button class="button primary submit-button">{{ isEditingClient ? 'Guardar cambios' : 'Registrar cliente' }} <span>→</span></button></form></section>
    </section>
  </main>`
}).mount('#app')
