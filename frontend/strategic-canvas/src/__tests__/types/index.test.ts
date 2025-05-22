import {
  NodeType,
  BaseNodeData,
  CEOLogNodeData,
  DataSnippetNodeData,
  SWOTNodeData,
  RiskOpportunityNodeData,
  ImageNodeData,
  NodeData,
  CanvasNode,
  CanvasEdge,
  CanvasState,
  AIAnalysisResult,
  SaveCanvasResponse,
  LoadCanvasResponse
} from '../../types';

// Type tests using TypeScript's type system
// These tests will fail at compile-time if types are incorrectly defined

describe('TypeScript Type Tests', () => {
  describe('NodeType enum', () => {
    it('should have all expected node types', () => {
      const nodeTypes: NodeType[] = [
        NodeType.BASIC,
        NodeType.CEO_LOG,
        NodeType.DATA_SNIPPET,
        NodeType.SWOT_S,
        NodeType.SWOT_W,
        NodeType.SWOT_O,
        NodeType.SWOT_T,
        NodeType.RISK,
        NodeType.OPPORTUNITY,
        NodeType.IMAGE,
      ];

      expect(nodeTypes).toHaveLength(10);
      expect(NodeType.BASIC).toBe('basic');
      expect(NodeType.CEO_LOG).toBe('ceoLog');
      expect(NodeType.DATA_SNIPPET).toBe('dataSnippet');
    });
  });

  describe('Node Data Types', () => {
    it('should accept valid BaseNodeData', () => {
      const baseData: BaseNodeData = {
        content: 'Test content',
        title: 'Optional title',
      };

      const minimalBaseData: BaseNodeData = {
        content: 'Only content required',
      };

      expect(baseData.content).toBe('Test content');
      expect(minimalBaseData.title).toBeUndefined();
    });

    it('should accept valid CEOLogNodeData', () => {
      const ceoLogData: CEOLogNodeData = {
        content: 'CEO log entry content',
        title: 'Weekly Update',
        logId: 'log-123',
        date: '2024-01-01',
      };

      expect(ceoLogData.logId).toBe('log-123');
      expect(ceoLogData.date).toBe('2024-01-01');
    });

    it('should accept valid DataSnippetNodeData', () => {
      const dataSnippetData: DataSnippetNodeData = {
        content: 'Data visualization content',
        dataSourceId: 'source-456',
        dataType: 'chart',
        dataValue: { revenue: 1000000 },
      };

      expect(dataSnippetData.dataType).toBe('chart');
      expect(dataSnippetData.dataValue).toEqual({ revenue: 1000000 });
    });

    it('should accept valid SWOTNodeData', () => {
      const swotData: SWOTNodeData = {
        content: 'Strong market position',
        category: 'strength',
      };

      expect(swotData.category).toBe('strength');
    });

    it('should accept valid RiskOpportunityNodeData', () => {
      const riskData: RiskOpportunityNodeData = {
        content: 'Market volatility risk',
        impact: 'high',
        likelihood: 'medium',
      };

      expect(riskData.impact).toBe('high');
      expect(riskData.likelihood).toBe('medium');
    });

    it('should accept valid ImageNodeData', () => {
      const imageData: ImageNodeData = {
        content: 'Strategic framework diagram',
        imageUrl: 'https://example.com/diagram.png',
        altText: 'Strategic framework visualization',
      };

      expect(imageData.imageUrl).toBe('https://example.com/diagram.png');
    });

    it('should accept NodeData union type', () => {
      const nodeDataArray: NodeData[] = [
        { content: 'Basic content' } as BaseNodeData,
        { content: 'CEO log', logId: 'log-1', date: '2024-01-01' } as CEOLogNodeData,
        { content: 'Chart data', dataSourceId: 'src-1', dataType: 'chart' } as DataSnippetNodeData,
      ];

      expect(nodeDataArray).toHaveLength(3);
    });
  });

  describe('Canvas Types', () => {
    it('should accept valid CanvasNode', () => {
      const canvasNode: CanvasNode = {
        id: 'node-1',
        type: NodeType.BASIC,
        position: { x: 100, y: 200 },
        data: { content: 'Test node content' },
        draggable: true,
        selectable: true,
        style: { backgroundColor: 'white' },
      };

      expect(canvasNode.id).toBe('node-1');
      expect(canvasNode.type).toBe(NodeType.BASIC);
      expect(canvasNode.position).toEqual({ x: 100, y: 200 });
    });

    it('should accept valid CanvasEdge', () => {
      const canvasEdge: CanvasEdge = {
        id: 'edge-1',
        source: 'node-1',
        target: 'node-2',
        sourceHandle: 'handle-a',
        targetHandle: 'handle-b',
        label: 'Connection label',
        style: { stroke: 'blue' },
        isAISuggested: true,
      };

      expect(canvasEdge.source).toBe('node-1');
      expect(canvasEdge.target).toBe('node-2');
      expect(canvasEdge.isAISuggested).toBe(true);
    });

    it('should accept minimal CanvasEdge', () => {
      const minimalEdge: CanvasEdge = {
        id: 'edge-minimal',
        source: 'node-a',
        target: 'node-b',
      };

      expect(minimalEdge.sourceHandle).toBeUndefined();
      expect(minimalEdge.label).toBeUndefined();
      expect(minimalEdge.isAISuggested).toBeUndefined();
    });

    it('should accept valid CanvasState', () => {
      const canvasState: CanvasState = {
        nodes: [
          {
            id: 'node-1',
            type: NodeType.BASIC,
            position: { x: 0, y: 0 },
            data: { content: 'Test' },
            draggable: true,
            selectable: true,
          },
        ],
        edges: [
          {
            id: 'edge-1',
            source: 'node-1',
            target: 'node-2',
          },
        ],
        selectedElements: {
          nodes: [],
          edges: [],
        },
        viewportTransform: {
          x: 0,
          y: 0,
          zoom: 1,
        },
        canvasId: 'canvas-123',
      };

      expect(canvasState.nodes).toHaveLength(1);
      expect(canvasState.edges).toHaveLength(1);
      expect(canvasState.canvasId).toBe('canvas-123');
    });
  });

  describe('AI and API Types', () => {
    it('should accept valid AIAnalysisResult', () => {
      const aiResult: AIAnalysisResult = {
        themes: ['Strategy', 'Innovation'],
        summary: 'Analysis summary text',
        suggestedConnections: [
          {
            sourceNodeId: 'node-1',
            targetNodeId: 'node-2',
            label: 'Strategic connection',
          },
        ],
      };

      expect(aiResult.themes).toEqual(['Strategy', 'Innovation']);
      expect(aiResult.suggestedConnections).toHaveLength(1);
    });

    it('should accept AIAnalysisResult without suggested connections', () => {
      const aiResultNoConnections: AIAnalysisResult = {
        themes: ['Analysis'],
        summary: 'Simple analysis',
      };

      expect(aiResultNoConnections.suggestedConnections).toBeUndefined();
    });

    it('should accept valid SaveCanvasResponse', () => {
      const saveResponse: SaveCanvasResponse = {
        canvasId: 'saved-canvas-123',
        success: true,
        message: 'Canvas saved successfully',
      };

      expect(saveResponse.success).toBe(true);
      expect(saveResponse.canvasId).toBe('saved-canvas-123');
    });

    it('should accept valid LoadCanvasResponse', () => {
      const loadResponse: LoadCanvasResponse = {
        canvasId: 'loaded-canvas-456',
        nodes: [],
        edges: [],
        success: true,
        message: 'Canvas loaded successfully',
      };

      expect(loadResponse.nodes).toEqual([]);
      expect(loadResponse.edges).toEqual([]);
      expect(loadResponse.success).toBe(true);
    });
  });

  describe('Type Guards and Validation', () => {
    it('should validate node data types at runtime', () => {
      const isCEOLogData = (data: NodeData): data is CEOLogNodeData => {
        return 'logId' in data && 'date' in data;
      };

      const ceoData: NodeData = {
        content: 'CEO content',
        logId: 'log-1',
        date: '2024-01-01',
      } as CEOLogNodeData;

      const basicData: NodeData = {
        content: 'Basic content',
      } as BaseNodeData;

      expect(isCEOLogData(ceoData)).toBe(true);
      expect(isCEOLogData(basicData)).toBe(false);
    });

    it('should validate SWOT categories', () => {
      const validCategories: SWOTNodeData['category'][] = [
        'strength',
        'weakness',
        'opportunity',
        'threat',
      ];

      validCategories.forEach(category => {
        const swotData: SWOTNodeData = {
          content: 'SWOT content',
          category,
        };
        expect(swotData.category).toBe(category);
      });
    });

    it('should validate impact and likelihood levels', () => {
      const validLevels: RiskOpportunityNodeData['impact'][] = ['low', 'medium', 'high'];

      validLevels.forEach(level => {
        const riskData: RiskOpportunityNodeData = {
          content: 'Risk content',
          impact: level,
          likelihood: level,
        };
        expect(riskData.impact).toBe(level);
        expect(riskData.likelihood).toBe(level);
      });
    });

    it('should validate data types for DataSnippetNodeData', () => {
      const validDataTypes: DataSnippetNodeData['dataType'][] = ['chart', 'metric', 'text'];

      validDataTypes.forEach(dataType => {
        const dataSnippet: DataSnippetNodeData = {
          content: 'Data content',
          dataSourceId: 'source-1',
          dataType,
        };
        expect(dataSnippet.dataType).toBe(dataType);
      });
    });
  });

  describe('Type Compatibility', () => {
    it('should be compatible with ReactFlow types', () => {
      // This test ensures our custom types extend ReactFlow types correctly
      const node: CanvasNode = {
        id: 'test-node',
        type: NodeType.BASIC,
        position: { x: 0, y: 0 },
        data: { content: 'Test content' },
        draggable: true,
        selectable: true,
      };

      // Should be usable as a ReactFlow Node
      const reactFlowNode = {
        ...node,
        measured: { width: 100, height: 50 },
      };

      expect(reactFlowNode.id).toBe('test-node');
      expect(reactFlowNode.position).toEqual({ x: 0, y: 0 });
    });

    it('should handle optional properties correctly', () => {
      const minimalNode: CanvasNode = {
        id: 'minimal',
        type: NodeType.BASIC,
        position: { x: 0, y: 0 },
        data: { content: 'Minimal' },
        draggable: true,
        selectable: true,
      };

      const fullNode: CanvasNode = {
        ...minimalNode,
        style: { backgroundColor: 'red' },
      };

      expect(minimalNode.style).toBeUndefined();
      expect(fullNode.style).toEqual({ backgroundColor: 'red' });
    });
  });
});