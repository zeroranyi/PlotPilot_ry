import axios from 'axios'
import { API_BASE_URL } from './config'

export interface CoreRules {
  power_system: string
  physics_rules: string
  magic_tech: string
}

export interface Geography {
  terrain: string
  climate: string
  resources: string
  ecology: string
}

export interface Society {
  politics: string
  economy: string
  class_system: string
}

export interface Culture {
  history: string
  religion: string
  taboos: string
}

export interface DailyLife {
  food_clothing: string
  language_slang: string
  entertainment: string
}

export interface Worldbuilding {
  id: string
  novel_id: string
  core_rules: CoreRules
  geography: Geography
  society: Society
  culture: Culture
  daily_life: DailyLife
  created_at: string
  updated_at: string
}

export const worldbuildingApi = {
  getWorldbuilding: async (slug: string): Promise<Worldbuilding> => {
    const response = await axios.get(`${API_BASE_URL}/novels/${slug}/worldbuilding`)
    return response.data
  },

  updateWorldbuilding: async (slug: string, data: Partial<Worldbuilding>): Promise<Worldbuilding> => {
    const response = await axios.put(`${API_BASE_URL}/novels/${slug}/worldbuilding`, data)
    return response.data
  }
}
