<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <h1 class="sidebar-brand__title">{{ t('nav.companyName') }}</h1>
        <span class="sidebar-brand__subtitle">{{ t('nav.subtitle') }}</span>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" class="sidebar-nav__item" :class="{ 'is-active': $route.path === '/' }">
          <span class="sidebar-nav__icon" v-html="icons.overview"></span>
          <span class="sidebar-nav__label">{{ t('nav.overview') }}</span>
        </router-link>
        <router-link to="/inventory" class="sidebar-nav__item" :class="{ 'is-active': $route.path === '/inventory' }">
          <span class="sidebar-nav__icon" v-html="icons.inventory"></span>
          <span class="sidebar-nav__label">{{ t('nav.inventory') }}</span>
        </router-link>
        <router-link to="/orders" class="sidebar-nav__item" :class="{ 'is-active': $route.path === '/orders' }">
          <span class="sidebar-nav__icon" v-html="icons.orders"></span>
          <span class="sidebar-nav__label">{{ t('nav.orders') }}</span>
        </router-link>
        <router-link to="/spending" class="sidebar-nav__item" :class="{ 'is-active': $route.path === '/spending' }">
          <span class="sidebar-nav__icon" v-html="icons.spending"></span>
          <span class="sidebar-nav__label">{{ t('nav.finance') }}</span>
        </router-link>
        <router-link to="/demand" class="sidebar-nav__item" :class="{ 'is-active': $route.path === '/demand' }">
          <span class="sidebar-nav__icon" v-html="icons.demand"></span>
          <span class="sidebar-nav__label">{{ t('nav.demandForecast') }}</span>
        </router-link>
        <router-link to="/reports" class="sidebar-nav__item" :class="{ 'is-active': $route.path === '/reports' }">
          <span class="sidebar-nav__icon" v-html="icons.reports"></span>
          <span class="sidebar-nav__label">{{ t('nav.reports') }}</span>
        </router-link>
        <router-link to="/restocking" class="sidebar-nav__item" :class="{ 'is-active': $route.path === '/restocking' }">
          <span class="sidebar-nav__icon" v-html="icons.restocking"></span>
          <span class="sidebar-nav__label">{{ t('nav.restocking') }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="app-main">
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    const icons = {
      overview: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" /></svg>',
      inventory: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" /></svg>',
      orders: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218c1.121-2.3 1.749-4.766 1.749-7.353 0-.322-.026-.638-.076-.947H5.106M7.5 14.25L5.106 5.997M7.5 14.25L5.106 5.997m5.394 12.253a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm7.5 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" /></svg>',
      spending: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3M4.5 19.5h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" /></svg>',
      demand: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18l6.16-6.16a1.5 1.5 0 012.12 0l2.84 2.84a1.5 1.5 0 002.12 0L21.75 8.25M17.25 6h4.5v4.5" /></svg>',
      reports: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 4.5v15M15 4.5v15M4.5 9h15M4.5 15h15M3.75 4.5h16.5a1.125 1.125 0 011.125 1.125v13.75a1.125 1.125 0 01-1.125 1.125H3.75a1.125 1.125 0 01-1.125-1.125V5.625A1.125 1.125 0 013.75 4.5z" /></svg>',
      restocking: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" /></svg>'
    }

    return {
      t,
      icons,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
:root {
  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;

  /* Surface & text */
  --color-bg-page: #f8fafc;
  --color-bg-surface: #ffffff;
  --color-text-heading: #0f172a;
  --color-text-body: #1e293b;
  --color-text-secondary: #475569;
  --color-text-tertiary: #334155;
  --color-text-muted: #64748b;

  /* Borders */
  --color-border: #e2e8f0;
  --color-border-subtle: #f1f5f9;
  --color-border-hover: #cbd5e1;

  /* Brand / primary */
  --color-primary: #2563eb;
  --color-primary-accent: #3b82f6;
  --color-primary-bg: #eff6ff;

  /* Semantic status */
  --color-success: #059669;
  --color-success-bg: #d1fae5;
  --color-success-text: #065f46;
  --color-warning: #ea580c;
  --color-warning-bg: #fed7aa;
  --color-warning-text: #92400e;
  --color-danger: #dc2626;
  --color-danger-bg: #fecaca;
  --color-danger-text: #991b1b;
  --color-info-bg: #dbeafe;
  --color-info-text: #1e40af;
  --color-neutral-bg: #e0e7ff;
  --color-neutral-text: #3730a3;

  /* Spacing scale (4px base) */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;

  /* Radii */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 10px;

  /* Layout */
  --sidebar-width: 260px;
  --content-max-width: 1600px;
  --shadow-card: 0 4px 12px rgba(0, 0, 0, 0.06);
  --shadow-header: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--color-bg-page);
  color: var(--color-text-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app-shell {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  background: var(--color-bg-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: sticky;
  top: 0;
  /* Deviation from skill: overflow stays visible on .sidebar itself (not
     auto) so the footer's non-teleported ProfileMenu/LanguageSwitcher
     dropdowns aren't clipped. Only .sidebar-nav scrolls if it overflows. */
  overflow: visible;
}

.sidebar-brand {
  padding: var(--space-6) var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.sidebar-brand__title {
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--color-text-heading);
  letter-spacing: -0.025em;
}

.sidebar-brand__subtitle {
  display: block;
  font-size: 0.813rem;
  color: var(--color-text-muted);
  font-weight: 400;
  margin-top: var(--space-1);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4);
  flex: 1;
  overflow-y: auto;
}

.sidebar-nav__item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  transition: all 0.2s ease;
}

.sidebar-nav__item:hover {
  background: var(--color-border-subtle);
  color: var(--color-text-heading);
}

.sidebar-nav__item.is-active {
  background: var(--color-primary-bg);
  color: var(--color-primary);
}

.sidebar-nav__icon svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.sidebar-footer {
  border-top: 1px solid var(--color-border);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.app-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  max-width: var(--content-max-width);
  width: 100%;
  padding: var(--space-6) var(--space-8);
}

.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--color-text-heading);
  margin-bottom: 0.375rem;
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: 0.938rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-bg-surface);
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: var(--color-border-hover);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--color-text-heading);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value {
  color: var(--color-warning);
}

