import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export interface SWOTItem {
  id: string;
  category: string;
  content: string;
  source: string;
  source_references: any[];
  impact_score?: number;
  certainty_score?: number;
  created_at: string;
  updated_at: string;
}

export interface SWOTAnalysis {
  id: string;
  title: string;
  description?: string;
  items: SWOTItem[];
  tows_strategies: any[];
  created_at: string;
  updated_at: string;
}

export interface SWOTItemCreate {
  category: string;
  content: string;
  source: string;
  source_references?: any[];
  impact_score?: number;
  certainty_score?: number;
}

export interface SOLinkage {
  id: string;
  user_id: string;
  topic_context?: string;
  subjective_item_id?: string;
  subjective_snippet_text: string;
  objective_item_id?: string;
  objective_snippet_text: string;
  objective_item_title?: string;
  linkage_type: string;
  ai_summary_of_linkage: string;
  ai_prompt_for_ceo: string;
  created_at: string;
}

export interface SOLinkageDiscoveryParams {
  userId: string;
  topicContext?: string;
  subjectiveEntryIds?: string[];
  objectiveDatasetIds?: string[];
  dateRangeStart?: string;
  dateRangeEnd?: string;
  maxLinkagesToFind?: number;
}

export const analysisService = {
  createAIGuidedSwot: async (title: string, description?: string): Promise<SWOTAnalysis> => {
    const response = await axios.post(`${API_BASE_URL}/api/analysis/swot/ai-guided`, null, {
      params: { title, description }
    });
    return response.data;
  },

  getSwotAnalysis: async (analysisId: string): Promise<SWOTAnalysis> => {
    const response = await axios.get(`${API_BASE_URL}/api/analysis/swot/${analysisId}`);
    return response.data;
  },

  addSwotItem: async (analysisId: string, item: SWOTItemCreate): Promise<SWOTItem> => {
    const response = await axios.post(`${API_BASE_URL}/api/analysis/swot/${analysisId}/items`, item);
    return response.data;
  },

  generateTowsStrategies: async (analysisId: string): Promise<any[]> => {
    const response = await axios.post(`${API_BASE_URL}/api/analysis/swot/${analysisId}/generate-tows`);
    return response.data.tows_strategies;
  },

  discoverSOLinkages: async (params: SOLinkageDiscoveryParams): Promise<SOLinkage[]> => {
    const response = await axios.post(`${API_BASE_URL}/api/analysis/so-linkage/discover`, null, {
      params: {
        user_id: params.userId,
        topic_context: params.topicContext,
        subjective_entry_ids: params.subjectiveEntryIds,
        objective_dataset_ids: params.objectiveDatasetIds,
        date_range_start: params.dateRangeStart,
        date_range_end: params.dateRangeEnd,
        max_linkages_to_find: params.maxLinkagesToFind
      }
    });
    return response.data;
  },

  listSOLinkages: async (userId: string): Promise<SOLinkage[]> => {
    const response = await axios.get(`${API_BASE_URL}/api/analysis/so-linkage`, {
      params: { user_id: userId }
    });
    return response.data;
  }
};

export default analysisService;
