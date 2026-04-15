/** 知识三元组在图表中的中文展示（与后端 importance / location_type 枚举对齐） */

export function tripleStringAttrs(t: { attributes?: Record<string, unknown> }): Record<string, string> {
  const a = t.attributes
  if (!a || typeof a !== 'object') return {}
  const out: Record<string, string> = {}
  for (const [k, v] of Object.entries(a)) {
    if (v !== undefined && v !== null) out[k] = String(v)
  }
  return out
}

export function characterImportanceZh(v?: string): string {
  switch (v) {
    case 'primary':
      return '主角'
    case 'secondary':
      return '重要配角'
    case 'minor':
      return '次要人物'
    default:
      return ''
  }
}

export function locationImportanceZh(v?: string): string {
  switch (v) {
    case 'core':
      return '核心'
    case 'important':
      return '重要'
    case 'normal':
      return '一般'
    default:
      return ''
  }
}

export function locationTypeZh(v?: string): string {
  switch (v) {
    case 'city':
      return '城市'
    case 'region':
      return '区域'
    case 'building':
      return '建筑'
    case 'faction':
      return '势力'
    case 'realm':
      return '领域'
    default:
      return v || ''
  }
}
