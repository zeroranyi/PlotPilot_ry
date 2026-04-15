<template>
  <div class="fs-suggestions" :class="{ 'fs-suggestions--embedded': embedded, 'fs-suggestions--compact': compact }">
    <n-empty v-if="!currentChapterNumber" description="请先选择章节" size="small" />

    <template v-else>
      <!-- 自动运行模式：简洁显示 -->
      <template v-if="autoRun">
        <n-spin :show="loading" size="small">
          <n-empty v-if="ran && items.length === 0" description="暂无匹配的伏笔建议" size="small" />
          <n-space v-else-if="items.length" vertical :size="8">
            <n-card
              v-for="row in items.slice(0, 5)"
              :key="row.entry.id"
              size="small"
              :bordered="true"
              class="fs-item-card"
            >
              <n-space align="flex-start" :size="8">
                <n-checkbox
                  :checked="picked.has(row.entry.id)"
                  @update:checked="(v: boolean) => togglePick(row.entry.id, v)"
                />
                <div style="flex: 1; min-width: 0">
                  <n-space align="center" :size="6" wrap>
                    <n-tag size="tiny" round type="warning">分 {{ row.score.toFixed(2) }}</n-tag>
                    <n-tag size="tiny" round>第{{ row.entry.chapter }}章埋</n-tag>
                  </n-space>
                  <p class="clue-text">{{ row.entry.hidden_clue }}</p>
                </div>
              </n-space>
            </n-card>
            <n-text v-if="items.length > 5" depth="3" style="font-size: 11px">
              还有 {{ items.length - 5 }} 条建议...
            </n-text>
          </n-space>
        </n-spin>
      </template>

      <!-- 手动模式：保留原 UI -->
      <template v-else>
        <n-alert
          type="info"
          :show-icon="true"
          class="fs-lead"
          :class="{ 'fs-lead--compact': compact }"
        >
          <span class="fs-lead-text">
            <strong>写</strong>：即时计算，不落库。
            <strong>读</strong>：与「伏笔账本」同源；勾选项便于你抄进节拍提示。
          </span>
        </n-alert>

        <n-space vertical :size="12" style="width: 100%">
          <n-form-item label="本章大纲 / 要点" label-placement="top" :show-feedback="false">
            <n-input
              v-model:value="outlineDraft"
              type="textarea"
              placeholder="可留空：将仅用上方「本章规划」里的结构树大纲参与匹配；若补充要点，匹配更准。"
              :autosize="{ minRows: compact ? 3 : 4, maxRows: 12 }"
            />
            <n-text depth="3" class="fs-hint">
              算法：词重叠启发式；未接向量库时不必写太长。
            </n-text>
          </n-form-item>
          <n-button type="primary" size="small" :loading="loading" @click="runSuggest">
            分析建议回收项
          </n-button>

          <n-text v-if="note" depth="3" style="font-size: 11px">{{ note }}</n-text>

          <n-empty v-if="ran && items.length === 0" description="暂无达到阈值的匹配" />

          <n-space v-if="items.length" vertical :size="8">
            <n-text strong style="font-size: 13px">💡 建议回收</n-text>
            <n-card
              v-for="row in items"
              :key="row.entry.id"
              size="small"
              :bordered="true"
            >
              <n-space align="flex-start" :size="10">
                <n-checkbox
                  :checked="picked.has(row.entry.id)"
                  @update:checked="(v: boolean) => togglePick(row.entry.id, v)"
                />
                <div style="flex: 1; min-width: 0">
                  <n-space align="center" :size="8" wrap>
                    <n-tag size="tiny" round type="warning">分 {{ row.score.toFixed(2) }}</n-tag>
                    <n-tag size="tiny" round>埋设 第{{ row.entry.chapter }}章</n-tag>
                  </n-space>
                  <p class="clue-text">{{ row.entry.hidden_clue }}</p>
                  <n-text depth="3" style="font-size: 11px">{{ row.reason }}</n-text>
                </div>
              </n-space>
            </n-card>
          </n-space>
        </n-space>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { foreshadowApi } from '../../api/foreshadow'
import type { ChapterForeshadowSuggestionItem } from '../../api/foreshadow'

const props = withDefaults(
  defineProps<{
    slug: string
    currentChapterNumber?: number | null
    embedded?: boolean
    compact?: boolean
    prefillOutline?: string
    autoRun?: boolean
  }>(),
  { currentChapterNumber: null, embedded: false, compact: false, prefillOutline: '', autoRun: false }
)

const message = useMessage()
const outlineDraft = ref('')
const loading = ref(false)
const ran = ref(false)
const items = ref<ChapterForeshadowSuggestionItem[]>([])
const note = ref('')
const picked = ref<Set<string>>(new Set())

function togglePick(id: string, on: boolean) {
  const next = new Set(picked.value)
  if (on) {
    next.add(id)
  } else {
    next.delete(id)
  }
  picked.value = next
}

async function runSuggest() {
  const ch = props.currentChapterNumber
  if (!ch) return
  loading.value = true
  ran.value = true
  try {
    const res = await foreshadowApi.chapterSuggestions(props.slug, ch, outlineDraft.value, {
      min_score: 0.06,
      limit: 16,
    })
    items.value = res.items
    note.value = res.note
    picked.value = new Set()
  } catch {
    message.error('建议分析失败')
    items.value = []
  } finally {
    loading.value = false
  }
}

watch(
  () => props.currentChapterNumber,
  (ch, prev) => {
    ran.value = false
    items.value = []
    note.value = ''
    picked.value = new Set()
    if (ch != null && ch !== prev) {
      outlineDraft.value = (props.prefillOutline || '').trim()
      // 自动运行分析
      if (props.autoRun && outlineDraft.value) {
        runSuggest()
      }
    }
  }
)

onMounted(() => {
  if (props.currentChapterNumber && !outlineDraft.value.trim()) {
    outlineDraft.value = (props.prefillOutline || '').trim()
  }
  // 自动运行分析
  if (props.autoRun && props.currentChapterNumber && outlineDraft.value.trim()) {
    runSuggest()
  }
})

watch(
  () => props.prefillOutline,
  (text) => {
    if (!props.currentChapterNumber) return
    if (!outlineDraft.value.trim() && (text || '').trim()) {
      outlineDraft.value = (text || '').trim()
    }
  }
)
</script>

<style scoped>
.fs-suggestions {
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  padding: 12px 16px 20px;
}

.fs-suggestions--embedded {
  padding: 0;
  height: auto;
  max-height: none;
}

.fs-suggestions--compact .fs-lead {
  margin-bottom: 8px;
  padding: 8px 10px;
}

.fs-lead {
  margin-bottom: 12px;
  font-size: 12px;
}

.fs-lead--compact {
  font-size: 11px;
}

.fs-lead-text {
  line-height: 1.5;
}

.fs-hint {
  display: block;
  margin-top: 6px;
  font-size: 11px;
  line-height: 1.45;
}

.clue-text {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.5;
}

.fs-item-card {
  transition: all 0.2s ease;
}

.fs-item-card:hover {
  border-color: var(--n-primary-color);
}
</style>