.stat-card.success .stat-value {
  color: var(--color-success);
}

.stat-card.danger .stat-value {
  color: var(--color-danger);
}

.stat-card.info .stat-value {
  color: var(--color-primary);
}

.card {
  background: var(--color-bg-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  border: 1px solid var(--color-border);
  margin-bottom: var(--space-5);
  box-shadow: var(--shadow-card);
  transition: all 0.2s ease;
}

.card:hover {
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border-subtle);
}

.card-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text-heading);
  letter-spacing: -0.025em;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--color-bg-page);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-weight: 600;
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--color-border-subtle);
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--color-bg-page);
}

.badge {
  display: inline-block;
  padding: 0.313rem var(--space-3);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success {
  background: var(--color-success-bg);
  color: var(--color-success-text);
}

.badge.warning {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
}

.badge.danger {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
}

.badge.info {
  background: var(--color-info-bg);
  color: var(--color-info-text);
}

.badge.increasing {
  background: var(--color-success-bg);
  color: var(--color-success-text);
}

.badge.decreasing {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
}

.badge.stable {
  background: var(--color-neutral-bg);
  color: var(--color-neutral-text);
}

.badge.high {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
}

.badge.medium {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
}

.badge.low {
  background: var(--color-info-bg);
  color: var(--color-info-text);
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--color-text-muted);
  font-size: 0.938rem;
}

.error {
  background: #fef2f2;
  border: 1px solid var(--color-danger-bg);
  color: var(--color-danger-text);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: 0.938rem;
}
</style>
