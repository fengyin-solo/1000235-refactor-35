<template>
  <section class="page" data-module="footage">
    <header class="page-head">
      <div>
        <h2>素材管理管理</h2>
        <p class="page-desc">维护拍摄素材，围绕素材编号、素材类型、拍摄日期、文件大小做登记、筛选与状态流转。</p>
      </div>
      <div class="page-actions">
        <button class="btn primary" type="button" @click="openCreate">登记拍摄素材</button>
        <button class="btn" type="button" @click="exportRows">导出素材管理清单</button>
      </div>
    </header>

    <div class="stat-row">
      <article v-for="item in page.stats" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong class="stat-value">{{ item.value }}</strong>
      </article>
    </div>

    <form class="filter-bar" @submit.prevent="reload">
      <label v-for="field in filterFields" :key="field" class="filter-item">
        <span>{{ field }}</span>
        <input v-model="filters[field]" :placeholder="`按${field}检索`" />
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetFilters">重置条件</button>
    </form>

    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in page.columns" :key="column">{{ column }}</th>
          <th>可执行动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="String(row.id)">
          <td v-for="column in page.columns" :key="column">{{ row[column] ?? '—' }}</td>
          <td class="row-actions">
            <button
              v-for="action in page.actions"
              :key="action"
              class="link"
              type="button"
              @click="runAction(action, row)"
            >
              {{ action }}
            </button>
          </td>
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="page.columns.length + 1" class="empty-state">暂无素材管理数据，可先登记拍摄素材</td>
        </tr>
      </tbody>
    </table>

    <footer class="page-foot">
      <span>共 {{ total }} 条素材管理记录</span>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { request } from '@/api/client'

type Row = Record<string, string | number | null>

/** 拍摄素材的共用规则：列口径、可执行动作、统计卡只维护这一份，新增素材类型时改这里即可。 */
const page = {
  endpoint: '/api/footage',
  columns: ["素材编号", "素材类型", "拍摄日期", "文件大小", "存储介质", "转码格式", "备份位置", "素材状态"],
  actions: ["提交转码", "确认归档", "登记丢失"],
  stats: [{"label": "待转码素材", "value": 0}, {"label": "已归档素材", "value": 0}, {"label": "存储占用", "value": 0}],
}

const rows = ref<Row[]>([])
const total = ref(0)
const errorMessage = ref('')
const filters = ref<Record<string, string>>({})
const filterFields = page.columns.slice(0, 3)

/** 列表、归档操作、下载共用同一套执行口径：先清掉旧错误，失败时留下一句可读的说明。 */
async function runSafely(work: () => Promise<void>, fallback: string) {
  errorMessage.value = ''
  try {
    await work()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : fallback
  }
}

function resetFilters() {
  filters.value = {}
  void reload()
}

function exportRows() {
  window.open(`${page.endpoint}/export`, '_blank')
}

function openCreate() {
  errorMessage.value = '拍摄素材登记入口尚未接入审批流'
}

async function runAction(action: string, row: Row) {
  await runSafely(async () => {
    const response = await request(`${page.endpoint}/${row.id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    })
    if (!response.ok) {
      throw new Error('素材管理动作未生效，请稍后重试')
    }
    await reload()
  }, '素材管理操作失败')
}

async function reload() {
  const query = new URLSearchParams(filters.value as Record<string, string>).toString()
  await runSafely(async () => {
    const response = await request(`${page.endpoint}?${query}`)
    if (!response.ok) {
      throw new Error('拍摄素材列表读取失败')
    }
    const payload = await response.json()
    rows.value = payload.items ?? []
    total.value = payload.total ?? rows.value.length
  }, '素材管理列表读取失败')
}

onMounted(reload)
</script>
