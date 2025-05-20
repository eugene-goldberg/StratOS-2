import { create } from 'zustand';
import planningService, { StrategicPlan, Initiative, InitiativeCreate, Action, ActionCreate } from '../services/planningService';

interface PlanningState {
  plans: StrategicPlan[];
  initiatives: Initiative[];
  isLoading: boolean;
  error: string | null;
  loadPlans: () => Promise<void>;
  createInitiative: (planId: string, data: InitiativeCreate) => Promise<Initiative | null>;
  updateInitiative: (id: string, data: Partial<InitiativeCreate>) => Promise<void>;
  deleteInitiative: (id: string) => Promise<void>;
  addAction: (initiativeId: string, data: ActionCreate) => Promise<Action | null>;
  updateAction: (initiativeId: string, actionId: string, data: ActionCreate) => Promise<void>;
  deleteAction: (initiativeId: string, actionId: string) => Promise<void>;
}

export const usePlanningStore = create<PlanningState>((set, get) => ({
  plans: [],
  initiatives: [],
  isLoading: false,
  error: null,

  loadPlans: async () => {
    set({ isLoading: true, error: null });
    try {
      const plans = await planningService.listPlans();
      const initiatives = plans.flatMap(p => p.initiatives || []);
      set({ plans, initiatives, isLoading: false });
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to load plans'
      });
    }
  },

  createInitiative: async (planId, data) => {
    try {
      set({ isLoading: true });
      const init = await planningService.createInitiative(planId, data);
      set(state => ({
        initiatives: [...state.initiatives, init],
        isLoading: false
      }));
      return init;
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to create initiative'
      });
      return null;
    }
  },

  updateInitiative: async (id, data) => {
    try {
      set({ isLoading: true });
      const updated = await planningService.updateInitiative(id, data);
      set(state => ({
        initiatives: state.initiatives.map(i => i.id === updated.id ? updated : i),
        isLoading: false
      }));
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to update initiative'
      });
    }
  },

  deleteInitiative: async (id) => {
    try {
      set({ isLoading: true });
      await planningService.deleteInitiative(id);
      set(state => ({
        initiatives: state.initiatives.filter(i => i.id !== id),
        isLoading: false
      }));
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to delete initiative'
      });
    }
  },

  addAction: async (initiativeId, data) => {
    try {
      set({ isLoading: true });
      const action = await planningService.addAction(initiativeId, data);
      set(state => ({
        initiatives: state.initiatives.map(i => i.id === initiativeId ? { ...i, actions: [...i.actions, action] } : i),
        isLoading: false
      }));
      return action;
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to add action'
      });
      return null;
    }
  },

  updateAction: async (initiativeId, actionId, data) => {
    try {
      set({ isLoading: true });
      const updated = await planningService.updateAction(actionId, data);
      set(state => ({
        initiatives: state.initiatives.map(i =>
          i.id === initiativeId ? { ...i, actions: i.actions.map(a => a.id === actionId ? updated : a) } : i
        ),
        isLoading: false
      }));
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to update action'
      });
    }
  },

  deleteAction: async (initiativeId, actionId) => {
    try {
      set({ isLoading: true });
      await planningService.deleteAction(actionId);
      set(state => ({
        initiatives: state.initiatives.map(i =>
          i.id === initiativeId ? { ...i, actions: i.actions.filter(a => a.id !== actionId) } : i
        ),
        isLoading: false
      }));
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to delete action'
      });
    }
  }
}));

export default usePlanningStore;
