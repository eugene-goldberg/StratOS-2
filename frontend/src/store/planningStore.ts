import { create } from 'zustand';
import planningService, { 
  StrategicPlan, 
  Initiative, 
  InitiativeCreate, 
  Action, 
  ActionCreate,
  Resource,
  ResourceCreate,
  ResourceUpdate,
  ResourceAllocationCreate,
  ResourceUtilization,
  ResourceConflict
} from '../services/planningService';

interface PlanningState {
  plans: StrategicPlan[];
  initiatives: Initiative[];
  resourceUtilization: ResourceUtilization | null;
  resourceConflicts: ResourceConflict[];
  isLoading: boolean;
  error: string | null;
  loadPlans: () => Promise<void>;
  createInitiative: (planId: string, data: InitiativeCreate) => Promise<Initiative | null>;
  updateInitiative: (id: string, data: Partial<InitiativeCreate>) => Promise<void>;
  deleteInitiative: (id: string) => Promise<void>;
  addAction: (initiativeId: string, data: ActionCreate) => Promise<Action | null>;
  updateAction: (initiativeId: string, actionId: string, data: ActionCreate) => Promise<void>;
  deleteAction: (initiativeId: string, actionId: string) => Promise<void>;
  createResource: (initiativeId: string, data: ResourceCreate) => Promise<Resource | null>;
  updateResource: (initiativeId: string, resourceId: string, data: ResourceUpdate) => Promise<void>;
  deleteResource: (initiativeId: string, resourceId: string) => Promise<void>;
  allocateResource: (data: ResourceAllocationCreate) => Promise<void>;
  releaseResourceAllocation: (allocationId: string) => Promise<void>;
  loadResourceUtilization: (resourceType?: string) => Promise<void>;
  checkResourceConflicts: (initiativeId: string) => Promise<void>;
}

export const usePlanningStore = create<PlanningState>((set, get) => ({
  plans: [],
  initiatives: [],
  resourceUtilization: null,
  resourceConflicts: [],
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
  },

  createResource: async (initiativeId, data) => {
    try {
      set({ isLoading: true });
      const resource = await planningService.createResource(initiativeId, data);
      set(state => ({
        initiatives: state.initiatives.map(i => 
          i.id === initiativeId ? { ...i, resources: [...i.resources, resource] } : i
        ),
        isLoading: false
      }));
      return resource;
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to create resource'
      });
      return null;
    }
  },

  updateResource: async (initiativeId, resourceId, data) => {
    try {
      set({ isLoading: true });
      const updated = await planningService.updateResource(initiativeId, resourceId, data);
      set(state => ({
        initiatives: state.initiatives.map(i =>
          i.id === initiativeId ? { 
            ...i, 
            resources: i.resources.map(r => r.id === resourceId ? updated : r) 
          } : i
        ),
        isLoading: false
      }));
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to update resource'
      });
    }
  },

  deleteResource: async (initiativeId, resourceId) => {
    try {
      set({ isLoading: true });
      await planningService.deleteResource(initiativeId, resourceId);
      set(state => ({
        initiatives: state.initiatives.map(i =>
          i.id === initiativeId ? { 
            ...i, 
            resources: i.resources.filter(r => r.id !== resourceId) 
          } : i
        ),
        isLoading: false
      }));
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to delete resource'
      });
    }
  },

  allocateResource: async (data) => {
    try {
      set({ isLoading: true });
      const allocation = await planningService.allocateResource(data);
      
      // Reload plans to get updated resource allocations
      await get().loadPlans();
      
      // Reload utilization data
      await get().loadResourceUtilization();
      
      set({ isLoading: false });
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to allocate resource'
      });
    }
  },

  releaseResourceAllocation: async (allocationId) => {
    try {
      set({ isLoading: true });
      await planningService.releaseResourceAllocation({ 
        allocation_id: allocationId,
        release_date: new Date().toISOString()
      });
      
      // Reload plans to get updated resource allocations
      await get().loadPlans();
      
      // Reload utilization data
      await get().loadResourceUtilization();
      
      set({ isLoading: false });
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to release resource allocation'
      });
    }
  },

  loadResourceUtilization: async (resourceType) => {
    try {
      const utilization = await planningService.getResourceUtilization(resourceType);
      set({ resourceUtilization: utilization });
    } catch (err) {
      console.error('Failed to load resource utilization:', err);
    }
  },

  checkResourceConflicts: async (initiativeId) => {
    try {
      const conflicts = await planningService.checkResourceConflicts(initiativeId);
      set({ resourceConflicts: conflicts });
    } catch (err) {
      console.error('Failed to check resource conflicts:', err);
      set({ resourceConflicts: [] });
    }
  }
}));

export default usePlanningStore;
