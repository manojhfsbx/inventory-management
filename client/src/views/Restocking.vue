<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Set a budget and restock items based on demand forecasts</p>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Budget</h3>
      </div>
      <div class="budget-slider">
        <div class="budget-value">{{ formatCurrency(budget, 'USD') }}</div>
        <input
          type="range"
          class="budget-range"
          min="0"
          max="5000"
          step="50"
          v-model.number="budget"
        />
        <div class="budget-range-labels">
          <span>$0</span>
          <span>$5,000</span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading recommendations...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">Budget</div>
          <div class="stat-value">{{ formatCurrency(budget, 'USD') }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Selected Cost</div>
          <div class="stat-value">{{ formatCurrency(selectedCost, 'USD') }}</div>
        </div>
        <div class="stat-card" :class="remaining < 0 ? 'danger' : 'success'">
          <div class="stat-label">Remaining</div>
          <div class="stat-value">{{ formatCurrency(remaining, 'USD') }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Items</h3>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          <p>No items can be recommended at this budget — try increasing it.</p>
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th></th>
                <th>Item</th>
                <th>Trend</th>
                <th>Current / Forecasted Demand</th>
                <th>Recommended Qty</th>
                <th>Unit Cost</th>
                <th>Line Cost</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.sku">
                <td>
                  <input
                    type="checkbox"
                    :checked="selectedSkus.has(rec.sku)"
                    @change="toggleSku(rec.sku)"
                  />
                </td>
                <td>
                  <div class="item-name">{{ rec.name }}</div>
                  <div class="item-sku">{{ rec.sku }}</div>
                </td>
                <td>
                  <span :class="['badge', rec.trend]">{{ rec.trend }}</span>
                </td>
                <td>{{ rec.current_demand }} / {{ rec.forecasted_demand }}</td>
                <td>{{ rec.recommended_qty }}</td>
                <td>{{ formatCurrencyWithDecimals(rec.unit_cost, 'USD', 2) }}</td>
                <td>{{ formatCurrencyWithDecimals(rec.cost, 'USD', 2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="submitError" class="error">{{ submitError }}</div>
      <div v-if="orderResult" class="order-confirmation">
        Order <strong>{{ orderResult.order_number }}</strong> placed successfully.
        Expected delivery: {{ formatDate(orderResult.expected_delivery) }}
      </div>

      <button
        class="place-order-btn"
        :disabled="selectedSkus.size === 0 || submitting || !!orderResult"
        @click="placeOrder"
      >
        {{ orderResult ? 'Order placed' : (submitting ? 'Placing order...' : 'Place Order') }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const budget = ref(1000)
    const recommendations = ref([])
    const selectedSkus = ref(new Set())

    const loading = ref(true)
    const error = ref(null)

    const submitting = ref(false)
    const submitError = ref(null)
    const orderResult = ref(null)

    let debounceTimer = null
    let latestRequestId = 0

    const loadRecommendations = async () => {
      const requestId = ++latestRequestId
      try {
        loading.value = true
        error.value = null
        const data = await api.getRestockRecommendations(budget.value)
        if (requestId !== latestRequestId) return // a newer request superseded this one

        recommendations.value = data.recommendations

        // Default-select all recommended items - they're already
        // budget-filtered/trimmed by the server.
        selectedSkus.value = new Set(data.recommendations.map(r => r.sku))
      } catch (err) {
        if (requestId !== latestRequestId) return
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        if (requestId === latestRequestId) loading.value = false
      }
    }

    const toggleSku = (sku) => {
      const next = new Set(selectedSkus.value)
      if (next.has(sku)) {
        next.delete(sku)
      } else {
        next.add(sku)
      }
      selectedSkus.value = next
    }

    const selectedCost = computed(() => {
      return recommendations.value
        .filter(rec => selectedSkus.value.has(rec.sku))
        .reduce((sum, rec) => sum + rec.cost, 0)
    })

    const remaining = computed(() => budget.value - selectedCost.value)

    // Debounce budget changes before hitting the API, then reset any
    // previously submitted order state since the recommendation set changed.
    watch(budget, () => {
      orderResult.value = null
      submitError.value = null

      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 300)
    })

    const placeOrder = async () => {
      submitting.value = true
      submitError.value = null
      try {
        const items = recommendations.value
          .filter(rec => selectedSkus.value.has(rec.sku))
          .map(rec => ({
            sku: rec.sku,
            name: rec.name,
            quantity: rec.recommended_qty,
            unit_price: rec.unit_cost
          }))

        orderResult.value = await api.createRestockOrder(items, budget.value)
      } catch (err) {
        submitError.value = 'Failed to place order: ' + (err.response?.data?.detail || err.message)
      } finally {
        submitting.value = false
      }
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    onMounted(loadRecommendations)

    return {
      budget,
      recommendations,
      selectedSkus,
      loading,
      error,
      submitting,
      submitError,
      orderResult,
      selectedCost,
      remaining,
      toggleSku,
      placeOrder,
      formatCurrency,
      formatCurrencyWithDecimals,
      formatDate
    }
  }
}
</script>

<style scoped>
.budget-slider {
  padding: 0.5rem 0.25rem;
}

.budget-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 1rem;
}

.budget-range {
  width: 100%;
  accent-color: #2563eb;
  background: #f8fafc;
  border-radius: 999px;
  height: 6px;
  cursor: pointer;
}

.budget-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.budget-range::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.budget-range::-moz-range-track {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 999px;
  height: 6px;
}

.budget-range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
}

.item-name {
  font-weight: 500;
  color: #0f172a;
}

.item-sku {
  font-size: 0.75rem;
  color: #64748b;
}

.empty-state {
  padding: 3rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.order-confirmation {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}

.place-order-btn {
  background: #2563eb;
  color: #ffffff;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}
</style>
