<template>
  <n-spin :show="loading" description="加载中…">
  <div class="drift-panel">
    <div class="panel-header">
      <span class="panel-title">文风漂移监控</span>
      <n-button size="small" :loading="loading" @click="load">刷新</n-button>
    </div>

    <n-alert v-if="loadError" type="error" :title="loadError" class="drift-alert" closable @close="loadError = ''" />

    <!-- 告警横幅 -->
    <n-alert
      v-if="report && report.drift_alert"
      type="warning"
      title="⚠️ 文风漂移告警"
      class="drift-alert"
    >
      最近 {{ report.alert_consecutive }} 章相似度均低于
      {{ (report.alert_threshold * 100).toFixed(0) }}%，
      建议回顾作者指纹或调整写作风格。
    </n-alert>

    <n-alert
      v-else-if="report && report.scores.length >= report.alert_consecutive"
      type="success"
      title="文风正常"
      class="drift-alert"
    >
      已连续 {{ report.alert_consecutive }} 章监测，近期文风与作者指纹匹配良好。
    </n-alert>

    <n-alert v-else-if="report" type="info" class="drift-alert">
      指纹样本不足（需至少 10 个文风样本才能计算相似度）。
      请先在「采血」功能（文风 → 采样）添加样本。
    </n-alert>

    <!-- 评分趋势表格 -->
    <n-data-table
      v-if="report && report.scores.length"
      :columns="columns"
      :data="report.scores.slice().reverse()"
      :max-height="300"
      size="small"
      striped
      class="score-table"
    />

    <n-empty v-else-if="!loading && report && !report.scores.length" description="暂无评分数据" size="small" />

    <!-- 手动评分章节 -->
    <n-collapse class="manual-score-collapse">
      <n-collapse-item title="手动补算历史章节评分" name="manual">
        <n-space vertical :size="8">
          <n-text depth="3" style="font-size: 12px">
            输入章节号，从正文中重算文风相似度并写入记录。
          </n-text>
          <n-space align="center" :size="8">
            <n-input-number
              v-model:value="manualChapterNumber"
              :min="1"
              placeholder="章节号"
              style="width: 100px"
              size="small"
            />
            <n-button
              size="small"
              type="primary"
              :loading="manualScoring"
              @click="manualScore"
            >
              评分
            </n-button>
          </n-space>
          <n-text v-if="manualResult" depth="3" style="font-size: 12px">
            第{{ manualResult.chapter_number }}章 相似度: {{ manualResult.similarity_score !== null ? (manualResult.similarity_score * 100).toFixed(1) + '%' : '(指纹不足)' }}
          </n-text>
        </n-space>
      </n-collapse-item>
    </n-collapse>

  </div>
  </n-spin>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { NTag, NProgress, useMessage } from 'naive-ui'
import { voiceDriftApi, type DriftReportResponse, type ScoreChapterResponse } from '@/api/voiceDrift'
import { chapterApi } from '@/api/chapter'

const props = defineProps<{ slug: string }>()
const message = useMessage()

const loading = ref(false)
const loadError = ref('')
const report = ref<DriftReportResponse | null>(null)

// 手动评分
const manualChapterNumber = ref<number | null>(null)
const manualScoring = ref(false)
const manualResult = ref<ScoreChapterResponse | null>(null)

async function manualScore() {
  const n = manualChapterNumber.value
  if (!n || !props.slug) return
  manualScoring.value = true
  manualResult.value = null
  try {
    const chapter = await chapterApi.getChapter(props.slug, n)
    if (!chapter?.content) {
      message.warning(`第${n}章暂无正文内容，无法评分`)
      return
    }
    const r = await voiceDriftApi.scoreChapter(props.slug, {
      chapter_number: n,
      content: chapter.content,
    })
    manualResult.value = r
    await load()
    message.success(`第${n}章评分完成`)
  } catch {
    message.error('评分失败，请稍后重试')
  } finally {
    manualScoring.value = false
  }
}

async function load() {
  if (!props.slug) return
  loading.value = true
  loadError.value = ''
  try {
    report.value = await voiceDriftApi.getDriftReport(props.slug)
  } catch {
    loadError.value = '加载漂移报告失败，请检查网络或稍后重试'
    report.value = null
  } finally {
    loading.value = false
  }
}

const columns = [
  {
    title: '章节',
    key: 'chapter_number',
    width: 60,
  },
  {
    title: '相似度',
    key: 'similarity_score',
    width: 120,
    render(row: any) {
      const pct = Math.round(row.similarity_score * 100)
      const status = pct >= 75 ? 'success' : pct >= 50 ? 'warning' : 'error'
      return h(NProgress, {
        type: 'line',
        percentage: pct,
        status,
        indicatorPlacement: 'inside',
        height: 18,
      })
    },
  },
  {
    title: '形容词密度',
    key: 'adjective_density',
    render: (row: any) => `${(row.adjective_density * 100).toFixed(2)}%`,
    width: 100,
  },
  {
    title: '均句长',
    key: 'avg_sentence_length',
    render: (row: any) => `${row.avg_sentence_length.toFixed(1)}字`,
    width: 80,
  },
  {
    title: '状态',
    key: 'status',
    width: 70,
    render(row: any) {
      const ok = row.similarity_score >= 0.75
      return h(NTag, { type: ok ? 'success' : 'warning', size: 'small' }, () => ok ? '正常' : '偏离')
    },
  },
  {
    title: '计算时间',
    key: 'computed_at',
    render: (row: any) => row.computed_at?.slice(0, 16) ?? '-',
  },
]

onMounted(load)
</script>

<style scoped>
.drift-panel {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.panel-title {
  font-weight: 600;
  font-size: 14px;
}
.drift-alert {
  margin: 0;
}
.score-table {
  border-radius: 6px;
  overflow: hidden;
}
.manual-score-collapse {
  border-top: 1px solid var(--n-border-color, #e0e0e6);
  padding-top: 4px;
}
</style>
